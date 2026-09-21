from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(
    __file__
).resolve().parents[1]

OUTPUT_DIR = (
    BACKEND_ROOT
    / "evals"
    / "datasets"
    / "v3_independent"
)

DEFAULT_BENCHMARK_ROOT = (
    Path.home()
    / "Desktop"
    / "TFM_FOUNDERZ"
    / "benchmark-v3-sources"
)

BENCHMARK_ROOT = Path(
    os.getenv(
        "RETRIEVAL_V3_BENCHMARK_ROOT",
        str(DEFAULT_BENCHMARK_ROOT),
    )
).resolve()


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    category: str
    question: str
    expected_file: str


@dataclass(frozen=True)
class RepositorySpec:
    key: str
    source: str
    tag: str
    local_directory: str
    dataset_filename: str
    dataset_name: str
    cases: tuple[EvaluationCase, ...]


HTTPX_CASES = (
    EvaluationCase(
        case_id="httpx-api-001",
        category="api",
        question=(
            "¿Dónde se implementan las funciones HTTP de alto nivel "
            "como get, post, put y request que permiten enviar una "
            "petición sin crear manualmente un cliente?"
        ),
        expected_file="httpx/_api.py",
    ),
    EvaluationCase(
        case_id="httpx-client-001",
        category="client",
        question=(
            "¿Qué archivo implementa los clientes síncrono y asíncrono "
            "que gestionan el envío de peticiones, redirecciones y "
            "configuración de transporte?"
        ),
        expected_file="httpx/_client.py",
    ),
    EvaluationCase(
        case_id="httpx-auth-001",
        category="authentication",
        question=(
            "¿Dónde se implementan los flujos de autenticación Basic, "
            "Digest, NetRC y la clase base de autenticación de HTTPX?"
        ),
        expected_file="httpx/_auth.py",
    ),
    EvaluationCase(
        case_id="httpx-config-001",
        category="configuration",
        question=(
            "¿Qué módulo define la configuración de timeouts, límites "
            "de conexiones, proxies y creación del contexto SSL?"
        ),
        expected_file="httpx/_config.py",
    ),
    EvaluationCase(
        case_id="httpx-content-001",
        category="request-content",
        question=(
            "¿Dónde se transforma el contenido de una petición en "
            "streams y se codifican cuerpos JSON, formularios y "
            "contenido multipart?"
        ),
        expected_file="httpx/_content.py",
    ),
    EvaluationCase(
        case_id="httpx-decoders-001",
        category="decoding",
        question=(
            "¿Qué archivo implementa la decodificación del contenido "
            "HTTP comprimido con gzip, deflate, Brotli o Zstandard?"
        ),
        expected_file="httpx/_decoders.py",
    ),
    EvaluationCase(
        case_id="httpx-exceptions-001",
        category="errors",
        question=(
            "¿Dónde está definida la jerarquía de excepciones de HTTPX "
            "para timeouts, errores de red, protocolo y estado HTTP?"
        ),
        expected_file="httpx/_exceptions.py",
    ),
    EvaluationCase(
        case_id="httpx-models-001",
        category="models",
        question=(
            "¿Qué módulo implementa los principales modelos HTTP como "
            "Request, Response, Headers y Cookies?"
        ),
        expected_file="httpx/_models.py",
    ),
    EvaluationCase(
        case_id="httpx-urls-001",
        category="url",
        question=(
            "¿Dónde se implementan el análisis, normalización y "
            "manipulación de URLs utilizadas por HTTPX?"
        ),
        expected_file="httpx/_urls.py",
    ),
    EvaluationCase(
        case_id="httpx-transport-001",
        category="transport",
        question=(
            "¿Qué archivo implementa el transporte HTTP predeterminado "
            "y adapta los errores de la capa de transporte a errores "
            "propios de HTTPX?"
        ),
        expected_file="httpx/_transports/default.py",
    ),
)


