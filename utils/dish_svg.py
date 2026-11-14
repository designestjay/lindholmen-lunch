"""Style check for dish illustrations.

Jay picked detailed line art on 14 Nov 2026: about 4–6.5 KB raw, at most
2.5 KB gzip, viewBox 0 0 64 64. Strokes stay #111. A highlight fill under
the lines may be lime #c8ff36 or the one soft secondary, #fff4cc.
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path
from xml.etree import ElementTree

RAW_LIMIT = 7 * 1024
GZIP_LIMIT = int(2.5 * 1024)
MAX_PATHS = 120
VIEWBOX = "0 0 64 64"

STROKE_COLOURS = {"#111", "#111111"}
FILL_COLOURS = {"none", "transparent", "#c8ff36", "#fff4cc"}
FORBIDDEN_TAGS = {
    "image",
    "text",
    "filter",
    "lineargradient",
    "radialgradient",
    "script",
    "style",
    "foreignobject",
    "use",
}

_HEX = re.compile(r"#[0-9a-fA-F]{3,8}")
_STYLE_PAIR = re.compile(r"(fill|stroke)\s*:\s*([^;]+)", re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _norm_colour(value: str) -> str:
    colour = (value or "").strip().lower()
    if colour in {"#111111"}:
        return "#111"
    return colour


def check_dish_svg(data: bytes) -> list[str]:
    """Return style problems. An empty list means the file may be committed."""
    problems = []
    if len(data) > RAW_LIMIT:
        problems.append(f"raw size {len(data)} exceeds {RAW_LIMIT}")
    gzipped = len(gzip.compress(data))
    if gzipped > GZIP_LIMIT:
        problems.append(f"gzip size {gzipped} exceeds {GZIP_LIMIT}")
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        return problems + [f"not svg: {exc}"]
    if root.get("viewBox") != VIEWBOX:
        problems.append(f"viewBox must be {VIEWBOX}")
    paths = 0
    for element in root.iter():
        name = _local(element.tag)
        if name in FORBIDDEN_TAGS:
            problems.append(f"forbidden <{name}>")
        if name == "path":
            paths += 1
        paint = {}
        style = element.get("style") or ""
        for key, value in _STYLE_PAIR.findall(style):
            paint[key.lower()] = value.strip()
        for key in ("fill", "stroke"):
            if element.get(key) is not None:
                paint[key] = element.get(key) or ""
        stroke = _norm_colour(paint.get("stroke", ""))
        if stroke and stroke not in STROKE_COLOURS:
            problems.append(f"stroke {stroke} is outside #111")
        fill = _norm_colour(paint.get("fill", ""))
        if fill and fill not in FILL_COLOURS:
            problems.append(f"fill {fill} is outside the approved palette")
        for colour in _HEX.findall(style):
            normalised = _norm_colour(colour)
            if normalised not in STROKE_COLOURS | FILL_COLOURS:
                problems.append(f"colour {normalised} is outside the approved palette")
    if paths > MAX_PATHS:
        problems.append(f"{paths} paths exceeds {MAX_PATHS}")
    return problems


def check_dish_file(path: Path) -> list[str]:
    return check_dish_svg(path.read_bytes())
