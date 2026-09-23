---
name: paprika-recipes
description: Create .paprikarecipes import files for the Paprika Recipe Manager app (iOS, Android, Mac, Windows). Use this skill whenever the user wants a recipe "in Paprika", asks to export, save, or import recipes into Paprika, mentions .paprikarecipe / .paprikarecipes (including misspellings like "paprikarecipie"), or wants to bundle several recipes from chat, a photo, a PDF, a web page, or past conversations into one Paprika import file. Also use it to read or inspect an existing .paprikarecipes file.
compatibility: Python 3 with pip; installs the paprika-recipes package (3.x) from PyPI.
---

# Paprika Recipes

Paprika imports a `.paprikarecipes` file: a zip archive in which each entry is one recipe
as gzip-compressed JSON, named after the recipe. Building that by hand looks easy and
isn't. Hand-built files that parse fine on a desktop have crashed the iOS app, because of
missing fields, wrong field types, a stale hash, or a zip entry name that doesn't match the
recipe name (apostrophes are a common culprit). So don't hand-roll the format: use the
`paprika-recipes` library, which writes files the app accepts, through the bundled script.

## When to Use This Skill

- The user wants a recipe "in Paprika", or asks to save, export or import recipes into Paprika
- The user mentions a .paprikarecipe or .paprikarecipes file, even misspelled
- The user wants several recipes bundled into one import file, from chat, a photo, a PDF,
  a web page or past conversations
- The user wants to read, inspect or edit an existing .paprikarecipes file

## What This Skill Does

1. **Builds import files**: Writes `.paprikarecipes` archives with the `paprika-recipes`
   library, so they import on iOS, Android, Mac and Windows.
2. **Validates input**: Reports every problem in the recipe data at once (missing
   fields, bad ratings, broken JSON, empty input).
3. **Makes entry names safe**: Handles slashes, very long names and duplicate recipe names.
4. **Verifies the output**: Reopens the archive and checks every entry's gzip format,
   required fields, round-trip text and hash. Writes nothing if a check fails.
5. **Reads and edits archives**: Opens an existing file so recipes can be inspected,
   changed and rebuilt.

## How to Use

### Basic Usage

```
Put this recipe in Paprika: [pasted recipe, photo or link]
```

### Advanced Usage

```
Bundle all my soup recipes from our past conversations into one Paprika file,
with the category "Soups"
```

```
Add the category "Weeknight" to every recipe in this .paprikarecipes file
```

## Workflow

1. **Gather the recipes.** Pull them from wherever the user pointed: the chat, an image,
   a document, a web page, or past conversations. If the user asks for "all my X recipes",
   search broadly and tell them which ones you found, so they can spot a missing one.
2. **Write a JSON input file** (a list of recipe objects; fields below).
3. **Run the builder:**
   ```bash
   pip install 'paprika-recipes>=3,<4' --break-system-packages -q
   python <this-skill-dir>/scripts/build_paprika.py recipes.json "/mnt/user-data/outputs/My Recipes.paprikarecipes"
   ```
   `<this-skill-dir>` is the folder this SKILL.md lives in. The script validates the
   input, builds every recipe with a fresh hash, writes the archive, then reopens it and
   checks each entry (gzip format, required fields, round-trip text, hash). If anything is
   wrong it prints every problem at once and writes no file, so fix the JSON and rerun;
   never patch the output by hand. Warnings (unknown fields, unusual difficulty) don't
   stop the build but are worth a look.
4. **Deliver the file** and give brief import steps: on desktop, File → Import; on
   iPhone/iPad, tap the file and use Share / Open In → Paprika.

Always produce one `.paprikarecipes` archive, even for a single recipe, since every
Paprika platform imports it.

## Recipe fields

All values are strings unless noted. Only `name`, `ingredients` and `directions`
are required; leave anything unknown empty rather than inventing it (especially
`nutritional_info` and `source_url`).

| Field | Notes |
|---|---|
| `name` | Recipe title. Also becomes the zip entry name; the script makes slashes, very long names and duplicate names safe automatically. |
| `description` | One or two sentences. |
| `ingredients` | A string or a list of lines. One ingredient per line, `\n`-separated, quantity first ("1 cup steel-cut oats"). Paprika scales these, so keep numbers as numbers. Section headers go on their own line. |
| `directions` | One step per line or paragraph. Numbering ("1. …") is optional. |
| `notes` | Tips, variations, storage, substitutions. Blank lines are fine. |
| `servings` | e.g. "4" or "12 bars". |
| `prep_time`, `cook_time`, `total_time` | Free text, e.g. "10 min", "1 hr 15 min". |
| `difficulty` | "Easy", "Medium" or "Hard". |
| `categories` | List of strings (a comma-separated string also works). Paprika creates missing categories on import. |
| `source`, `source_url` | Where the recipe came from, if known. |
| `rating` | Whole number 0–5 (0 = unrated). |
| `nutritional_info` | Only if actually provided. |

## Example

**User**: "Bundle my soup recipes into one Paprika file"

**Output**: Claude finds the recipes, lists them for the user to check, writes them to
`recipes.json`, and runs the builder:
```
OK: wrote 3 recipe(s) to /mnt/user-data/outputs/Soups.paprikarecipes
  - Weeknight Lentil Soup
  - Tomato Basil Soup
  - Chicken Tortilla Soup
```
The user gets `Soups.paprikarecipes` and imports it with File → Import on desktop, or
by tapping it and choosing Paprika on iPhone or iPad.

## Tips

- Put everything the cook needs in the recipe itself. Paprika is used at the stove,
  often on a phone, so storage, make-ahead and appliance tips belong in `notes`.
- Keep ingredient lines clean and scalable: "2 tbsp butter, softened", not "some butter".
- Match the user's existing category names when you know them, so imports land where
  they expect.
- If the user states dietary rules (allergies, no added salt for a baby, etc.), keep
  them in the recipe text so they travel with it.

## Reading an existing file

```python
from paprika_recipes.archive import Archive
with open("file.paprikarecipes", "rb") as f:
    archive = Archive.from_file(f)
for r in archive.recipes:
    print(r.name, r.categories)
```
To change recipes, edit them, call `update_hash()` on each one you changed, and write
a new archive:
```python
with open("edited.paprikarecipes", "wb") as f:
    archive.as_paprikarecipes(f)
```
Or dump the recipes to the JSON input format and rebuild with the script, which also
verifies the result.

## Common Use Cases

- Saving a recipe from a chat, photo, cookbook page or website into Paprika
- Moving a collection of recipes into Paprika in one import
- Bulk-editing categories or other fields in an existing Paprika export
- Checking what's inside a .paprikarecipes file before importing it
