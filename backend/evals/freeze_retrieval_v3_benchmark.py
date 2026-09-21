from __future__ import annotations

import hashlib
import json
from pathlib import Path


BACKEND_ROOT = Path(
    __file__
).resolve().parents[1]

BENCHMARK_DIR = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "v3_independent"
)

MANIFEST_PATH = (
    BENCHMARK_DIR
    / "freeze-manifest.json"
)

FROZEN_FILES = (
    "suite.json",
    "httpx.json",
    "vue-router.json",
    "fastapi.json",
    "README.md",
)


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb",
    ) as file:
        while chunk := file.read(
            1024 * 1024
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def main() -> None:
    missing = [
        filename
        for filename in FROZEN_FILES
        if not (
            BENCHMARK_DIR
            / filename
        ).is_file()
    ]

    if missing:
        raise RuntimeError(
            "Faltan archivos del benchmark:\n"
            + "\n".join(
                f"  - {filename}"
                for filename in missing
            )
        )

    hashes = {
        filename: sha256_file(
            BENCHMARK_DIR
            / filename
        )
        for filename in FROZEN_FILES
    }

    payload = {
        "benchmark": (
            "DevPilot AI Retrieval v3 "
            "Independent Validation"
        ),
        "status": "frozen-before-evaluation",
        "algorithm": "sha256",
        "files": hashes,
    }

    with MANIFEST_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write(
            "\n"
        )

    print()
    print("=" * 100)
    print(
        "RETRIEVAL V3 BENCHMARK FREEZE MANIFEST"
    )
    print("=" * 100)

    for filename, digest in hashes.items():
        print(
            f"[OK] {filename:<20} {digest}"
        )

    print()
    print(
        f"Manifest: {MANIFEST_PATH}"
    )

    print()
    print(
        "El benchmark queda identificado por hashes SHA-256."
    )


if __name__ == "__main__":
    main()