---
layout: default
title: Contributing
permalink: /contributing/
---

# Contributing

## Adding a tool

Edit the appropriate file in `_data/tools/`:

| File | Stage |
|------|-------|
| `data_conversion.yml` | Data Conversion |
| `qc.yml` | Quality Control |
| `preprocessing.yml` | Preprocessing |
| `registration_normalization.yml` | Registration & Normalization |
| `statistical_analysis.yml` | Statistical Analysis |
| `connectivity.yml` | Connectivity |
| `visualization.yml` | Visualization |
| `workflow_managers.yml` | Workflow Managers |
| `data_sources.yml` | Data Sources |

Each entry follows this format:

```yaml
- name: Tool Name
  description: One sentence. What it does, not why it matters.
  url: https://...
  github: owner/repo   # omit if not on GitHub
  language: Python     # primary implementation language
```

## Rules

- One sentence description. No marketing language.
- `url` should point to the most useful page (docs > repo > homepage).
- Include `github: owner/repo` whenever possible — it powers the health checks.
- If a tool spans multiple stages, put it in the stage where most people first encounter it.
- Do not add ratings, stars, or opinions.

## What belongs here

Open-source tools for processing, analyzing, or visualizing MRI data. No commercial software, no general-purpose libraries unless they have a significant MRI-specific use case.
