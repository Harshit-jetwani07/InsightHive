import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_all_ten_routing_cases_reference_registered_tools():
    cases = json.loads(
        (ROOT / "evaluation" / "routing_cases.json").read_text(encoding="utf-8")
    )
    registered = set()
    for path in (ROOT / "tools").glob("*.py"):
        registered.update(_function_names(path))
    for path in (ROOT / "mcp_server").glob("*.py"):
        registered.update(f"mcp_{name}" for name in _function_names(path))

    expected = {case["expected_tool"] for case in cases}
    assert len(cases) == 10
    assert len({case["id"] for case in cases}) == 10
    assert expected <= registered