VUE_ROUTER_CASES = (
    EvaluationCase(
        case_id="vue-router-core-001",
        category="router",
        question=(
            "¿Dónde se crea la instancia principal del router y se "
            "coordina el proceso completo de navegación entre rutas?"
        ),
        expected_file="packages/router/src/router.ts",
    ),
    EvaluationCase(
        case_id="vue-router-link-001",
        category="component",
        question=(
            "¿Qué archivo implementa el componente de enlace del router, "
            "incluyendo el cálculo de rutas activas y la navegación "
            "cuando se hace clic?"
        ),
        expected_file="packages/router/src/RouterLink.ts",
    ),
    EvaluationCase(
        case_id="vue-router-view-001",
        category="component",
        question=(
            "¿Dónde se implementa el componente que renderiza el "
            "componente asociado a la ruta actual según la profundidad "
            "de rutas anidadas?"
        ),
        expected_file="packages/router/src/RouterView.ts",
    ),
    EvaluationCase(
        case_id="vue-router-guards-001",
        category="navigation",
        question=(
            "¿Qué módulo extrae, transforma y ejecuta los guards de "
            "navegación definidos en componentes?"
        ),
        expected_file="packages/router/src/navigationGuards.ts",
    ),
    EvaluationCase(
        case_id="vue-router-html5-history-001",
        category="history",
        question=(
            "¿Dónde se implementa el historial web basado en la API "
            "History del navegador para navegación con URLs normales?"
        ),
        expected_file="packages/router/src/history/html5.ts",
    ),
    EvaluationCase(
        case_id="vue-router-memory-history-001",
        category="history",
        question=(
            "¿Qué archivo implementa un historial de navegación "
            "completamente en memoria que no depende del navegador?"
        ),
        expected_file="packages/router/src/history/memory.ts",
    ),
    EvaluationCase(
        case_id="vue-router-matcher-001",
        category="matcher",
        question=(
            "¿Dónde se implementa el matcher que añade, elimina y "
            "resuelve registros de rutas a partir de una ubicación?"
        ),
        expected_file="packages/router/src/matcher/index.ts",
    ),
    EvaluationCase(
        case_id="vue-router-query-001",
        category="query",
        question=(
            "¿Qué archivo convierte query strings en objetos de "
            "parámetros y vuelve a serializarlos a una URL?"
        ),
        expected_file="packages/router/src/query.ts",
    ),
    EvaluationCase(
        case_id="vue-router-encoding-001",
        category="url",
        question=(
            "¿Dónde se implementan las reglas de codificación y "
            "decodificación utilizadas para parámetros, query strings "
            "y hashes de las rutas?"
        ),
        expected_file="packages/router/src/encoding.ts",
    ),
    EvaluationCase(
        case_id="vue-router-scroll-001",
        category="scroll",
        question=(
            "¿Qué módulo guarda, calcula y restaura la posición de "
            "scroll durante una navegación del router?"
        ),
        expected_file="packages/router/src/scrollBehavior.ts",
    ),
)


FASTAPI_CASES = (
    EvaluationCase(
        case_id="fastapi-application-001",
        category="application",
        question=(
            "¿Dónde está implementada la clase principal FastAPI que "
            "configura la aplicación, OpenAPI, documentación y registro "
            "de rutas?"
        ),
        expected_file="fastapi/applications.py",
    ),
    EvaluationCase(
        case_id="fastapi-routing-001",
        category="routing",
        question=(
            "¿Qué archivo implementa APIRoute y la construcción del "
            "handler que procesa una petición y serializa la respuesta?"
        ),
        expected_file="fastapi/routing.py",
    ),
    EvaluationCase(
        case_id="fastapi-dependencies-001",
        category="dependencies",
        question=(
            "¿Dónde se analiza y resuelve el árbol de dependencias de "
            "un endpoint, incluyendo parámetros y caché de dependencias?"
        ),
        expected_file="fastapi/dependencies/utils.py",
    ),
    EvaluationCase(
        case_id="fastapi-oauth2-001",
        category="security",
        question=(
            "¿Qué módulo implementa OAuth2PasswordBearer, formularios "
            "del password flow y la extracción del token Bearer?"
        ),
        expected_file="fastapi/security/oauth2.py",
    ),
    EvaluationCase(
        case_id="fastapi-openapi-001",
        category="openapi",
        question=(
            "¿Dónde se construyen las operaciones, parámetros, "
            "esquemas de seguridad y componentes del documento OpenAPI?"
        ),
        expected_file="fastapi/openapi/utils.py",
    ),
    EvaluationCase(
        case_id="fastapi-exception-handlers-001",
        category="errors",
        question=(
            "¿Qué archivo contiene los handlers que convierten "
            "HTTPException y errores de validación en respuestas HTTP?"
        ),
        expected_file="fastapi/exception_handlers.py",
    ),
    EvaluationCase(
        case_id="fastapi-encoders-001",
        category="serialization",
        question=(
            "¿Dónde se implementa la conversión de modelos, dataclasses, "
            "fechas, enums y otros objetos Python a estructuras "
            "compatibles con JSON?"
        ),
        expected_file="fastapi/encoders.py",
    ),
    EvaluationCase(
        case_id="fastapi-params-001",
        category="parameters",
        question=(
            "¿Qué módulo define las clases que representan parámetros "
            "Path, Query, Header, Cookie, Body, Form y File?"
        ),
        expected_file="fastapi/params.py",
    ),
    EvaluationCase(
        case_id="fastapi-background-001",
        category="background-tasks",
        question=(
            "¿Dónde se implementa la clase utilizada para registrar "
            "funciones que se ejecutarán después de enviar la respuesta "
            "al cliente?"
        ),
        expected_file="fastapi/background.py",
    ),
    EvaluationCase(
        case_id="fastapi-exceptions-001",
        category="errors",
        question=(
            "¿Qué archivo define las excepciones propias de FastAPI, "
            "incluyendo errores HTTP y errores de validación de "
            "peticiones?"
        ),
        expected_file="fastapi/exceptions.py",
    ),
)


