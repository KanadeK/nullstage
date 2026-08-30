# Implementation Plan: NullStage v0.1.0

## Overview

Build the smallest complete offline geometry preflight for microphone spill: schema to measured scenario, score to ranked evidence, bounded optimizer to improved candidate, then reports, package, CI, public release, and verified notification.

## Architecture Decisions

- Keep the runtime dependency-free so a release wheel is easy to trust and install.
- Use a single authoritative scenario model; optimized placements are report results, not a second persisted truth source.
- Model direct free-field geometry only. The limitation is part of the result contract, not an optional disclaimer.
- Optimize microphones independently because sources are fixed and v0.1 has no microphone-to-microphone coupling or collision constraint.
- Generate SVG and HTML directly from the same report object used by JSON so visual and machine evidence cannot diverge.

## Dependency Graph

```text
scenario schema -> scoring model -> analysis report -> optimizer
                                  -> JSON/SVG/HTML renderers -> CLI
all product slices -> examples/docs -> release gate -> CI -> GitHub Release
```

## Task List

### Phase 1: Foundation

- [ ] Task 1: Define domain values, JSON boundary validation, and model math with RED/GREEN tests.
- [ ] Task 2: Produce a deterministic per-microphone analysis and threshold decision.

### Checkpoint: Foundation

- [ ] Focused tests pass and the included scenario produces a meaningful margin table.

### Phase 2: Complete User Flow

- [ ] Task 3: Add bounded deterministic optimization and independent exhaustive cross-check.
- [ ] Task 4: Add JSON, SVG, HTML, and CLI output/exit behavior.

### Checkpoint: Complete User Flow

- [ ] Installed-style CLI analyzes, optimizes, fails invalid input, and writes a coherent evidence bundle.

### Phase 3: Delivery

- [ ] Task 5: Add examples, bilingual README, research/model notes, troubleshooting, security, and contribution docs.
- [ ] Task 6: Add a release-equivalent check script, cross-platform CI, tagged release automation, license, changelog, and package metadata.
- [ ] Task 7: Review all five quality axes, fix required findings, publish, verify remote artifacts, and notify by Gmail.

### Checkpoint: Complete

- [ ] Every success criterion in `docs/spec.md` has current evidence.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Users mistake a geometric estimate for room prediction | High | Prominent model banner and limitations in every format; no safety wording |
| Search grid grows unexpectedly | Medium | Schema caps and preflight candidate-count rejection |
| Visual report disagrees with JSON | Medium | Render every format from one immutable report and test shared identifiers/values |
| Cross-platform float text differs | Medium | Fixed rounding at serialization boundaries and deterministic golden assertions |
| GitHub authentication is stale | Medium | Finish local release gate first, then use official `gh` authentication recovery and verify before writes |

## Open Questions

None blocking under the user's explicit free-rein authorization.

