"""Map a dish name to a generic category. Rules first, then a fuzzy neighbour.

No network and no model. Unknown dishes are queued for a person.
"""

from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

_TAXONOMY = Path("data/dish_taxonomy.json")
_LIBRARY = Path("data/dish_library.json")

_PRICE = re.compile(r"\d+\s*(?:kr|sek)\b", re.IGNORECASE)
_COUNT = re.compile(r"\b\d+\s*bitar\b", re.IGNORECASE)
_LEADING = re.compile(
    r"^(?:veckans|vegetarisk|vegansk|dagens)\b[^:]{0,40}:\s*",
    re.IGNORECASE,
)
_ALLERGEN = re.compile(r"\((?:[A-Za-zÅÄÖåäö]{1,3}(?:\s*,\s*[A-Za-zÅÄÖåäö]{1,3})*)\)")
_SPACE = re.compile(r"\s+")


def load_taxonomy(path: Path | None = None) -> dict:
    source = path or _TAXONOMY
    data = json.loads(source.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_library(path: Path | None = None) -> dict:
    source = path or _LIBRARY
    if not source.exists():
        return {}
    data = json.loads(source.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def normalise(text: str) -> str:
    value = unicodedata.normalize("NFC", text or "").lower()
    value = _PRICE.sub(" ", value)
    value = _COUNT.sub(" ", value)
    value = _ALLERGEN.sub(" ", value)
    value = value.replace("🌶️", " ").replace("🌶", " ")
    value = _LEADING.sub("", value)
    value = _SPACE.sub(" ", value).strip(" -–—,.;")
    return value


def _contains(text: str, keyword: str) -> bool:
    needle = keyword.lower()
    if not needle:
        return False
    pattern = r"(?<![a-zåäö0-9])" + re.escape(needle)
    return re.search(pattern, text) is not None


def _ignored(text: str, taxonomy: dict) -> bool:
    for pattern in taxonomy.get("ignore") or []:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _closed(text: str, taxonomy: dict) -> bool:
    for phrase in taxonomy.get("closed") or []:
        if phrase and phrase.lower() in text:
            return True
    return False


_PASTA_SHAPE = (
    "pasta",
    "penne",
    "spaghetti",
    "linguine",
    "fusilli",
    "rigatoni",
    "tagliatelle",
    "farfalle",
    "makaron",
)
_NOT_A_PASTA = (
    "skinka",
    "bacon",
    "salsiccia",
    "ciabatta",
    "sallad",
    "burgare",
    "smörgås",
    "baguette",
    "wrap",
)


def _pesto_names_pasta(text: str) -> bool:
    """Pesto on a sandwich is not a pasta. A pasta word keeps the pasta category."""
    if any(_contains(text, word) for word in _PASTA_SHAPE):
        return True
    if any(_contains(text, word) for word in _NOT_A_PASTA):
        return False
    return True


def _best_keyword(text: str, categories: dict) -> tuple[str, str, int] | None:
    best = None
    for slug, spec in categories.items():
        if not isinstance(spec, dict):
            continue
        excludes = [item.lower() for item in spec.get("exclude") or []]
        if any(item in text for item in excludes):
            continue
        priority = int(spec.get("priority") or 0)
        for keyword in spec.get("keywords") or []:
            if _contains(text, keyword):
                if slug == "pasta-pesto" and not _pesto_names_pasta(text):
                    continue
                score = priority + len(keyword) * 2
                if best is None or score > best[2]:
                    best = (slug, keyword, score)
    return best


def _fuzzy(text: str, taxonomy: dict) -> tuple[str, float] | None:
    labelled = []
    for alias, slug in (taxonomy.get("aliases") or {}).items():
        labelled.append((normalise(alias), slug))
    for slug, spec in (taxonomy.get("categories") or {}).items():
        for example in (spec or {}).get("examples") or []:
            labelled.append((normalise(example), slug))
    tokens = " ".join(sorted(text.split()))
    best_slug = None
    best_score = 0.0
    for known, slug in labelled:
        if not known:
            continue
        score = SequenceMatcher(None, tokens, " ".join(sorted(known.split()))).ratio()
        if score > best_score:
            best_score = score
            best_slug = slug
    if best_slug and best_score >= 0.85:
        return best_slug, best_score
    return None


def _hint(slug: str, restaurant: str, taxonomy: dict) -> str:
    hints = taxonomy.get("restaurant_hints") or {}
    spec = hints.get(slug) or {}
    name = (restaurant or "").lower()
    for target, names in spec.items():
        if any(name == item.lower() or item.lower() in name for item in names):
            return target
    return slug


def classify(
    name: str,
    description: str = "",
    restaurant: str = "",
    taxonomy: dict | None = None,
) -> dict:
    """Return a category decision. `closed` and `ignored` dishes have no category."""
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    categories = taxonomy.get("categories") or {}
    dish_name = normalise(name)
    dish_desc = normalise(description)
    combined = f"{dish_name} {dish_desc}".strip()
    if not combined:
        return {"dish_category": None, "category_confidence": 0, "category_rule": "empty", "ignored": True}
    if _closed(combined, taxonomy):
        return {"dish_category": None, "category_confidence": 0, "category_rule": "closed", "closed": True}
    if _ignored(dish_name, taxonomy):
        return {"dish_category": None, "category_confidence": 0, "category_rule": "ignore", "ignored": True}

    aliases = {normalise(key): value for key, value in (taxonomy.get("aliases") or {}).items()}
    if dish_name in aliases:
        slug = aliases[dish_name]
        return {
            "dish_category": slug,
            "category_confidence": 0.99,
            "category_rule": "alias",
        }

    named = _best_keyword(dish_name, categories)
    if named:
        slug, keyword, _score = named
        slug = _hint(slug, restaurant, taxonomy)
        return {
            "dish_category": slug,
            "category_confidence": 0.92,
            "category_rule": f"kw:{keyword}",
        }
    described = _best_keyword(dish_desc, categories)
    if described:
        slug, keyword, _score = described
        slug = _hint(slug, restaurant, taxonomy)
        return {
            "dish_category": slug,
            "category_confidence": 0.72,
            "category_rule": f"desc:{keyword}",
        }
    fuzzy = _fuzzy(dish_name or dish_desc, taxonomy)
    if fuzzy:
        slug, score = fuzzy
        return {
            "dish_category": slug,
            "category_confidence": 0.6,
            "category_rule": f"fuzzy:{score:.2f}",
        }
    return {
        "dish_category": None,
        "category_confidence": 0,
        "category_rule": "no_rule",
    }


def update_image_queue(rows: list[dict], generated_on: str, path: Path | None = None) -> int:
    """Merge unknown and low-confidence dishes into data/image-queue.json.

    Same-day reruns do not increase seen_count. Returns how many keys are new.
    """
    target = path or Path("data/image-queue.json")
    current = {"generated_at": generated_on, "items": []}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                current = loaded
        except (json.JSONDecodeError, OSError):
            pass
    by_key = {}
    for item in current.get("items") or []:
        if isinstance(item, dict) and item.get("key"):
            by_key[item["key"]] = item
    new_count = 0
    for row in rows:
        if row.get("ignored") or row.get("closed_dish"):
            continue
        confidence = float(row.get("category_confidence") or 0)
        if row.get("dish_category") and confidence >= 0.8:
            continue
        key = row.get("key") or ""
        if not key:
            continue
        existing = by_key.get(key)
        if existing is None:
            new_count += 1
            by_key[key] = {
                "key": key,
                "name": row.get("name") or key,
                "description": row.get("description") or "",
                "restaurants": [row["restaurant"]] if row.get("restaurant") else [],
                "first_seen": generated_on,
                "last_seen": generated_on,
                "seen_count": 1,
                "counted_on": generated_on,
                "suggestion": row.get("dish_category"),
                "confidence": confidence,
                "reason": "no_rule" if not row.get("dish_category") else "low_confidence",
            }
            continue
        existing["last_seen"] = generated_on
        restaurant = row.get("restaurant")
        if restaurant and restaurant not in existing.get("restaurants", []):
            existing.setdefault("restaurants", []).append(restaurant)
        if existing.get("counted_on") != generated_on:
            existing["seen_count"] = int(existing.get("seen_count") or 1) + 1
            existing["counted_on"] = generated_on
    kept = []
    for item in by_key.values():
        last = item.get("last_seen") or generated_on
        try:
            age = (date_from(generated_on) - date_from(last)).days
        except ValueError:
            age = 0
        if age <= 28:
            kept.append(item)
    kept.sort(key=lambda item: item["key"])
    target.write_text(
        json.dumps({"generated_at": generated_on, "items": kept}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return new_count


def date_from(value: str):
    from datetime import date
    return date.fromisoformat(value[:10])


def coverage_line(decisions: list[dict], queue_new: int) -> str:
    classifiable = [item for item in decisions if not item.get("ignored") and not item.get("closed")]
    total = len(classifiable) or 1
    illustrated = sum(1 for item in classifiable if item.get("shown_image"))
    drafted = sum(1 for item in classifiable if item.get("dish_category"))
    unknown = sum(1 for item in classifiable if not item.get("dish_category"))
    return (
        f"Dish illustrations: {illustrated}/{len(classifiable)} dishes "
        f"({round(100 * illustrated / total)}%) with an approved image · "
        f"{drafted} classified · {unknown} unclassified · queue +{queue_new} new"
    )
