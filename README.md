# mritools

A community-driven directory of open-source MRI software, organized by workflow stage.

**Workflow stages:** Data Conversion → Quality Control → Preprocessing → Registration & Normalization → Statistical Analysis → Connectivity → Visualization → Workflow Managers → Data Sources

Tool health (last commit, stars, archived status) is updated automatically every week via GitHub Actions. Active tools rise; abandoned tools fade.

## Structure

```
_data/
  tools/
    data_conversion.yml
    qc.yml
    preprocessing.yml
    registration_normalization.yml
    statistical_analysis.yml
    connectivity.yml
    visualization.yml
    workflow_managers.yml
    data_sources.yml
  health.yml          # auto-generated, do not edit
scripts/
  update_health.py    # run by the health check workflow
.github/
  workflows/
    health_check.yml
```

## Adding a tool

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Running health checks locally

```bash
pip install pyyaml requests
GITHUB_TOKEN=your_token python scripts/update_health.py
```
