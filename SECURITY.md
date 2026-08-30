# Security policy

## Supported versions

The latest GitHub Release is supported. Before a first public release, only the current `main` branch is supported.

## Runtime boundary

NullStage reads local JSON and writes a new local directory. It makes no network request, starts no subprocess, evaluates no expression, and emits script-free HTML. Boundary validation rejects duplicate JSON keys, unexpected fields, non-finite numbers, out-of-stage points, unknown references, invalid physical distances, and excessive candidate searches.

Do not put secrets in a scenario: every label and coordinate is copied into reports. Treat reports as intentionally shareable artifacts.

## Reporting a vulnerability

Use GitHub's private security advisory flow for `KanadeK/nullstage`. Include the affected version, a minimal local scenario, expected versus actual behavior, and impact. Do not open a public issue for a vulnerability before a fix is available.
