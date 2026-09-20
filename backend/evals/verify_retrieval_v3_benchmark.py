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


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def main() -> None:
    if not MANIFEST_PATH.is_file():
        raise RuntimeError(
            f"No existe el manifest: {MANIFEST_PATH}"
        )

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        manifest = json.load(file)

    files = manifest.get("files")

    if not isinstance(files, dict):
        raise RuntimeError(
            "freeze-manifest.json no contiene "
            "una sección 'files' válida."
        )

    changed: list[str] = []

    print()
    print("=" * 100)
    print(
        "VERIFY RETRIEVAL V3 FROZEN BENCHMARK"
    )
    print("=" * 100)

    for filename, expected_hash in files.items():
        path = (
            BENCHMARK_DIR
            / filename
        )

        if not path.is_file():
            print(
                f"[MISSING] {filename}"
            )

            changed.append(
                filename
            )

            continue

        actual_hash = sha256_file(
            path
        )

        if actual_hash != expected_hash:
            print(
                f"[CHANGED] {filename}"
            )

            changed.append(
                filename
            )

            continue

        print(
            f"[OK] {filename}"
        )

    if changed:
        print()

        raise RuntimeError(
            "El benchmark congelado ha cambiado:\n"
            + "\n".join(
                f"  - {filename}"
                for filename in changed
            )
        )

    print()
    print(
        "Benchmark integrity: OK"
    )

    print(
        "Todos los hashes coinciden "
        "con el estado congelado."
    )


if __name__ == "__main__":
    main()