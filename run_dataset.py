"""
Main entry point: engine selects pattern → handler generates → validate → load.

The dataset generator is now a registered, governed pattern in
TheRollingPipelines registry. This script asks the engine to pick the right
pattern for the request, then dispatches the pattern's executable handler to
actually produce the rows.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the `datasets/` package importable (handler resolution needs this)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Make the `runtime` package importable
RUNTIME_REPO = Path.home() / "LocalDocuments" / "Projects" / "TheRollingPipelines"
sys.path.insert(0, str(RUNTIME_REPO))

from runtime import SelfEvolvingEngine, load_config  # noqa: E402

from datasets.loader import load_to_duckdb  # noqa: E402
from datasets.validator import validate_basic, validate_distribution  # noqa: E402


DEFAULT_QUERY     = "Generate SME banking dataset"
FALLBACK_PATTERN  = "sme-banking-dataset-generator"


def run(query: str = DEFAULT_QUERY) -> int:
    config = load_config(str(RUNTIME_REPO / "runtime" / "runtime.yaml"))

    # Resolve all relative paths against the runtime repo, not the cwd —
    # otherwise registry/audit/memory files get scattered into bb_datasets.
    if not Path(config.registry_path).is_absolute():
        config.registry_path = str(RUNTIME_REPO / config.registry_path)
    if not Path(config.promotion.audit_log).is_absolute():
        config.promotion.audit_log = str(RUNTIME_REPO / config.promotion.audit_log)
    if not Path(config.memory.episodic_path).is_absolute():
        config.memory.episodic_path = str(RUNTIME_REPO / config.memory.episodic_path)
    if not Path(config.memory.run_store_path).is_absolute():
        config.memory.run_store_path = str(RUNTIME_REPO / config.memory.run_store_path)

    # Engine is used here as a deterministic dispatcher — don't let it mutate
    # the registry by promoting whatever the stub LLM emits.
    config.promotion.enabled = False
    engine = SelfEvolvingEngine(config)

    # 1. Engine pipeline selects the most relevant pattern for the request.
    print(f"Engine: query={query!r}")
    result = engine.run(query, mode="exploration")
    llm_used = result["final_result"].get("patterns_used") or []

    # The Selector already ranked patterns by Jaccard relevance against the
    # query during execute(); re-run it here to get the ranked candidate list
    # for handler dispatch (the LLM's `patterns_used` is just a free-text hint).
    active = engine.registry.filter_by_tier("exploration")
    selector_ranked = [p.id for p in engine.selector.select(query, active)]
    candidate_ids = [*llm_used, *selector_ranked, FALLBACK_PATTERN]

    # 2. Walk candidates, take the first one with an executable handler.
    pattern = None
    fn = None
    for pid in candidate_ids:
        candidate = engine.registry.get_pattern(pid)
        if candidate is None:
            continue
        callable_fn = candidate.resolve_handler()
        if callable_fn is not None:
            pattern, fn = candidate, callable_fn
            break

    if fn is None:
        print(f"No executable pattern found (candidates: {candidate_ids})")
        return 1
    print(f"Selected pattern: {pattern.id}")

    # 3. Execute the handler to actually produce data.
    print(f"Dispatch: {pattern.handler}({pattern.config})")
    data = fn(**pattern.config)

    # 4. Validate.
    print("Validating...")
    errors = validate_basic(data) + validate_distribution(data)
    if errors:
        print("Validation failed:")
        for e in errors:
            print("-", e)
        return 1

    # 5. Load to DuckDB.
    print("Loading into DuckDB...")
    load_to_duckdb(data)

    print("Dataset ready ✅")
    return 0


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_QUERY
    raise SystemExit(run(query))
