from __future__ import annotations

"""
DevPilot AI
Retrieval V2 - Best-Rank cutoff experiment with Vector@30

Controlled configuration:

    Vector documents:  30
    Lexical documents: 20
    Path documents:    20

The original diagnostic is reused without modifying:

    evals/run_best_rank_candidate_cutoff.py

The shared production/default configuration is NOT modified.
"""

from evals import (
    multi_source_candidate_retrieval as multi_source,
)
from evals import (
    run_best_rank_candidate_cutoff as diagnostic,
)


VECTOR_DOCUMENT_K = 30
LEXICAL_DOCUMENT_K = 20
PATH_DOCUMENT_K = 20


# ============================================================
# ORIGINAL COLLECTOR
# ============================================================

_original_collector = getattr(
    diagnostic,
    "build_multi_source_candidate_collector",
    None,
)


def build_experimental_collector(
    *args,
    **kwargs,
):
    """
    Ejecuta el collector original modificando únicamente
    el número de documentos de la fuente vectorial.

    Vector:  20 -> 30
    Lexical: 20
    Path:    20
    """

    if _original_collector is None:
        raise RuntimeError(
            "The original diagnostic does not expose "
            "build_multi_source_candidate_collector."
        )

    kwargs["vector_document_k"] = (
        VECTOR_DOCUMENT_K
    )

    kwargs["lexical_document_k"] = (
        LEXICAL_DOCUMENT_K
    )

    kwargs["path_document_k"] = (
        PATH_DOCUMENT_K
    )

    return _original_collector(
        *args,
        **kwargs,
    )


# ============================================================
# PATCH HELPERS
# ============================================================

def patch_if_present(
    module,
    name: str,
    value: int,
) -> bool:
    """
    Modifica una constante únicamente si existe
    en el módulo indicado.
    """

    if not hasattr(
        module,
        name,
    ):
        return False

    setattr(
        module,
        name,
        value,
    )

    return True


def configure_experiment() -> list[str]:
    """
    Configura el proceso actual para:

        Vector = 30
        Lexical = 20
        Path = 20

    No escribe ningún archivo ni modifica los defaults
    persistentes del proyecto.
    """

    patches: list[str] = []

    # --------------------------------------------------------
    # Posibles constantes locales del diagnóstico
    # --------------------------------------------------------

    values = {
        "VECTOR_DOCUMENT_K":
            VECTOR_DOCUMENT_K,

        "LEXICAL_DOCUMENT_K":
            LEXICAL_DOCUMENT_K,

        "PATH_DOCUMENT_K":
            PATH_DOCUMENT_K,

        "DEFAULT_VECTOR_DOCUMENT_K":
            VECTOR_DOCUMENT_K,

        "DEFAULT_LEXICAL_DOCUMENT_K":
            LEXICAL_DOCUMENT_K,

        "DEFAULT_PATH_DOCUMENT_K":
            PATH_DOCUMENT_K,
    }

    for name, value in values.items():
        if patch_if_present(
            diagnostic,
            name,
            value,
        ):
            patches.append(
                f"diagnostic.{name}={value}"
            )

    # --------------------------------------------------------
    # Constantes del módulo compartido
    #
    # Esto solo afecta al proceso Python actual.
    # No modifica el fichero original.
    # --------------------------------------------------------

    shared_values = {
        "DEFAULT_VECTOR_DOCUMENT_K":
            VECTOR_DOCUMENT_K,

        "DEFAULT_LEXICAL_DOCUMENT_K":
            LEXICAL_DOCUMENT_K,

        "DEFAULT_PATH_DOCUMENT_K":
            PATH_DOCUMENT_K,
    }

    for name, value in shared_values.items():
        if patch_if_present(
            multi_source,
            name,
            value,
        ):
            patches.append(
                f"multi_source.{name}={value}"
            )

    # --------------------------------------------------------
    # Si el diagnóstico usa directamente el collector,
    # sustituimos su referencia para evitar el problema de
    # los argumentos por defecto ya ligados a 20 en Python.
    # --------------------------------------------------------

    if _original_collector is not None:
        diagnostic.build_multi_source_candidate_collector = (
            build_experimental_collector
        )

        patches.append(
            "build_multi_source_candidate_collector"
            "(30,20,20)"
        )

    # --------------------------------------------------------
    # Fail-fast:
    # evita ejecutar accidentalmente un experimento 20/20/20.
    # --------------------------------------------------------

    vector_patch_found = any(
        (
            "VECTOR_DOCUMENT_K=30" in patch
            or
            "DEFAULT_VECTOR_DOCUMENT_K=30"
            in patch
            or
            "build_multi_source_candidate_collector"
            in patch
        )
        for patch in patches
    )

    if not vector_patch_found:
        raise RuntimeError(
            "No se ha podido identificar cómo modificar "
            "Vector document K en "
            "run_best_rank_candidate_cutoff.py. "
            "Abortando para no ejecutar un falso Vector@30."
        )

    return patches


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    patches = configure_experiment()

    print()
    print("=" * 110)
    print(
        "DEVPILOT AI - RETRIEVAL V2 "
        "BEST-RANK CUTOFF VECTOR@30"
    )
    print("=" * 110)

    print()
    print("Controlled configuration")
    print("-" * 110)

    print(
        f"Vector documents:               "
        f"{VECTOR_DOCUMENT_K}"
    )

    print(
        f"Lexical documents:              "
        f"{LEXICAL_DOCUMENT_K}"
    )

    print(
        f"Path documents:                 "
        f"{PATH_DOCUMENT_K}"
    )

    print()
    print(
        "Experiment:"
    )

    print(
        "  Vector 20 -> 30"
    )

    print(
        "  Lexical unchanged at 20"
    )

    print(
        "  Path unchanged at 20"
    )

    print()
    print(
        "Runtime patches:"
    )

    for patch in patches:
        print(
            f"  - {patch}"
        )

    print()
    print("=" * 110)
    print()

    # Ejecutamos exactamente el diagnóstico original
    # después de aplicar la configuración experimental.
    diagnostic.main()


if __name__ == "__main__":
    main()