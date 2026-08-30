# Contributing

NullStage keeps one small authority path: scenario JSON → typed model → analysis/optimization → reports. Contributions should simplify or extend that path, not add a parallel parser or hidden fallback.

## Setup

```powershell
uv sync --dev --locked
uv run --no-sync python scripts/check.py
```

## Change discipline

1. Open an issue describing the user-visible problem and evidence.
2. Update `docs/spec.md` before changing the public JSON or exit-code contract.
3. Add a failing behavior test before implementation.
4. Keep the runtime dependency-free unless a proposal demonstrates that the standard library cannot satisfy the release contract.
5. Run the full check script before submitting.

Do not weaken a test, coverage gate, candidate cap, or failure exit to make a change pass. New acoustic models must state what they measure or approximate and must remain separable from the v0.1 direct-field report schema.

Commits use `feat:`, `fix:`, `test:`, `docs:`, or `chore:` with one logical change per commit. By contributing, you agree that your contribution is licensed under MIT.
