"""Run the release-equivalent NullStage acceptance gate."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
GATE_ROOT = ROOT / ".tmp" / "release-gate"
DIST_DIR = GATE_ROOT / "dist"
UV = shutil.which("uv")


def run(
    command: list[str],
    *,
    expected: int = 0,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(command)}", flush=True)
    process_env = os.environ.copy() if env is None else env.copy()
    process_env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        command,
        cwd=cwd,
        env=process_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != expected:
        raise RuntimeError(
            f"expected exit {expected}, got {result.returncode}: {' '.join(command)}"
        )
    return result


def reset_gate_root() -> None:
    resolved = GATE_ROOT.resolve()
    expected_parent = (ROOT / ".tmp").resolve()
    if resolved.parent != expected_parent or resolved.name != "release-gate":
        raise RuntimeError(f"refusing to clear unexpected gate path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def check_markdown_links() -> None:
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    failures: list[str] = []
    for markdown in sorted(ROOT.rglob("*.md")):
        if any(part.startswith(".") for part in markdown.relative_to(ROOT).parts):
            continue
        text = markdown.read_text(encoding="utf-8")
        for raw_target in pattern.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if path_text and not (markdown.parent / path_text).exists():
                failures.append(f"{markdown.relative_to(ROOT)} -> {target}")
    if failures:
        raise RuntimeError("broken local Markdown links:\n" + "\n".join(failures))
    print("Markdown links: PASS")


def module_command(*arguments: str) -> list[str]:
    return [sys.executable, "-m", "nullstage", *arguments]


def verify_examples() -> None:
    first = GATE_ROOT / "live-first"
    second = GATE_ROOT / "live-second"
    run(
        module_command(
            "optimize",
            "examples/live-band.json",
            "--output-dir",
            str(first),
            "--fail-below-db",
            "8",
        )
    )
    document = json.loads((first / "report.json").read_text(encoding="utf-8"))
    summary = document["summary"]
    if summary != {
        "baseline_worst_margin_db": 5.660909,
        "microphone_count": 3,
        "optimized_worst_margin_db": 8.818014,
        "status": "pass",
    }:
        raise RuntimeError(f"live-band proof drifted: {summary}")

    run(
        module_command(
            "optimize",
            "examples/live-band.json",
            "--output-dir",
            str(second),
            "--fail-below-db",
            "8",
        )
    )
    for name in ("report.json", "stage.svg", "report.html"):
        if (first / name).read_bytes() != (second / name).read_bytes():
            raise RuntimeError(f"non-deterministic artifact: {name}")
        if (first / name).read_bytes() != (ROOT / "docs/demo" / name).read_bytes():
            raise RuntimeError(f"committed demo is stale: docs/demo/{name}")

    blocked = run(
        module_command(
            "analyze",
            "examples/crowded-rehearsal.json",
            "--fail-below-db",
            "8",
        ),
        expected=1,
    )
    if "BELOW THRESHOLD" not in blocked.stdout:
        raise RuntimeError("exit 1 did not preserve threshold evidence")

    invalid = run(
        module_command("analyze", "examples/invalid-unknown-target.json"),
        expected=2,
    )
    if "Repair:" not in invalid.stderr or "missing-source" not in invalid.stderr:
        raise RuntimeError("exit 2 did not provide the invalid reference and repair step")
    print("Example outcomes, deterministic artifacts, and committed demo: PASS")


def build_and_inspect() -> Path:
    run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(DIST_DIR),
            ".",
        ]
    )
    wheels = sorted(DIST_DIR.glob("nullstage-0.1.0-*.whl"))
    sdists = sorted(DIST_DIR.glob("nullstage-0.1.0.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            f"unexpected distributions: {sorted(path.name for path in DIST_DIR.iterdir())}"
        )

    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        required = {
            "nullstage/__init__.py",
            "nullstage/__main__.py",
            "nullstage/analysis.py",
            "nullstage/cli.py",
            "nullstage/io.py",
            "nullstage/model.py",
            "nullstage/optimize.py",
            "nullstage/report.py",
            "nullstage/py.typed",
        }
        if not required <= names:
            raise RuntimeError(f"wheel missing files: {sorted(required - names)}")
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
        if "Version: 0.1.0" not in metadata or "Requires-Python: >=3.11" not in metadata:
            raise RuntimeError("wheel metadata does not match the release contract")
        if "Requires-Dist:" in metadata:
            raise RuntimeError("runtime wheel unexpectedly declares a third-party dependency")
        entry_name = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        if "nullstage = nullstage.cli:main" not in archive.read(entry_name).decode("utf-8"):
            raise RuntimeError("wheel console entry point is missing")
        if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
            raise RuntimeError("wheel license file is missing")

    with tarfile.open(sdists[0], "r:gz") as archive:
        names = set(archive.getnames())
        required_suffixes = {
            "README.md",
            "README.zh-CN.md",
            "examples/live-band.json",
            "docs/model.md",
            "scripts/check.py",
            "tests/test_cli.py",
        }
        missing = {
            suffix
            for suffix in required_suffixes
            if not any(name.endswith(suffix) for name in names)
        }
        if missing:
            raise RuntimeError(f"source distribution missing files: {sorted(missing)}")
    print("Wheel and source distribution contents: PASS")
    return wheels[0]


def clean_install_smoke(wheel: Path) -> None:
    if UV is None:
        raise RuntimeError("uv is required for the release gate")
    environment = GATE_ROOT / "installed-env"
    run([UV, "venv", "--python", sys.executable, str(environment)])
    clean_python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    console = environment / ("Scripts/nullstage.exe" if os.name == "nt" else "bin/nullstage")
    run([UV, "pip", "install", "--python", str(clean_python), "--no-index", str(wheel)])
    clean_env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    clean_env["PYTHONNOUSERSITE"] = "1"
    run([str(console), "version"], env=clean_env)
    run(
        [
            str(console),
            "optimize",
            str(ROOT / "examples/live-band.json"),
            "--output-dir",
            str(GATE_ROOT / "installed-live"),
            "--fail-below-db",
            "8",
        ],
        env=clean_env,
    )
    run(
        [
            str(console),
            "analyze",
            str(ROOT / "examples/crowded-rehearsal.json"),
            "--fail-below-db",
            "8",
        ],
        expected=1,
        env=clean_env,
    )
    run(
        [str(console), "analyze", str(ROOT / "examples/invalid-unknown-target.json")],
        expected=2,
        env=clean_env,
    )
    print("Clean wheel install and console exits 0/1/2: PASS")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if UV is None:
        raise RuntimeError("uv is required for the release gate")
    reset_gate_root()
    run([UV, "lock", "--check"])
    run([UV, "run", "--no-sync", "ruff", "format", "--check", "."])
    run([UV, "run", "--no-sync", "ruff", "check", "."])
    run([UV, "run", "--no-sync", "mypy", "src"])
    run(
        [
            UV,
            "run",
            "--no-sync",
            "pytest",
            "-q",
            "--cov=nullstage",
            "--cov-branch",
            "--cov-report=term-missing",
            f"--basetemp={GATE_ROOT / 'pytest'}",
            "-p",
            "no:cacheprovider",
        ]
    )
    check_markdown_links()
    verify_examples()
    wheel = build_and_inspect()
    clean_install_smoke(wheel)
    run([UV, "audit", "--locked"])
    print("NULLSTAGE_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
