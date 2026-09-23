#!/usr/bin/env python3
"""Build a Paprika .paprikarecipes archive from a JSON list of recipes, then verify it.

Usage: python build_paprika.py recipes.json output.paprikarecipes

The input is a JSON list of recipe objects (a single object is also accepted).
Exits non-zero with a plain-language list of problems if the input is invalid,
and never leaves a partial output file behind.
"""
import gzip
import json
import os
import sys
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from paprika_recipes.archive import Archive, ArchiveRecipe
except ImportError:
    sys.exit("error: paprika-recipes is not installed. Run: "
             "pip install 'paprika-recipes>=3,<4' --break-system-packages")

STRING_FIELDS = [
    "name", "description", "ingredients", "directions", "notes", "servings",
    "prep_time", "cook_time", "total_time", "difficulty", "source", "source_url",
    "nutritional_info",
]
LINE_FIELDS = ("ingredients", "directions", "notes")  # may be given as lists of lines
REQUIRED = ("name", "ingredients", "directions")
KNOWN = set(STRING_FIELDS) | {"categories", "rating"}
MAX_ENTRY_BYTES = 200  # keep entry names well under common 255-byte filename limits


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(x).strip() for x in value if str(x).strip())
    return str(value).strip()


def to_recipe(d, idx: int, problems: list, warnings: list):
    label = f"recipe #{idx + 1}"
    if not isinstance(d, dict):
        problems.append(f"{label}: expected an object, got {type(d).__name__}")
        return None
    label = f"recipe #{idx + 1} ({as_text(d.get('name')) or 'unnamed'})"

    kwargs = {k: as_text(d.get(k)) for k in STRING_FIELDS if d.get(k) is not None}
    for k in REQUIRED:
        if not kwargs.get(k):
            problems.append(f"{label}: missing or empty '{k}'")

    unknown = sorted(set(d) - KNOWN)
    if unknown:
        warnings.append(f"{label}: ignored unknown fields {unknown}")

    cats = d.get("categories", [])
    if isinstance(cats, str):
        cats = [c for c in (x.strip() for x in cats.split(",")) if c]
    elif not isinstance(cats, list):
        problems.append(f"{label}: 'categories' must be a list of strings")
        cats = []
    kwargs["categories"] = list(dict.fromkeys(str(c).strip() for c in cats if str(c).strip()))

    rating = d.get("rating", 0)
    try:
        rating = int(rating or 0)
    except (TypeError, ValueError):
        problems.append(f"{label}: 'rating' must be a whole number 0-5, got {rating!r}")
        rating = 0
    if not 0 <= rating <= 5:
        problems.append(f"{label}: 'rating' must be 0-5, got {rating}")
    kwargs["rating"] = rating

    if kwargs.get("difficulty") and kwargs["difficulty"] not in ("Easy", "Medium", "Hard"):
        warnings.append(f"{label}: unusual difficulty {kwargs['difficulty']!r} "
                        "(Paprika's own values are Easy, Medium, Hard)")

    r = ArchiveRecipe(**kwargs)
    r.update_hash()
    return r


def entry_name(recipe, used: set) -> str:
    """Zip entry name: the recipe name, made safe for a path and unique in the archive."""
    stem = recipe.name.replace("/", "%2F").replace("\\", "%5C").strip() or recipe.uid
    while len(stem.encode("utf-8")) > MAX_ENTRY_BYTES:
        stem = stem[:-1]
    name = f"{stem}.paprikarecipe"
    if name in used:
        name = f"{stem} ({recipe.uid.split('-')[0]}).paprikarecipe"
    used.add(name)
    return name


def check(ok, message: str) -> None:
    """Like assert, but not skipped when Python runs with -O."""
    if not ok:
        raise ValueError(message)


def verify(path: str, recipes: list) -> None:
    with ZipFile(path) as z:
        infos = z.infolist()
        check(len(infos) == len(recipes), f"archive has {len(infos)} entries, expected {len(recipes)}")
        for info, orig in zip(infos, recipes):
            raw = z.read(info)
            check(raw[:2] == b"\x1f\x8b", f"{info.filename}: entry is not gzip-compressed")
            data = json.loads(gzip.decompress(raw).decode("utf-8"))
            for k in ("uid", "name", "ingredients", "directions", "hash", "created", "categories"):
                check(k in data, f"{info.filename}: missing '{k}'")
            check(data["name"] == orig.name, f"{info.filename}: name changed on round trip")
            check(data["ingredients"] == orig.ingredients, f"{orig.name}: ingredients changed")
            check(data["directions"] == orig.directions, f"{orig.name}: directions changed")
            check(data["hash"] == orig.calculate_hash(), f"{orig.name}: stale hash")
    with open(path, "rb") as f:  # and the library's own reader agrees
        check(len(list(Archive.from_file(f).recipes)) == len(recipes), "library reader disagrees on recipe count")


def main():
    for stream in (sys.stdout, sys.stderr):  # e.g. emoji names on a Windows console
        stream.reconfigure(errors="replace")
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    if not out.endswith((".paprikarecipes")):
        sys.exit("error: output file must end in .paprikarecipes")

    try:
        with open(src, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: could not read {src}: {e}")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        sys.exit("error: input must be a non-empty JSON list of recipes")

    problems, warnings = [], []
    recipes = [to_recipe(d, i, problems, warnings) for i, d in enumerate(data)]
    for w in warnings:
        print(f"warning: {w}")
    if problems:
        sys.exit("error: fix these and rerun:\n  " + "\n  ".join(problems))

    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".paprikarecipes", dir=out_dir)
    os.close(fd)
    try:
        used = set()
        with ZipFile(tmp, "w", compression=ZIP_DEFLATED) as z:
            for r in recipes:
                z.writestr(entry_name(r, used), r.as_paprikarecipe())
        verify(tmp, recipes)
        os.replace(tmp, out)
    except Exception as e:
        os.unlink(tmp)
        sys.exit(f"error: build failed verification, no file written: {e}")

    print(f"OK: wrote {len(recipes)} recipe(s) to {out}")
    for r in recipes:
        print(f"  - {r.name}")


if __name__ == "__main__":
    main()
