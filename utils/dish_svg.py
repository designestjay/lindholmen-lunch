"""Line art is ink-only: strokes are currentColor and the root colour is #111. The protein colour comes from the page via CSS on the <use> host."""

from __future__ import annotations

import gzip
import re
from pathlib import Path
from xml.etree import ElementTree

RAW_LIMIT = 7 * 1024
GZIP_LIMIT = int(2.5 * 1024)
MIN_PATHS = 5
MAX_PATHS = 12
MAX_SUBPATHS = 160
VIEWBOX = "0 0 64 64"

STROKE_COLOURS = {"currentcolor"}
FILL_COLOURS = {"none", "transparent"}
MIN_STROKE = 1.25
MAX_STROKE = 3.0
PROTEIN_STROKES = {
    "beef": "#b4360f",
    "pork": "#b03a5b",
    "chicken": "#8a5a00",
    "fish": "#1f5f99",
    "veg": "#2f6b1e",
    "other": "#111",
}
PROTEIN_LABELS = {
    "beef": ("Nöt", "Beef"),
    "pork": ("Fläsk", "Pork"),
    "chicken": ("Kyckling", "Chicken"),
    "fish": ("Fisk", "Fish"),
    "veg": ("Vego", "Veggie"),
}
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
    "mask",
    "clippath",
    "pattern",
    "symbol",
}

_PRECISION = re.compile(r"\d\.\d{2,}")
_MOVE = re.compile(r"[Mm]")
_PROTEIN_PATTERNS = (
    ("beef", re.compile(r"(?<![a-zåäö])(?:nöt|beef)", re.IGNORECASE)),
    ("pork", re.compile(r"(?<![a-zåäö])(?:fläsk|pork)", re.IGNORECASE)),
    ("chicken", re.compile(r"(?<![a-zåäö])(?:kyckling|chicken)", re.IGNORECASE)),
    ("fish", re.compile(r"(?<![a-zåäö])(?:fisk|lax|räk|seafood|shrimp)", re.IGNORECASE)),
    ("veg", re.compile(r"(?<![a-zåäö])(?:vego|vegan|vegetar|veggie)", re.IGNORECASE)),
)
_TAG_PROTEIN = {
    "beef": "beef",
    "pork": "pork",
    "chicken": "chicken",
    "fish": "fish",
    "veg": "veg",
    "vegan": "veg",
}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _stroke_width(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


CATEGORY_PROTEIN = {
    "pho": "beef",
    "kottbullar": "beef",
    "tikka-masala": "chicken",
    "salad-bowl": "veg",
    "sushi-mix": "fish",
}
PATH_STROKES = STROKE_COLOURS | {"none", "transparent"}


def _protein_mentions(text: str, tags: list[str] | None = None) -> set[str]:
    found = set()
    haystack = text or ""
    for key, pattern in _PROTEIN_PATTERNS:
        if pattern.search(haystack):
            found.add(key)
    for tag in tags or []:
        mapped = _TAG_PROTEIN.get((tag or "").lower())
        if mapped:
            found.add(mapped)
    return found


def detect_protein(text: str, tags: list[str] | None = None) -> str | None:
    """Return one protein key, or None when the dish names none or several."""
    found = _protein_mentions(text, tags)
    if len(found) == 1:
        return found.pop()
    return None


def protein_for(text: str, tags: list[str] | None = None, category: str | None = None) -> str | None:
    """Text wins. A category default applies only when the text names no protein."""
    found = _protein_mentions(text, tags)
    if len(found) == 1:
        return next(iter(found))
    if found:
        return None
    return CATEGORY_PROTEIN.get(category or "")


def _luminance(hex_colour: str) -> float:
    raw = hex_colour.lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    channels = []
    for index in (0, 2, 4):
        value = int(raw[index:index + 2], 16) / 255
        if value <= 0.04045:
            channels.append(value / 12.92)
        else:
            channels.append(((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(foreground: str, background: str) -> float:
    light = _luminance(foreground)
    dark = _luminance(background)
    lighter, darker = max(light, dark), min(light, dark)
    return (lighter + 0.05) / (darker + 0.05)


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
    if _norm(root.get("color")) not in {"#111", "#111111"}:
        problems.append("root color must be #111")
    if _norm(root.get("fill")) not in {"none", "transparent"}:
        problems.append("root fill must be none")
    groups = [element for element in root.iter() if _local(element.tag) == "g"]
    if len(groups) != 1 or groups[0].get("id") != "art":
        problems.append("exactly one g#art")
    else:
        group = groups[0]
        if _norm(group.get("stroke")) not in STROKE_COLOURS:
            problems.append("art stroke must be currentColor")
        width = _stroke_width(group.get("stroke-width"))
        if width is None or not MIN_STROKE <= width <= MAX_STROKE:
            problems.append(f"art stroke-width must be between {MIN_STROKE} and {MAX_STROKE}")
        if group.get("stroke-linecap") != "round" or group.get("stroke-linejoin") != "round":
            problems.append("art caps and joins must be round")
        if _norm(group.get("fill")) != "none":
            problems.append("art fill must be none")
    paths = [element for element in root.iter() if _local(element.tag) == "path"]
    if not MIN_PATHS <= len(paths) <= MAX_PATHS:
        problems.append(f"{len(paths)} paths is outside {MIN_PATHS}–{MAX_PATHS}")
    moves = 0
    for element in root.iter():
        name = _local(element.tag)
        if name in FORBIDDEN_TAGS:
            problems.append(f"forbidden <{name}>")
        if element.get("transform") is not None:
            problems.append("transform is not allowed")
        for opacity_name in ("opacity", "stroke-opacity", "fill-opacity"):
            opacity = element.get(opacity_name)
            if opacity is not None and opacity not in {"1", "1.0"}:
                problems.append(f"{opacity_name} must be absent or 1")
        if name == "path":
            data_attr = element.get("d") or ""
            moves += len(_MOVE.findall(data_attr))
            if _PRECISION.search(data_attr):
                problems.append("path data uses more than one decimal place")
            effect = element.get("vector-effect")
            if effect is not None and effect != "non-scaling-stroke":
                problems.append("vector-effect must be non-scaling-stroke when set")
            path_width = _stroke_width(element.get("stroke-width"))
            if element.get("stroke-width") is not None and (
                path_width is None or not MIN_STROKE <= path_width <= MAX_STROKE
            ):
                problems.append(f"stroke-width must be between {MIN_STROKE} and {MAX_STROKE}")
            stroke = _norm(element.get("stroke") or "")
            if stroke and stroke not in PATH_STROKES:
                problems.append(f"stroke {stroke} is outside currentColor")
            fill = _norm(element.get("fill") or "")
            if fill and fill not in FILL_COLOURS:
                problems.append(f"fill {fill} is outside none or transparent")
    if moves > MAX_SUBPATHS:
        problems.append(f"{moves} subpaths exceeds {MAX_SUBPATHS}")
    return problems


def check_dish_file(path: Path) -> list[str]:
    return check_dish_svg(path.read_bytes())
