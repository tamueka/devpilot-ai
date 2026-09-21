# DevPilot AI v1.2.0 — Retrieval v3

## Resumen

DevPilot AI `v1.2.0` introduce Retrieval v3, una evolución del pipeline RAG orientada a mejorar la recuperación de archivos relevantes en repositorios no vistos anteriormente.

Retrieval v3 mantiene una arquitectura multifuente basada en:

- Vector Retrieval
- Lexical Retrieval
- Path Retrieval
- Best-Rank Fusion
- LLM Reranking

La versión incorpora mejoras específicas en la generación y selección de candidatos antes del reranking.

---

## Retrieval v3

Pipeline:

```text
Pregunta
   |
   +--> Vector Retrieval  @20
   |
   +--> Lexical Retrieval @20
   |
   +--> Path Retrieval    @20
                |
                v
          Best-Rank Fusion
                |
                v
             Top 20
                |
                v
           LLM Reranker
                |
                v
              Top 5


## Estado de evaluación

La implementación de Retrieval v3 y su benchmark independiente quedaron
congelados antes de la publicación de esta versión.

La ejecución final de las evaluaciones que requieren Vector Retrieval y LLM
Reranking no se realizó durante el cierre de la versión debido a que la cuenta
API externa utilizada por el entorno de evaluación no disponía de crédito.

El proveedor respondió con:

```text
HTTP 429
type: insufficient_quota
code: credit_balance_exhausted
