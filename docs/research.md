# Research and differentiation

Research was performed on 2026-08-30 before implementation. It combined the local `D:\我的\GitHub` project inventory, prior project memory, general web search, and multiple GitHub-focused queries. This is evidence of scope separation, not a claim that no related software can exist.

## Rejected directions

- **Bookbinding imposition and creep** were rejected because projects such as [Imp](https://github.com/lukaszlasek/imposition-imp), [imposer-rs](https://github.com/joaommartins/imposer-rs), and older imposition utilities already implement the core workflow.
- **Cross-stitch palette and floss substitution** was rejected because [Cstitch](https://github.com/kleintom/Cstitch), [XStitchLab](https://github.com/tomekhotdog/XStitchLab), and related pattern tools already cover color mapping and thread estimation.
- Local projects already cover furniture routes, screen-print capacity, board-game teaching compilation, comic reading order, pottery kiln loading, stage cue collisions, internal PC wiring, sewing SVG preflight, plotter wet-ink crossings, and many developer/release checks. NullStage does not reuse those product contracts.

## Representative live-audio projects

| Project | What it owns | Why NullStage is not a clone |
|---|---|---|
| [SoundDocs](https://github.com/SoundDocs/sounddocs) | Event documents, patch sheets, stage plots, mic plots, schedules, collaboration, and measurement tooling | NullStage has no account/editor/backend; it computes per-mic direct spill margins and bounded physical candidates from JSON |
| [SchemaTex](https://github.com/SchemaTex/SchemaTex) | A measured DSL for stage, evacuation, electrical, and other professional diagrams | NullStage consumes one small acoustic scenario and performs numerical source/mic analysis rather than diagram compilation |
| [PolarDesigner](https://github.com/AustrianAudioGmbH/PolarDesigner) | A VST/AU/AAX plug-in that changes the multi-band pattern of Austrian Audio OC818 hardware | NullStage does not process audio or control a microphone; it compares physical placement geometry across generic ideal patterns |
| [Acoustix](https://github.com/GaetanLepage/acoustix) | GPU/CPU reverberant simulation, microphone arrays, robotics localization, audio signals, STFT, and room impulse responses | NullStage is a zero-runtime-dependency planning preflight: no waveform, GPU, dataset, array processing, or room prediction |
| [Acoular](https://github.com/acoular/acoular) | Acoustic testing, beamforming, and source mapping from measured multichannel data | NullStage starts from declared stage geometry and produces a candidate layout; it is not a measurement or beamforming library |

Queries included combinations of:

- `microphone stage bleed planner polar pattern placement open source`
- `mic bleed calculator stage plot cardioid GitHub`
- `microphone placement optimization musical instruments stage bleed`
- exact-name searches for `NullStage`, `StageNull`, `MicNull`, and `BleedMap microphone`

The searches found stage-documentation tools, model-specific polar plugins, microphone-array/room simulators, and post-recording de-bleed tools, but no directly matching lightweight workflow that accepts constrained stage geometry and returns ranked target-to-spill placement evidence. An incomplete search is not proof of global uniqueness, so the project claims a differentiated contract, not invention of microphone directivity.

## Why the project may earn attention

- The problem is understandable from one SVG: sources, microphone arrows, baseline ghosts, candidate margins.
- The quick start has no service, account, microphone database, audio upload, or runtime dependency.
- The output is useful even when optimization fails a threshold; failure still produces ranked evidence.
- The model is honest enough to inspect and small enough for contributors to extend without adopting a room simulator.
- JSON plus deterministic CLI makes it usable in rehearsal notes, version control, and CI, while the standalone HTML remains shareable with non-programmers.

Stars and views cannot be guaranteed. The release optimizes for a clear first proof, searchable live-sound vocabulary, and low installation cost rather than promising popularity.
