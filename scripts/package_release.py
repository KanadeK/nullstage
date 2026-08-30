"""Build the exact GitHub Release assets for NullStage."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "release-assets"
VERSION = "0.1.0"


def reset_output() -> None:
    resolved = OUTPUT.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name != "release-assets":
        raise RuntimeError(f"refusing to clear unexpected release path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir()


def write_examples_bundle() -> None:
    members = [
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "docs/model.md",
        ROOT / "docs/troubleshooting.md",
        *sorted((ROOT / "docs/demo").iterdir()),
        *sorted((ROOT / "examples").iterdir()),
    ]
    destination = OUTPUT / f"nullstage-{VERSION}-examples.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in members:
            relative = source.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"nullstage-{VERSION}/{relative}", (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def write_checksums() -> None:
    lines = []
    for asset in sorted(OUTPUT.iterdir()):
        if asset.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        lines.append(f"{digest}  {asset.name}")
    (OUTPUT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def main() -> int:
    reset_output()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(OUTPUT),
            ".",
        ],
        cwd=ROOT,
        check=True,
    )
    write_examples_bundle()
    write_checksums()
    expected = {
        f"nullstage-{VERSION}-py3-none-any.whl",
        f"nullstage-{VERSION}.tar.gz",
        f"nullstage-{VERSION}-examples.zip",
        "SHA256SUMS",
    }
    actual = {path.name for path in OUTPUT.iterdir()}
    if actual != expected:
        raise RuntimeError(f"unexpected release assets: {sorted(actual)}")
    print("NULLSTAGE_RELEASE_ASSETS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