REPOSITORIES = (
    RepositorySpec(
        key="httpx",
        source="encode/httpx",
        tag="0.28.1",
        local_directory="httpx",
        dataset_filename="httpx.json",
        dataset_name=(
            "DevPilot AI Retrieval v3 Independent Validation - HTTPX"
        ),
        cases=HTTPX_CASES,
    ),
    RepositorySpec(
        key="vue-router",
        source="vuejs/router",
        tag="v5.2.0",
        local_directory="vue-router",
        dataset_filename="vue-router.json",
        dataset_name=(
            "DevPilot AI Retrieval v3 Independent Validation - Vue Router"
        ),
        cases=VUE_ROUTER_CASES,
    ),
    RepositorySpec(
        key="fastapi",
        source="fastapi/fastapi",
        tag="0.141.1",
        local_directory="fastapi",
        dataset_filename="fastapi.json",
        dataset_name=(
            "DevPilot AI Retrieval v3 Independent Validation - FastAPI"
        ),
        cases=FASTAPI_CASES,
    ),
)


DEVELOPMENT_REPOSITORIES = {
    "gothinkster/realworld",
    "pallets/click",
    "sindresorhus/ky",
    "commitizen-tools/commitizen",
    "axios/axios",
    "vuejs/pinia",
}


def run_git(
    repository: Path,
    *arguments: str,
) -> str:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            *arguments,
        ],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )

    return completed.stdout.strip()


def get_repository_sha(
    repository: Path,
) -> str:
    return run_git(
        repository,
        "rev-parse",
        "HEAD",
    )


def get_head_tags(
    repository: Path,
) -> set[str]:
    output = run_git(
        repository,
        "tag",
        "--points-at",
        "HEAD",
    )

    return {
        line.strip()
        for line in output.splitlines()
        if line.strip()
    }


def validate_repository(
    spec: RepositorySpec,
) -> tuple[Path, str]:
    repository = (
        BENCHMARK_ROOT
        / spec.local_directory
    )

    if not repository.is_dir():
        raise RuntimeError(
            f"No existe el repositorio local: {repository}"
        )

    git_directory = (
        repository
        / ".git"
    )

    if not git_directory.exists():
        raise RuntimeError(
            f"No es un repositorio Git: {repository}"
        )

    sha = get_repository_sha(
        repository
    )

    if len(sha) != 40:
        raise RuntimeError(
            f"SHA Git inválido para {spec.key}: {sha}"
        )

    tags = get_head_tags(
        repository
    )

    if spec.tag not in tags:
        raise RuntimeError(
            f"{spec.key}: HEAD no está en el tag "
            f"esperado {spec.tag}. Tags en HEAD: "
            f"{sorted(tags)}"
        )

    missing_files: list[str] = []

    for case in spec.cases:
        expected_path = (
            repository
            / Path(
                case.expected_file
            )
        )

        if not expected_path.is_file():
            missing_files.append(
                case.expected_file
            )

    if missing_files:
        formatted = "\n".join(
            f"  - {path}"
            for path in missing_files
        )

        raise RuntimeError(
            f"{spec.key}: faltan archivos esperados "
            f"en el commit congelado:\n{formatted}"
        )

    return repository, sha


def validate_cases() -> None:
    all_case_ids: list[str] = []

    for spec in REPOSITORIES:
        if len(spec.cases) != 10:
            raise RuntimeError(
                f"{spec.key}: se esperaban 10 casos, "
                f"hay {len(spec.cases)}"
            )

        for case in spec.cases:
            if not case.case_id.strip():
                raise RuntimeError(
                    f"{spec.key}: case_id vacío"
                )

            if not case.category.strip():
                raise RuntimeError(
                    f"{case.case_id}: category vacío"
                )

            if not case.question.strip():
                raise RuntimeError(
                    f"{case.case_id}: question vacío"
                )

            if not case.expected_file.strip():
                raise RuntimeError(
                    f"{case.case_id}: expected_file vacío"
                )

            all_case_ids.append(
                case.case_id
            )

    if len(all_case_ids) != 30:
        raise RuntimeError(
            f"Se esperaban 30 casos, "
            f"hay {len(all_case_ids)}"
        )

    duplicates = {
        case_id
        for case_id in all_case_ids
        if all_case_ids.count(
            case_id
        ) > 1
    }

    if duplicates:
        raise RuntimeError(
            "Hay IDs duplicados: "
            + ", ".join(
                sorted(
                    duplicates
                )
            )
        )


