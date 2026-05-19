# bb_datasets

## Overview

`bb_datasets` is a Python repository for synthetic SME banking dataset generation and fraud-detector evaluation. It works alongside the sibling `TheRollingPipelines` runtime, which selects generator or detector patterns and provides runtime configuration.

## Architecture Summary

The repo has two main entry points:

- `run_dataset.py` selects a dataset generator pattern through the runtime, validates the generated records, and loads them into DuckDB.
- `fraud/orchestrator.py` evaluates registered fraud detector patterns against labelled datasets using a two-phase exploration/validation loop.

The deeper design reference lives in `design/architecture.md`.

## Repository Structure

- `datasets/`: generators, registry-backed dataset loading, schema helpers, and validation
- `fraud/`: fraud loading, feature engineering, detector orchestration, and evaluation loop
- `tests/`: unit-style tests for generators, loaders, validators, and fraud evaluation
- `design/`: architecture and review notes created during housekeeping

## Setup

This repository currently does not include committed dependency metadata such as `pyproject.toml` or `requirements.txt`.

It also expects a sibling runtime repository at:

```text
~/LocalDocuments/Projects/TheRollingPipelines
```

## Run

Generate and load a dataset through the runtime selector:

```bash
python run_dataset.py "Generate realistic SME banking dataset"
```

Run the fraud evaluation orchestrator:

```bash
python fraud/orchestrator.py "Detect fraud in SME transactions"
```

Compare all registered fraud detector patterns:

```bash
python fraud/orchestrator.py --compare
```

## Test / SIT

Intended commands:

```bash
pytest
python run_dataset.py "Generate realistic SME banking dataset"
python fraud/orchestrator.py --compare
```

These commands were not executed during this housekeeping session because local shell/process access was unavailable.

## Configuration

Key configuration locations:

- runtime config is loaded from the sibling runtime repo at `runtime/runtime.yaml`
- dataset packages are resolved from `external-datasets/registry/datasets.json`

## Documentation

- Architecture: `design/architecture.md`
- Pending review issues: `design/issues-pending-review.md`

## Current Status

- Architecture and handoff documentation were added during project housekeeping.
- SIT remains pending local execution.
- No code was archived in this pass because no candidate could be proven redundant with sufficient confidence from the available session tooling.
