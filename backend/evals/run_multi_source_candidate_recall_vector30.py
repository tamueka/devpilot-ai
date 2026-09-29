from __future__ import annotations

"""
Experimento controlado de candidate recall.

Única variable modificada respecto al diagnóstico original:

    Vector documents: 30
    Lexical documents: 20
    Path documents: 20

El archivo original:
    evals/run_multi_source_candidate_recall.py

NO se modifica.

Tampoco se modifican los defaults compartidos de:
    evals/multi_source_candidate_retrieval.py
"""

from evals import run_multi_source_candidate_recall as diagnostic


VECTOR_DOCUMENT_K = 30
LEXICAL_DOCUMENT_K = 20
PATH_DOCUMENT_K = 20


# Conservamos la implementación real utilizada
# por el diagnóstico original.
_original_build_collector = (
    diagnostic.build_multi_source_candidate_collector
)


def build_experimental_collector(
    *args,
    **kwargs,
):
    """
    Construye el mismo collector del experimento original,
    modificando únicamente el número de documentos
    procedentes de la búsqueda vectorial.
    """

    kwargs["vector_document_k"] = (
        VECTOR_DOCUMENT_K
    )

    kwargs["lexical_document_k"] = (
        LEXICAL_DOCUMENT_K
    )

    kwargs["path_document_k"] = (
        PATH_DOCUMENT_K
    )

    return _original_build_collector(
        *args,
        **kwargs,
    )


def main() -> None:
    print()
    print("=" * 110)
    print(
        "DEVPILOT AI - "
        "RETRIEVAL V2 VECTOR@30 EXPERIMENT"
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
        "Only Vector document K changes: "
        "20 -> 30."
    )

    print()

    # --------------------------------------------------------
    # Monkey patch SOLO dentro de este proceso experimental.
    #
    # El archivo original importa esta función directamente,
    # por lo que sustituimos su referencia global antes de
    # ejecutar el diagnóstico.
    # --------------------------------------------------------

    diagnostic.build_multi_source_candidate_collector = (
        build_experimental_collector
    )

    # --------------------------------------------------------
    # El summary del script original utiliza estas constantes
    # para imprimir Recall@K.
    #
    # Las modificamos solo dentro del módulo cargado en este
    # proceso. No se modifica ningún archivo del proyecto.
    # --------------------------------------------------------

    diagnostic.DEFAULT_VECTOR_DOCUMENT_K = (
        VECTOR_DOCUMENT_K
    )

    diagnostic.DEFAULT_LEXICAL_DOCUMENT_K = (
        LEXICAL_DOCUMENT_K
    )

    diagnostic.DEFAULT_PATH_DOCUMENT_K = (
        PATH_DOCUMENT_K
    )

    # Ejecutamos exactamente el diagnóstico existente,
    # reutilizando datasets, projects config, métricas,
    # impresión y evaluación original.
    diagnostic.main()


if __name__ == "__main__":
    main()