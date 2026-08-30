# NullStage v0.1.0 Tasks

## Task 1: Domain and input boundary

**Acceptance criteria:**
- [x] Valid JSON becomes immutable typed values.
- [x] Duplicate/unknown/out-of-bounds/non-finite data fails with a repair message.
- [x] Ideal polar and free-field distance math has focused tests.

**Verification:** `uv run --no-sync pytest tests/test_model.py --basetemp=.tmp/pytest-model -p no:cacheprovider`

**Dependencies:** None

**Files likely touched:** `src/nullstage/model.py`, `src/nullstage/io.py`, `tests/test_model.py`, `tests/test_io.py`

## Task 2: Analysis slice

**Acceptance criteria:**
- [x] Every mic reports target level, combined spill level, margin, and ranked spill contributors.
- [x] Threshold policy is separate from analysis and keeps report evidence.

**Verification:** `uv run --no-sync pytest tests/test_analysis.py --basetemp=.tmp/pytest-analysis -p no:cacheprovider`

**Dependencies:** Task 1

**Files likely touched:** `src/nullstage/analysis.py`, `tests/test_analysis.py`

## Task 3: Optimization slice

**Acceptance criteria:**
- [x] Search stays inside each declared envelope and declared candidate cap.
- [x] Deterministic tie-breaking prefers higher margin, then less movement, less rotation, and stable coordinates.
- [x] A small independent enumeration matches the optimizer.

**Verification:** `uv run --no-sync pytest tests/test_optimize.py --basetemp=.tmp/pytest-optimize -p no:cacheprovider`

**Dependencies:** Tasks 1–2

**Files likely touched:** `src/nullstage/optimize.py`, `tests/test_optimize.py`

## Task 4: Reports and CLI

**Acceptance criteria:**
- [x] Analyze/optimize write deterministic JSON, SVG, and standalone HTML.
- [x] Exit codes 0/1/2 match the public contract.
- [x] Output collision and partial-output behavior are tested.

**Verification:** `uv run --no-sync pytest tests/test_reports.py tests/test_cli.py --basetemp=.tmp/pytest-cli -p no:cacheprovider`

**Dependencies:** Tasks 2–3

**Files likely touched:** `src/nullstage/report.py`, `src/nullstage/cli.py`, `tests/test_reports.py`, `tests/test_cli.py`

## Task 5: Examples and user documentation

**Acceptance criteria:**
- [x] Useful, blocked, and invalid fixtures exercise real paths.
- [x] English/Chinese quick starts, model, research, and repair flow are complete.
- [x] Generated preview comes from the committed example.

**Verification:** run the documented commands verbatim and inspect the generated evidence bundle.

**Dependencies:** Task 4

**Files likely touched:** `examples/*`, `README.md`, `README.zh-CN.md`, `docs/model.md`, `docs/research.md`

## Task 6: Release automation

**Acceptance criteria:**
- [x] One command gates format, lint, types, tests/coverage, examples, build, install, and console smoke.
- [x] CI runs on Ubuntu/Python 3.11 and Windows/Python 3.14.
- [x] Tag workflow builds exact assets and checksums.

**Verification:** `uv run --no-sync python scripts/check.py`

**Dependencies:** Tasks 1–5

**Files likely touched:** `pyproject.toml`, `uv.lock`, `scripts/check.py`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`

## Task 7: Review and public release

**Acceptance criteria:**
- [x] Five-axis review has no unresolved Critical/Required finding.
- [ ] Clean atomic history, author/contributor hygiene, public CI, annotated tag, Release assets/checksums, and fresh downloaded-wheel execution are verified.
- [ ] Gmail self-notification is sent only after remote verification.

**Verification:** public repository, Actions, tag, Release API/assets, fresh install, contributor list, and Sent-mail evidence.

**Dependencies:** Tasks 1–6

**Files likely touched:** release metadata and documentation only if verification finds a real defect.
