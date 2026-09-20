# Validación Independiente de Retrieval v3

Este directorio contiene el benchmark independiente congelado utilizado
para evaluar la capacidad de generalización de DevPilot AI Retrieval v3.

## Objetivo

Este benchmark está separado intencionadamente de todos los datasets
utilizados durante el desarrollo de Retrieval v1, v2 y v3.

Los siguientes repositorios quedan excluidos porque ya han sido
utilizados durante el desarrollo o el diagnóstico:

- RealWorld Angular
- Pallets Click
- Ky
- Commitizen
- Axios
- Pinia

## Protocolo de congelación

Antes de ejecutar Retrieval v3:

1. Seleccionar nuevos repositorios.
2. Congelar cada repositorio en un commit SHA exacto de Git.
3. Crear las preguntas de evaluación.
4. Verificar que todos los archivos esperados existen en el commit congelado.
5. Congelar los datasets.
6. Hacer commit del benchmark en Git.
7. No modificar Retrieval v3 después de inspeccionar los resultados de validación.

## Protocolo de evaluación

Configuración congelada de Retrieval v3:

- Candidatos vectoriales: 20
- Candidatos léxicos: 20
- Candidatos por ruta: 20
- Fusión: Best-Rank
- Candidatos enviados al reranker: 20
- Documentos finales: 5

El benchmark solo debe ejecutarse una vez que tanto la configuración de
Retrieval v3 como el dataset hayan sido congelados.

## Interpretación

Los resultados de este benchmark solo pueden utilizarse como evidencia
de generalización de Retrieval v3 mientras el benchmark permanezca
sin modificaciones después de la primera evaluación.

Si posteriormente sus resultados se utilizan para ajustar Retrieval v3,
este benchmark pasa a considerarse datos de desarrollo y será necesario
crear un nuevo benchmark independiente.