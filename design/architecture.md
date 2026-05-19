# Architecture

## 1. Purpose

`bb_datasets` generates synthetic SME banking datasets and evaluates fraud detectors against registered datasets using the sibling `TheRollingPipelines` runtime.

## 2. Current System Shape

This is a Python project without committed packaging metadata. It has two main operating modes:

- dataset generation and loading through `run_dataset.py`, using the runtime registry to select a generator pattern;
- fraud detection and two-phase evaluation through `fraud/orchestrator.py`, using registered datasets plus runtime-managed detector patterns.

The repository depends on a sibling runtime repo at `~/LocalDocuments/Projects/TheRollingPipelines` and on dataset package metadata under `external-datasets/registry/datasets.json`.

## 3. Component Map

| Component | Path | Responsibility | Key dependencies |
|---|---|---|---|
| Dataset package API | `datasets/__init__.py` | Public exports for generation, registry lookup, loading, and validation | `datasets.loader`, `datasets.registry`, `datasets.validator` |
| Dataset generators | `datasets/` | Generate synthetic SME banking datasets and support loading into DuckDB | `pandas`, `duckdb` |
| Dataset registry | `datasets/registry.py` | Resolve versioned dataset packages from the filesystem registry | `external-datasets/registry/datasets.json` |
| Dataset validation | `datasets/validator.py` | Validate generated data and registry-backed dataset packages | `datasets.loader`, `datasets.schema` |
| Dataset entry point | `run_dataset.py` | Ask the runtime to select a dataset generator, validate outputs, and load them into DuckDB | `runtime`, `datasets.loader`, `datasets.validator` |
| Fraud loaders/features | `fraud/load.py`, `fraud/features.py` | Load detector-ready transaction frames and derive fraud features | `duckdb`, `pandas`, `datasets.loader` |
| Fraud evaluation loop | `fraud/loop.py` | Execute exploration/validation phases and append phase-run logs | `fraud.features`, `fraud.load` |
| Fraud orchestration | `fraud/orchestrator.py` | Select, compare, tune, and record runtime detector patterns | `runtime.selector`, `runtime.registry`, `runtime.learning.updater`, `fraud.loop` |
| Tests | `tests/` | Unit coverage for generators, loaders, validators, and fraud loop behaviour | `pytest`-style test layout |

## 4. Runtime Flow

```text
User query
  → `run_dataset.py` or `fraud/orchestrator.py`
  → load runtime config from sibling `TheRollingPipelines`
  → resolve candidate patterns from runtime registry
  → execute generator or detector handler
  → validate / score outputs
  → write DuckDB tables or fraud phase-run logs
```

## 5. Data Flow

Important data movement paths:

- synthetic generator output is loaded into `exports/duckdb/sandbox.db` via `datasets.loader.load_to_duckdb`;
- registry-backed dataset packages are discovered via `external-datasets/registry/datasets.json` and loaded from filesystem package folders;
- fraud evaluation builds feature frames from registered datasets, then scores detector output against `fraud_flag` labels;
- two-phase fraud evaluation appends TSV results to `fraud/memory/phase_runs.tsv`.

## 6. Configuration

Runtime/configuration inputs currently visible in source:

- sibling runtime path: `~/LocalDocuments/Projects/TheRollingPipelines` hardcoded in `run_dataset.py` and `fraud/orchestrator.py`;
- runtime config file: `runtime/runtime.yaml` from the sibling runtime repo;
- dataset registry path: `external-datasets/registry/datasets.json` from `datasets.registry.DEFAULT_REGISTRY_PATH`.

No environment variables are documented in this repo. Secret values are not stored in the repository documentation created during this pass.

## 7. Testing and SIT

Test strategy visible from the repository:

- unit-style tests live under `tests/` and cover generators, loaders, validators, and fraud loop behaviour;
- the most likely primary test command is `pytest`.

SIT command intended for this repo:

```text
pytest
python run_dataset.py "Generate realistic SME banking dataset"
python fraud/orchestrator.py --compare
```

Actual SIT execution was not possible during this session because local shell/process access was unavailable.

## 8. Deployment / Execution

Local execution appears to be the primary mode:

- run `run_dataset.py` to generate and load dataset tables into DuckDB;
- run `fraud/orchestrator.py` to evaluate runtime-registered fraud detectors.

No separate deployment automation, CI/CD configuration, or production deployment files were confirmed from the repository view used in this housekeeping pass.

## 9. Governance / Operational Notes

- Runtime pattern selection, scoring, and optional EMA updates are delegated to `TheRollingPipelines`.
- Fraud evaluation logs are append-only TSV outputs under `fraud/memory/`.
- The repository resolves runtime memory and audit paths relative to the sibling runtime repo to avoid scattering state files.
- A portability limitation exists because the runtime repo path is hardcoded in source.

## 10. Known Gaps

See `design/issues-pending-review.md`.
