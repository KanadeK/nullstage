"""NullStage command-line interface."""

from __future__ import annotations

import argparse
import math
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from nullstage import __version__
from nullstage.analysis import analyze_scenario
from nullstage.io import ScenarioError, parse_scenario_text
from nullstage.optimize import OptimizationError, optimize_scenario
from nullstage.report import (
    OutputBundle,
    build_analysis_bundle,
    build_optimization_bundle,
)


class ReportWriteError(OSError):
    """The requested artifact directory cannot be created safely."""


def _finite_float(value: str) -> float:
    try:
        converted = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a finite number") from error
    if not math.isfinite(converted):
        raise argparse.ArgumentTypeError("must be a finite number")
    return converted


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nullstage",
        description="Preflight microphone spill geometry before rehearsal.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("analyze", "optimize"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("scenario", type=Path)
        command_parser.add_argument(
            "--output-dir",
            type=Path,
            help="write report.json, stage.svg, and report.html to a new directory",
        )
        command_parser.add_argument(
            "--fail-below-db",
            type=_finite_float,
            help="return exit 1 when any selected placement has a lower margin",
        )
    subparsers.add_parser("version")
    return parser


def _write_bundle(bundle: OutputBundle, output_dir: Path) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_dir.mkdir(mode=0o755)
    except FileExistsError as error:
        raise ReportWriteError(
            f"output directory already exists: {output_dir}; choose a new path to avoid overwriting"
        ) from error
    try:
        (output_dir / "report.json").write_text(bundle.json_text, encoding="utf-8", newline="\n")
        (output_dir / "stage.svg").write_text(bundle.svg_text, encoding="utf-8", newline="\n")
        (output_dir / "report.html").write_text(bundle.html_text, encoding="utf-8", newline="\n")
    except OSError:
        shutil.rmtree(output_dir)
        raise


def _repair_message(error: Exception) -> str:
    if isinstance(error, ScenarioError):
        return "Repair the named field in the scenario JSON, then rerun the same command."
    if isinstance(error, OptimizationError):
        return "Reduce the declared search range or increase its steps, then rerun optimize."
    if isinstance(error, ReportWriteError):
        return "Choose a new output directory; NullStage never replaces an existing path."
    return "Check the input/output path and permissions, then rerun the same command."


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "version":
        print(f"NullStage {__version__}")
        return 0

    try:
        scenario = parse_scenario_text(args.scenario.read_text(encoding="utf-8"))
        if args.command == "analyze":
            bundle = build_analysis_bundle(
                scenario,
                analyze_scenario(scenario),
                threshold_db=args.fail_below_db,
            )
        else:
            bundle = build_optimization_bundle(
                scenario,
                optimize_scenario(scenario),
                threshold_db=args.fail_below_db,
            )
        if args.output_dir is not None:
            _write_bundle(bundle, args.output_dir)
    except (OSError, UnicodeError, ScenarioError, OptimizationError) as error:
        print(f"error: {error}", file=sys.stderr)
        print(f"Repair: {_repair_message(error)}", file=sys.stderr)
        return 2

    print(bundle.terminal_text, end="")
    if args.output_dir is not None:
        print(f"Artifacts: {args.output_dir.resolve()}")
    return 1 if bundle.failing_microphone_ids else 0
