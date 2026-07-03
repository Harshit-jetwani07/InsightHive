"""Run Google ADK agents from the Streamlit frontend."""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Optional

from google.adk.runners import Runner
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.orchestrator import build_root_agent
from services.guardrails import validate_user_question
from services.observability import TraceLogger

APP_NAME = "insight_hive"


class AgentRunnerService:
    _unavailable_keys: set[str] = set()

    def __init__(self) -> None:
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
        self.runner = Runner(
            agent=build_root_agent(),
            app_name=APP_NAME,
            session_service=self.session_service,
            memory_service=self.memory_service,
        )
        self.tracer = TraceLogger()
        self._sessions_created: set[tuple[str, str]] = set()
        self._tool_artifacts: list[dict] = []

    def _ensure_api_key(self, api_key: Optional[str]) -> None:
        key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
        if not key:
            raise ValueError("ADK mode requires GOOGLE_API_KEY; use Sample Intelligence Mode without it.")
        os.environ["GOOGLE_API_KEY"] = key

    @staticmethod
    def _is_retryable_provider_error(exc: Exception) -> bool:
        """Return True only for provider failures where a backup key may help."""
        message = str(exc).lower()
        retryable_markers = (
            "429",
            "quota",
            "resource_exhausted",
            "rate limit",
            "rate_limit",
            "too many requests",
            "503",
            "service unavailable",
        )
        return any(marker in message for marker in retryable_markers)

    def _ensure_session(self, user_id: str, session_id: str) -> None:
        key = (user_id, session_id)
        if key in self._sessions_created:
            return

        async def _create() -> None:
            await self.session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )

        asyncio.run(_create())
        self._sessions_created.add(key)

    def _commit_session_to_memory(self, user_id: str, session_id: str) -> None:
        async def _commit() -> None:
            session = await self.session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            if session is not None:
                await self.memory_service.add_session_to_memory(session)

        asyncio.run(_commit())

    def search_memory_text(self, user_id: str, query: str) -> list[str]:
        """Search the configured ADK memory service without another LLM call."""
        async def _search():
            return await self.memory_service.search_memory(
                app_name=APP_NAME,
                user_id=user_id,
                query=query,
            )

        response = asyncio.run(_search())
        texts: list[str] = []
        for memory in response.memories:
            content = getattr(memory, "content", None)
            for part in getattr(content, "parts", []) or []:
                text = getattr(part, "text", None)
                if text:
                    texts.append(text)
        return texts

    def run_query(
        self,
        question: str,
        *,
        user_id: str,
        session_id: str,
        api_key: Optional[str] = None,
        _backup_index: int = 0,
    ) -> str:
        allowed, reason = validate_user_question(question)
        if not allowed:
            self.tracer.new_trace()
            self.tracer.log("guardrail_block", status="blocked", detail=reason)
            return reason

        requested_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
        if requested_key in self._unavailable_keys:
            # Never expose artifacts from a previous request when the current
            # request is rejected by the quota circuit breaker.
            self._tool_artifacts = []
            ordered_backups = [
                os.getenv("GOOGLE_API_KEY_2", "").strip(),
                os.getenv("GOOGLE_API_KEY_3", "").strip(),
            ]
            healthy_backups = [
                key
                for key in ordered_backups
                if key and key not in self._unavailable_keys
            ]
            if not healthy_backups:
                return (
                    "ADK agent error: all configured Gemini projects are temporarily "
                    "unavailable or quota-exhausted. Quota-resilient tools remain available."
                )
            backup_key = healthy_backups[0]
            next_index = ordered_backups.index(backup_key) + 1
            backup_runner = AgentRunnerService()
            response = backup_runner.run_query(
                question,
                user_id=user_id,
                session_id=f"{session_id}-healthy-backup-{next_index + 1}",
                api_key=backup_key,
                _backup_index=next_index,
            )
            self._tool_artifacts = backup_runner.get_tool_artifacts()
            self.tracer = backup_runner.tracer
            return response

        self._ensure_api_key(api_key)
        self._ensure_session(user_id, session_id)
        trace_id = self.tracer.new_trace()
        self._tool_artifacts = []
        self.tracer.log("user_query", detail=question[:240])
        run_started = time.perf_counter()
        tool_started: dict[str, float] = {}

        content = types.Content(role="user", parts=[types.Part(text=question)])
        final_response = "No response received from the agent."

        try:
            events = self.runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            )
            for event in events:
                if hasattr(event, "content") and event.content and getattr(event.content, "parts", None):
                    for part in event.content.parts:
                        if getattr(part, "function_call", None):
                            fn = part.function_call
                            tool_started[getattr(fn, "name", "unknown_tool")] = time.perf_counter()
                            self.tracer.log(
                                "tool_call",
                                agent=getattr(event, "author", "agent"),
                                tool=getattr(fn, "name", "unknown_tool"),
                                detail=str(getattr(fn, "args", ""))[:240],
                            )
                        if getattr(part, "function_response", None):
                            fn_resp = part.function_response
                            tool_name = getattr(fn_resp, "name", "unknown_tool")
                            raw_response = getattr(fn_resp, "response", "")
                            payload = self._decode_tool_response(raw_response)
                            # ADK models agent delegation as an internal function
                            # response. It is useful in the trace, but it is not
                            # business evidence and must not inflate tool metrics.
                            if tool_name != "transfer_to_agent":
                                self._tool_artifacts.append(
                                    {
                                        "tool": tool_name,
                                        "agent": getattr(event, "author", "agent"),
                                        "payload": payload,
                                    }
                                )
                            started = tool_started.pop(tool_name, time.perf_counter())
                            self.tracer.log(
                                "tool_response",
                                agent=getattr(event, "author", "agent"),
                                tool=tool_name,
                                detail=str(getattr(fn_resp, "response", ""))[:240],
                                latency_ms=round((time.perf_counter() - started) * 1000),
                            )

                if hasattr(event, "is_final_response") and event.is_final_response():
                    if event.content and event.content.parts:
                        text_parts = [
                            part.text for part in event.content.parts if getattr(part, "text", None)
                        ]
                        if text_parts:
                            final_response = "\n".join(text_parts).strip()
                    break
                elif getattr(event, "type", "") == "final_response" and event.content:
                    final_response = event.content.parts[0].text

            self.tracer.log(
                "final_response",
                detail=final_response[:240],
                latency_ms=round((time.perf_counter() - run_started) * 1000),
            )
            self._commit_session_to_memory(user_id, session_id)
            if final_response == "No response received from the agent.":
                current_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
                self._unavailable_keys.add(current_key)
                backup_keys = [
                    os.getenv("GOOGLE_API_KEY_2", "").strip(),
                    os.getenv("GOOGLE_API_KEY_3", "").strip(),
                ]
                remaining_keys = [
                    key
                    for key in backup_keys[_backup_index:]
                    if key and key != current_key
                ]
                if remaining_keys:
                    backup_key = remaining_keys[0]
                    next_index = backup_keys.index(backup_key) + 1
                    backup_runner = AgentRunnerService()
                    response = backup_runner.run_query(
                        question,
                        user_id=user_id,
                        session_id=f"{session_id}-backup-{next_index + 1}",
                        api_key=backup_key,
                        _backup_index=next_index,
                    )
                    self._tool_artifacts = backup_runner.get_tool_artifacts()
                    self.tracer = backup_runner.tracer
                    self.tracer.log(
                        "api_key_failover",
                        status=(
                            "completed"
                            if response != "No response received from the agent."
                            and not response.startswith("ADK agent error:")
                            else "error"
                        ),
                        detail=(
                            "Provider returned no response; "
                            f"backup key {next_index + 1} attempted."
                        ),
                    )
                    return response
            return final_response
        except Exception as exc:
            self.tracer.log("error", status="error", detail=str(exc))
            current_key = (api_key or os.getenv("GOOGLE_API_KEY", "")).strip()
            if self._is_retryable_provider_error(exc):
                self._unavailable_keys.add(current_key)
            backup_keys = [
                os.getenv("GOOGLE_API_KEY_2", "").strip(),
                os.getenv("GOOGLE_API_KEY_3", "").strip(),
            ]
            remaining_keys = [
                key
                for key in backup_keys[_backup_index:]
                if key and key != current_key
            ]
            if (
                remaining_keys
                and self._is_retryable_provider_error(exc)
            ):
                backup_key = remaining_keys[0]
                next_index = backup_keys.index(backup_key) + 1
                # MCP toolsets keep async session state. A provider failure may
                # close that event loop, so retry on a fresh ADK runner instead
                # of reusing a partially-consumed runtime.
                backup_runner = AgentRunnerService()
                response = backup_runner.run_query(
                    question,
                    user_id=user_id,
                    session_id=f"{session_id}-backup-{next_index + 1}",
                    api_key=backup_key,
                    _backup_index=next_index,
                )
                self._tool_artifacts = backup_runner.get_tool_artifacts()
                self.tracer = backup_runner.tracer
                self.tracer.log(
                    "api_key_failover",
                    status=(
                        "completed"
                        if not response.startswith("ADK agent error:")
                        else "error"
                    ),
                    detail=(
                        "Provider quota unavailable; "
                        f"backup key {next_index + 1} attempted."
                    ),
                )
                return response
            return (
                f"ADK agent error: {exc}\n\n"
                "Check that google-adk is installed and your Gemini API key is valid."
            )

    def get_trace_events(self) -> list[dict]:
        return self.tracer.get_events()

    @staticmethod
    def _decode_tool_response(response):
        value = response
        if isinstance(value, dict) and set(value) == {"result"}:
            value = value["result"]
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def get_tool_artifacts(self) -> list[dict]:
        return list(self._tool_artifacts)

    def get_latest_tool_artifact(self, tool_name: str) -> Optional[dict]:
        for artifact in reversed(self._tool_artifacts):
            if artifact["tool"] == tool_name:
                payload = artifact["payload"]
                return payload if isinstance(payload, dict) else {"result": payload}
        return None


_runner: Optional[AgentRunnerService] = None


def get_agent_runner() -> AgentRunnerService:
    global _runner
    if _runner is None:
        _runner = AgentRunnerService()
    return _runner
