# Contributing

## Adding a tool

Edit the appropriate file in `_data/tools/`:

| File | Stage |
|------|-------|
| `data_conversion.yml` | Data conversion |
| `qc.yml` | Quality control |
| `preprocessing.yml` | Preprocessing |
| `analysis.yml` | Analysis |
| `visualization.yml` | Visualization |

Each entry follows this format:

```yaml
- name: Tool Name
  description: One sentence. What it does, not why it matters.
  url: https://...
  github: owner/repo   # omit if not on GitHub
```

## Rules

- One sentence description. No marketing language.
- `url` should point to the most useful page (docs > repo > homepage).
- Include `github: owner/repo` whenever possible — it powers the health checks.
- If a tool spans multiple stages, put it in the stage where most people first encounter it.
- Do not add ratings, stars, or opinions.

## What belongs here

Open-source tools for processing, analyzing, or visualizing MRI data. No commercial software, no general-purpose libraries unless they have a significant MRI-specific use case.
