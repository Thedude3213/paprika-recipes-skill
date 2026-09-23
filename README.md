# Paprika Recipes skill for Claude

A Claude skill that creates `.paprikarecipes` import files for
[Paprika Recipe Manager](https://www.paprikaapp.com/) on iOS, Android, Mac and Windows.
Ask Claude for a recipe "in Paprika" and you get a file you can import directly.

## Why it exists

A `.paprikarecipes` file is a zip of gzip-compressed JSON recipes, which looks easy to
build by hand. It isn't: hand-built files that imported fine on desktop crashed the iOS
app because of missing fields, stale hashes and bad zip entry names. This skill doesn't
hand-roll the format. It builds files with the
[`paprika-recipes`](https://pypi.org/project/paprika-recipes/) library (pinned `>=3,<4`)
through a script that validates the input and verifies the output. Files built this way
import cleanly on iPhone.

## Install

**Claude.ai:** download `paprika-recipes.skill` from
[Releases](https://github.com/Thedude3213/paprika-recipes-skill/releases), then go to
Settings → Capabilities → Skills and upload it.

**Claude Code:** copy the `paprika-recipes/` folder into `~/.claude/skills/`:

```bash
git clone https://github.com/Thedude3213/paprika-recipes-skill.git
cp -r paprika-recipes-skill/paprika-recipes ~/.claude/skills/
```

## Example prompts

- "Put this recipe in Paprika" (with a recipe pasted, photographed, or linked)
- "Bundle my soup recipes into one Paprika file"
- "Add a category to recipes in this .paprikarecipes file"

Import the result on desktop with File → Import. On iPhone or iPad, tap the file and
open it in Paprika.

## How it works

Claude writes the recipes as a JSON list and runs the bundled builder:

```bash
python paprika-recipes/scripts/build_paprika.py recipes.json "My Recipes.paprikarecipes"
```

```json
[
  {
    "name": "Weeknight Lentil Soup",
    "ingredients": ["1 tbsp olive oil", "1 onion, diced", "1 cup red lentils", "4 cups stock"],
    "directions": "1. Soften the onion in the oil.\n2. Add lentils and stock; simmer 20 min.",
    "servings": "4",
    "total_time": "30 min",
    "categories": ["Soups"],
    "rating": 5
  }
]
```

Only `name`, `ingredients` and `directions` are required. The other fields are
`description`, `notes`, `servings`, `prep_time`, `cook_time`, `total_time`,
`difficulty`, `categories`, `source`, `source_url`, `rating` (0–5) and
`nutritional_info`. See [SKILL.md](paprika-recipes/SKILL.md) for details.

The script:

- **Validates the input** and reports every problem at once (missing fields, bad
  ratings, broken JSON, empty input) instead of stopping at the first one.
- **Makes zip entry names safe**: escapes slashes, shortens very long names, and
  de-duplicates repeated recipe names.
- **Writes atomically**, so a failed build never leaves a partial file behind.
- **Verifies every entry** after writing: gzip format, required fields, round-trip text,
  and a fresh hash. If any check fails, no file is written.

Tested with apostrophes, accents, fractions, emoji, duplicate names, and reading and
editing an existing archive.

## Requirements

Python 3 and pip. The skill installs `paprika-recipes` from PyPI when it runs.

## License

[MIT](LICENSE)
