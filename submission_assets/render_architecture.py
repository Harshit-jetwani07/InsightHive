"""Render the exact judge-facing InsightHive architecture diagram as PNG."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1600, 1000
BG = "#070b16"
PANEL = "#10172b"
PANEL_ALT = "#12112a"
PURPLE = "#8c7cff"
TEAL = "#57dec7"
TEXT = "#f3f1ff"
MUTED = "#9aa4be"
LINE = "#41416f"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/{name}",
        f"/usr/local/lib/python3.12/site-packages/PIL/fonts/{name}",
        name,
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def centered(draw: ImageDraw.ImageDraw, box, text: str, text_font, fill=TEXT):
    left, top, right, bottom = box
    bounds = draw.multiline_textbbox((0, 0), text, font=text_font, align="center", spacing=6)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    draw.multiline_text(
        ((left + right - text_width) / 2, (top + bottom - text_height) / 2),
        text,
        font=text_font,
        fill=fill,
        align="center",
        spacing=6,
    )


def box(draw, coords, title, subtitle="", accent=PURPLE):
    draw.rounded_rectangle(coords, radius=22, fill=PANEL, outline=accent, width=3)
    left, top, right, _ = coords
    draw.rounded_rectangle((left, top, right, top + 9), radius=8, fill=accent)
    draw.text((left + 22, top + 22), title, font=font(24, True), fill=TEXT)
    if subtitle:
        draw.multiline_text(
            (left + 22, top + 58),
            subtitle,
            font=font(16),
            fill=MUTED,
            spacing=5,
        )


def arrow(draw, start, end, color=LINE, width=4):
    draw.line((start, end), fill=color, width=width)
    x, y = end
    if abs(end[1] - start[1]) >= abs(end[0] - start[0]):
        direction = 1 if end[1] > start[1] else -1
        points = [(x, y), (x - 8, y - 13 * direction), (x + 8, y - 13 * direction)]
    else:
        direction = 1 if end[0] > start[0] else -1
        points = [(x, y), (x - 13 * direction, y - 8), (x - 13 * direction, y + 8)]
    draw.polygon(points, fill=color)


def main(output: str):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    draw.text((70, 42), "InsightHive", font=font(50, True), fill=TEXT)
    draw.text((335, 51), "Multi-Agent Architecture", font=font(40, True), fill=PURPLE)
    draw.text(
        (72, 108),
        "One objective  >  verified tools  >  grounded recommendations  >  human-governed release",
        font=font(21),
        fill=MUTED,
    )
    draw.text((1320, 58), "Google ADK", font=font(24, True), fill=TEAL)
    draw.text((1318, 90), "Agents for Business", font=font(16), fill=MUTED)
    draw.text((1178, 120), "Jiya Aalwani  |  Harshit Jetwani", font=font(15), fill=MUTED)

    user = (70, 180, 390, 290)
    mission = (500, 180, 1100, 290)
    root = (500, 350, 1100, 465)
    evidence = (1210, 350, 1530, 465)
    box(draw, user, "Business Objective", "CSV / Excel / Northstar demo", TEAL)
    box(draw, mission, "Agent Mission Control", "Question · evidence rubric · decision brief", PURPLE)
    box(draw, root, "Google ADK Root Orchestrator", "Plans · routes · verifies · synthesizes", TEAL)
    box(draw, evidence, "Observability", "Trace · artifacts · latency · evaluation", PURPLE)
    arrow(draw, (390, 235), (500, 235), TEAL)
    arrow(draw, (800, 290), (800, 350), PURPLE)
    arrow(draw, (1100, 408), (1210, 408), PURPLE)

    agent_y1, agent_y2 = 540, 655
    agent_width, gap = 230, 25
    start_x = 70
    agents = [
        ("Ingestion", "Confined parsing"),
        ("Quality", "Readiness + anomalies"),
        ("Analytics", "Stats + forecast"),
        ("Insight", "MCP + vector RAG"),
        ("Report", "Validated contract"),
        ("Governance", "HITL publish gate"),
    ]
    for index, (title, subtitle) in enumerate(agents):
        left = start_x + index * (agent_width + gap)
        coords = (left, agent_y1, left + agent_width, agent_y2)
        box(draw, coords, f"{title} Agent", subtitle, PURPLE if index % 2 == 0 else TEAL)
        arrow(draw, (800, 465), (left + agent_width / 2, agent_y1), LINE, 3)

    layer_y1, layer_y2 = 735, 840
    layers = [
        (70, 360, "Deterministic Tools", "Quality · statistics · forecast"),
        (430, 720, "Live MCP + Vector RAG", "Industry KPI grounding"),
        (790, 1080, "ADK Session + Memory", "Cross-session recall"),
        (1150, 1530, "Security Controls", "Guardrails · secret hygiene"),
    ]
    for left, right, title, subtitle in layers:
        box(draw, (left, layer_y1, right, layer_y2), title, subtitle, TEAL)

    arrow(draw, (800, agent_y2), (800, layer_y1), LINE, 4)

    governance = (250, 890, 690, 970)
    report = (910, 890, 1350, 970)
    draw.rounded_rectangle(governance, radius=18, fill=PANEL_ALT, outline=PURPLE, width=3)
    draw.rounded_rectangle(report, radius=18, fill=PANEL_ALT, outline=TEAL, width=3)
    centered(draw, governance, "Human Review\nPending > Reject/Revise > Approve", font(20, True))
    centered(draw, report, "Executive Report\nDownload enabled only after approval", font(20, True))
    arrow(draw, (690, 930), (910, 930), TEAL, 4)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG", optimize=True)
    print(output_path)


if __name__ == "__main__":
    destination = sys.argv[1] if len(sys.argv) > 1 else "docs/architecture.png"
    main(destination)
