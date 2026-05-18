# bb_datasets

Synthetic SME banking datasets plus a fraud-evaluation loop that plugs into the `TheRollingPipelines` runtime.

## What is here

- `datasets/`: dataset generators, registry-backed dataset loading, DuckDB loading, schema helpers, and validation.
- `fraud/`: fraud feature engineering, detector variants, orchestration, and two-phase evaluation logging.
- `run_dataset.py`: asks the runtime to select a dataset generator pattern, validates the generated rows, and loads them into DuckDB.
- `tests/`: unit tests for generators, loaders, validators, dataset packages, and fraud evaluation.

## Runtime dependency

This repo expects the runtime repo to exist at:

```text
~/LocalDocuments/Projects/TheRollingPipelines
```

Both `run_dataset.py` and `fraud/orchestrator.py` load `runtime/runtime.yaml` from that sibling repo and resolve registry and memory paths relative to it.

## Dataset packages

Registry-backed datasets are resolved from:

```text
external-datasets/registry/datasets.json
```

Use the public helpers in `datasets.registry` and `datasets.loader` to inspect or load them.

## Common entry points

Generate and load a dataset through the runtime selector:

```bash
python run_dataset.py "Generate realistic SME banking dataset"
```

Run the fraud orchestrator against the registered datasets:

```bash
python fraud/orchestrator.py "Detect fraud in SME transactions"
```

Compare all fraud detector patterns side by side:

```bash
python fraud/orchestrator.py --compare
```

Run the test suite:

```bash
pytest
```

## Notes

- The repository currently does not publish dependency metadata such as `pyproject.toml` or `requirements.txt`.
- Runtime artifacts such as DuckDB exports and fraud phase logs are intentionally excluded from version control.
