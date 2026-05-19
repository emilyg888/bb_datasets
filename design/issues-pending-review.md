# Issues Pending Review

## Summary

| ID | Severity | Area | Issue | Recommended action | Status |
|---|---|---|---|---|---|
| ISSUE-001 | Medium | Tests | SIT was not run in this session because local shell/process access was unavailable. | Run `pytest`, `python run_dataset.py "Generate realistic SME banking dataset"`, and `python fraud/orchestrator.py --compare` in a local shell before handoff. | Pending review |
| ISSUE-002 | Medium | Config | Runtime dependency path is hardcoded to `~/LocalDocuments/Projects/TheRollingPipelines` in entry points. | Externalize the runtime path into config or environment-driven discovery. | Pending review |
| ISSUE-003 | Medium | Config | The repo has no committed dependency metadata such as `pyproject.toml` or `requirements.txt`. | Add one supported dependency-management path and document it in README. | Pending review |
| ISSUE-004 | Low | Code | No low-risk redundant-code candidates were archived because redundancy could not be proven with both reference checks and executed tests from this session. | Re-run housekeeping locally with code search and tests, then archive only verified redundant files. | Pending review |

## SIT Results

| Command | Result | Notes |
|---|---|---|
| `pytest` | Not run | Local shell/process access was unavailable in this session. |
| `python run_dataset.py "Generate realistic SME banking dataset"` | Not run | Requires local runtime repo and executable shell access. |
| `python fraud/orchestrator.py --compare` | Not run | Requires local runtime repo, registered datasets, and executable shell access. |

## Archived Code Review

| Original path | Archived path | Reason | Review needed? |
|---|---|---|---|
| None | None | No low-risk archive candidates were proven redundant during this session. | No |

## Detailed Issues

### ISSUE-001 — SIT not executed in this session

- Severity: Medium
- Area: Tests
- Evidence: The session could inspect repository contents through GitHub but could not execute local shell commands.
- Impact: Handoff confidence is lower because integration behaviour was not re-verified after documentation changes.
- Recommended action: Run the documented SIT commands locally and update this file with actual results.
- Status: Pending review

### ISSUE-002 — Hardcoded sibling runtime path

- Severity: Medium
- Area: Config
- Evidence: `run_dataset.py` and `fraud/orchestrator.py` resolve `~/LocalDocuments/Projects/TheRollingPipelines` directly in source.
- Impact: The repo is less portable across machines and harder to run in clean environments or CI.
- Recommended action: Introduce a config value or environment variable for runtime repo resolution.
- Status: Pending review

### ISSUE-003 — Missing dependency manifest

- Severity: Medium
- Area: Config
- Evidence: No `pyproject.toml`, `requirements.txt`, or similar dependency manifest was present on `main`.
- Impact: Setup is implicit and reproducibility is weaker for new developers or review environments.
- Recommended action: Add a single supported dependency-management approach and document installation steps.
- Status: Pending review

### ISSUE-004 — Redundant code audit incomplete

- Severity: Low
- Area: Code
- Evidence: No file was archived because the session could not run local search/test validation needed to satisfy the archive safety rules.
- Impact: Some stale code may still exist, but moving it now would be higher risk than leaving it in place.
- Recommended action: Perform a local follow-up audit with reference search and tests, then archive only proven redundant files into `src_archives/2026-05-19_housekeeping/`.
- Status: Pending review