def build_dataset(
    spec: RepositorySpec,
    *,
    commit_sha: str,
) -> dict[str, Any]:
    return {
        "name": spec.dataset_name,
        "version": "1.0",
        "repository": {
            "key": spec.key,
            "source": spec.source,
            "tag": spec.tag,
            "commit": commit_sha,
        },
        "cases": [
            {
                "id": case.case_id,
                "category": case.category,
                "question": case.question,
                "expected_files": [
                    case.expected_file
                ],
            }
            for case in spec.cases
        ],
    }


def build_suite(
    repository_shas: dict[str, str],
) -> dict[str, Any]:
    return {
        "name": (
            "DevPilot AI Retrieval v3 "
            "Independent Validation"
        ),
        "version": "1.0",
        "status": "frozen-before-evaluation",
        "retrieval_version": "v3",
        "repositories": [
            {
                "key": spec.key,
                "source": spec.source,
                "tag": spec.tag,
                "commit": repository_shas[
                    spec.key
                ],
                "dataset": (
                    "evals/datasets/"
                    "v3_independent/"
                    f"{spec.dataset_filename}"
                ),
            }
            for spec in REPOSITORIES
        ],
        "methodology": {
            "purpose": (
                "Independent generalization evaluation "
                "for Retrieval v3"
            ),
            "development_datasets_excluded": sorted(
                DEVELOPMENT_REPOSITORIES
            ),
            "rules": [
                (
                    "Repositories must not have been used "
                    "for Retrieval v3 tuning."
                ),
                (
                    "Questions and expected files must be "
                    "frozen before running Retrieval v3."
                ),
                (
                    "No retrieval parameter may be changed "
                    "after inspecting validation results."
                ),
                (
                    "The validation run is one-shot for the "
                    "frozen Retrieval v3 configuration."
                ),
                (
                    "Any later tuning converts this dataset "
                    "into development data."
                ),
            ],
        },
    }


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    with path.open(
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


def main() -> None:
    print()
    print("=" * 100)
    print(
        "DEVPILOT AI - PREPARACIÓN BENCHMARK "
        "INDEPENDIENTE RETRIEVAL V3"
    )
    print("=" * 100)

    print()
    print(
        f"Repositorios locales: {BENCHMARK_ROOT}"
    )

    print(
        f"Salida:               {OUTPUT_DIR}"
    )

    print()

    validate_cases()

    repository_shas: dict[
        str,
        str,
    ] = {}

    datasets: dict[
        str,
        dict[str, Any],
    ] = {}

    for spec in REPOSITORIES:
        if (
            spec.source
            in DEVELOPMENT_REPOSITORIES
        ):
            raise RuntimeError(
                f"{spec.source} ya fue utilizado "
                "durante el desarrollo"
            )

        _, sha = validate_repository(
            spec
        )

        repository_shas[
            spec.key
        ] = sha

        datasets[
            spec.dataset_filename
        ] = build_dataset(
            spec,
            commit_sha=sha,
        )

        print(
            f"[OK] {spec.key:<12} "
            f"{spec.tag:<10} "
            f"{sha}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for filename, payload in datasets.items():
        write_json(
            OUTPUT_DIR
            / filename,
            payload,
        )

    suite = build_suite(
        repository_shas
    )

    write_json(
        OUTPUT_DIR
        / "suite.json",
        suite,
    )

    total_cases = sum(
        len(
            spec.cases
        )
        for spec in REPOSITORIES
    )

    total_expected_files = sum(
        len(
            spec.cases
        )
        for spec in REPOSITORIES
    )

    print()
    print("-" * 100)

    print(
        f"Repositorios:             "
        f"{len(REPOSITORIES)}"
    )

    print(
        f"Casos:                    "
        f"{total_cases}"
    )

    print(
        f"Archivos esperados:       "
        f"{total_expected_files}"
    )

    print(
        "Archivos esperados ausentes: 0"
    )

    print()
    print(
        "Datasets generados:"
    )

    for spec in REPOSITORIES:
        print(
            f"  - {OUTPUT_DIR / spec.dataset_filename}"
        )

    print(
        f"  - {OUTPUT_DIR / 'suite.json'}"
    )

    print()
    print("=" * 100)
    print(
        "PREFLIGHT CORRECTO"
    )
    print("=" * 100)

    print()
    print(
        "El benchmark todavía NO se ha ejecutado "
        "contra Retrieval v3."
    )

    print(
        "Puede congelarse ahora en Git."
    )


if __name__ == "__main__":
    main()