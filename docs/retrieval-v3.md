# Retrieval v3

Retrieval v3 es la evolución del sistema de recuperación RAG de DevPilot AI
preparada para la versión `v1.2.0`.

## Objetivo

El objetivo principal es mejorar la capacidad de recuperar el archivo correcto
en repositorios no vistos anteriormente, manteniendo una arquitectura de
retrieval multifuente y evitando ajustes específicos para archivos concretos.

## Arquitectura

Retrieval v3 utiliza tres fuentes de candidatos:

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
