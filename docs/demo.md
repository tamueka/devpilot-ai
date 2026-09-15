# Guion de demostración de DevPilot AI

## Objetivo de la demo

La demostración debe enseñar de forma clara el valor principal de DevPilot AI:

```text
Importar un proyecto
        ↓
Indexarlo
        ↓
Consultarlo mediante lenguaje natural
        ↓
Obtener respuestas con contexto real
        ↓
Generar documentación y tests
```

La demo está pensada para durar aproximadamente entre 5 y 7 minutos.

## Preparación previa

Antes de comenzar la defensa deben estar iniciados:

```text
PostgreSQL
Backend FastAPI
Frontend Angular
```

También debe existir una conexión funcional con el proveedor de IA.

Comprobar:

```text
Frontend
http://localhost:4200

Backend
http://127.0.0.1:8000

Swagger
http://127.0.0.1:8000/docs
```

## Estado inicial recomendado

Antes de iniciar la presentación:

- Tener la base de datos operativa.
- Tener preparado un usuario válido.
- Tener preparado un proyecto ZIP o RAR pequeño.
- Evitar usar un proyecto excesivamente grande durante la demo.
- Tener backend y frontend ya iniciados.
- Tener abierta la aplicación en la pantalla de login.
- Evitar realizar instalaciones o migraciones durante la defensa.

## Estructura general de la demo

La demostración se divide en los siguientes bloques:

```text
1. Login
2. Crear proyecto
3. Importar código
4. Indexación
5. Chat RAG
6. Fuentes
7. Conversación
8. README generado
9. Tests unitarios
10. Eliminación del proyecto
```

## Paso 1 - Autenticación

### Acción durante la autenticación

Mostrar la pantalla de login.

Iniciar sesión con un usuario previamente creado.

### Explicación de la autenticación

Texto recomendado:

```text
DevPilot AI incorpora autenticación JWT y aislamiento de recursos por usuario.
Cada usuario únicamente puede acceder a sus propios proyectos,
conversaciones y documentos.
```

### Aspectos clave de autenticación

```text
JWT
Rutas protegidas
Ownership
Restauración de sesión
```

No es necesario detenerse demasiado en esta parte.

Tiempo aproximado:

```text
20 - 30 segundos
```

## Paso 2 - Crear un proyecto

### Acción de creación del proyecto

Desde la pantalla de proyectos crear uno nuevo.

Ejemplo:

```text
Nombre:
Demo Angular

Descripción:
Proyecto de ejemplo para la defensa de DevPilot AI
```

### Explicación de creación del proyecto

Texto recomendado:

```text
Un proyecto es la unidad principal de trabajo de la aplicación.

A partir de él se almacenan documentos, chunks, embeddings,
conversaciones y mensajes.
```

### Aspectos clave de creación

El proyecto aparece inicialmente como pendiente porque todavía no se ha
indexado ningún repositorio.

Tiempo aproximado:

```text
20 segundos
```

## Paso 3 - Importar código fuente

### Acción de importación

Seleccionar:

```text
Subir ZIP / RAR
```

y cargar el proyecto preparado para la demo.

### Explicación de la importación

Texto recomendado:

```text
DevPilot AI admite proyectos comprimidos en ZIP y RAR.

Antes de indexarlos, el backend valida el archivo y realiza una
extracción segura.
```

### Seguridad durante la importación

La aplicación incorpora protecciones frente a:

```text
Path Traversal
Rutas absolutas
Symlinks
Archivos demasiado grandes
Archives manipulados
```

También se filtran directorios irrelevantes como:

```text
node_modules
dist
build
coverage
.git
```

Tiempo aproximado:

```text
30 - 45 segundos
```

## Paso 4 - Indexación

### Acción durante la indexación

Esperar a que el proyecto alcance el estado:

```text
Indexado
```

### Explicación del pipeline de indexación

Mientras se procesa, explicar este flujo:

```text
Archivo
   ↓
Extracción
   ↓
Documentos
   ↓
Chunking
   ↓
Embeddings
   ↓
PostgreSQL + pgvector
```

Texto recomendado:

```text
El proyecto no se envía completo al modelo.

Primero se transforma en documentos, después en fragmentos y finalmente
en embeddings que se almacenan en pgvector.

Esto permite recuperar únicamente las partes relevantes del código cuando
el usuario realiza una pregunta.
```

### Aspectos clave de la indexación

Destacar:

```text
Procesamiento selectivo
Chunking
Embeddings
Almacenamiento vectorial
Búsqueda semántica
```

Tiempo aproximado:

```text
30 - 45 segundos
```

## Paso 5 - Abrir el chat RAG

### Acción en el chat

Pulsar:

```text
Abrir chat
```

El proyecto debería quedar seleccionado automáticamente.

Realizar una primera pregunta.

Pregunta recomendada:

```text
Explícame la arquitectura principal de este proyecto.
```

Otra opción:

```text
¿Cómo funciona la autenticación de esta aplicación?
```

### Explicación del chat RAG

Mientras se genera la respuesta explicar:

```text
La pregunta también se transforma en un embedding.

Después se compara con los vectores almacenados en pgvector y se
recuperan los chunks más relacionados.
```

El flujo es:

```text
Pregunta
   ↓
Embedding
   ↓
Semantic Search
   ↓
Top-K chunks
   ↓
Prompt + contexto
   ↓
LLM
   ↓
Respuesta
```

### Aspectos clave del chat

Destacar:

```text
Semantic Search
Top-K
RAG
Contexto real del repositorio
LLM
```

Tiempo aproximado:

```text
45 - 60 segundos
```

## Paso 6 - Mostrar las fuentes

### Acción al mostrar las fuentes

Abrir o señalar las fuentes asociadas a la respuesta generada.

### Explicación de las fuentes

Texto recomendado:

```text
Una diferencia importante frente a un chat genérico es que DevPilot AI
muestra qué archivos del repositorio fueron utilizados para construir
la respuesta.
```

### Valor de las fuentes

Las fuentes permiten:

```text
Verificar la respuesta
Localizar código relevante
Reducir respuestas sin contexto
Mejorar la trazabilidad
```

Este punto es especialmente importante porque demuestra que realmente existe
un sistema RAG.

Tiempo aproximado:

```text
20 - 30 segundos
```

## Paso 7 - Continuar la conversación

### Acción de continuación

Realizar una segunda pregunta relacionada con la anterior.

Ejemplo:

```text
¿Dónde se implementa esa lógica?
```

Otra posibilidad:

```text
¿Qué archivos participan en ese flujo?
```

### Explicación del contexto conversacional

Texto recomendado:

```text
Las conversaciones se almacenan en base de datos y el sistema puede
reutilizar parte del historial para mantener el contexto entre mensajes.
```

### Aspectos clave de conversación

```text
Conversation
Messages
History
RAG context
```

Tiempo aproximado:

```text
20 - 30 segundos
```

## Paso 8 - Generar README

### Acción de generación de documentación

Volver a la pantalla de proyectos.

Pulsar:

```text
Generar README
```

### Explicación de generación de README

Texto recomendado:

```text
La generación de documentación reutiliza la misma infraestructura RAG.

El backend recupera información relevante del proyecto y la utiliza para
generar documentación basada en el código real.
```

### Elementos que mostrar del README

En el modal enseñar:

```text
Contenido generado
Fuentes analizadas
Botón copiar
Botón descargar
```

Destacar que el resultado no depende únicamente del conocimiento general del
modelo.

El proyecto indexado se utiliza como contexto para generar el documento.

Tiempo aproximado:

```text
30 - 45 segundos
```

## Paso 9 - Generar tests unitarios

### Acción de generación de tests

Pulsar:

```text
Generar tests
```

Seleccionar un archivo del proyecto.

Ejemplo:

```text
src/app/app.ts
```

Pulsar:

```text
Generar tests con IA
```

### Explicación de generación de tests

Texto recomendado:

```text
En este caso el usuario selecciona un documento concreto.

DevPilot AI combina ese archivo con contexto semánticamente relacionado
del mismo proyecto para generar el test.
```

El flujo es:

```text
Documento seleccionado
        ↓
Contexto relacionado
        ↓
RAG
        ↓
LLM
        ↓
Test generado
```

### Elementos que mostrar de los tests

Mostrar:

```text
Nombre de archivo sugerido
Código generado
Fuentes utilizadas
Copiar
Descargar
```

Tiempo aproximado:

```text
40 - 60 segundos
```

## Paso 10 - Eliminar proyecto

### Acción de eliminación

Abrir el menú:

```text
⋮
```

Pulsar:

```text
Eliminar proyecto
```

Mostrar el modal de confirmación.

Explicar la operación antes de confirmar.

Finalmente confirmar la eliminación.

### Explicación de eliminación

Texto recomendado:

```text
La eliminación también está protegida mediante ownership.

El backend elimina el proyecto y los datos relacionados, además del
almacenamiento local correspondiente.
```

### Aspectos clave de eliminación

```text
Confirmación explícita
DELETE API
Ownership
Cascade
Storage cleanup
```

Tiempo aproximado:

```text
20 segundos
```

## Cierre de la demostración

Después de eliminar el proyecto, cerrar con una explicación breve.

Texto recomendado:

```text
Con este flujo hemos visto el ciclo principal de DevPilot AI:
autenticación, importación de un repositorio, indexación vectorial,
consultas mediante RAG, generación de documentación y generación
de tests.

El objetivo del proyecto no es sustituir al desarrollador, sino reducir
el tiempo necesario para comprender y trabajar con una base de código
existente.
```

## Resumen visual del flujo

```text
Usuario
   ↓
Crear proyecto
   ↓
ZIP / RAR
   ↓
Extracción segura
   ↓
Documentos
   ↓
Chunks
   ↓
Embeddings
   ↓
pgvector
   ↓
Semantic Search
   ↓
RAG
   ↓
LLM
   ↓
Chat / README / Tests
```

## Duración recomendada

Distribución aproximada:

| Parte | Tiempo |
| --- | ---: |
| Login | 0:20 |
| Crear proyecto | 0:20 |
| Upload | 0:30 |
| Indexación | 0:40 |
| Chat RAG | 1:00 |
| Fuentes | 0:25 |
| Conversación | 0:25 |
| README | 0:40 |
| Tests | 0:50 |
| Eliminación | 0:20 |
| Cierre | 0:20 |

Duración aproximada total:

```text
5 - 7 minutos
```

## Preguntas recomendadas para la demostración

Conviene probar previamente varias preguntas y seleccionar las que produzcan
respuestas claras.

Buenas opciones:

```text
Explícame la arquitectura principal de este proyecto.

¿Cómo funciona la autenticación?

¿Qué hace este servicio?

¿Dónde se realizan las llamadas HTTP?

¿Qué archivos participan en el login?

¿Cómo se gestiona el estado?

¿Qué responsabilidades tiene este componente?
```

Evitar durante la demo preguntas demasiado abiertas como:

```text
Explícame todo el proyecto.
```

También conviene evitar consultas sobre información que no exista en el
repositorio.

## Plan alternativo ante fallo de la IA

Una demostración técnica debe tener un plan alternativo.

Si el proveedor de IA no responde durante la presentación:

1. Mostrar que el proyecto está indexado.
2. Explicar el pipeline utilizando el diagrama.
3. Mostrar capturas previamente preparadas del chat.
4. Mostrar las fuentes recuperadas.
5. Mostrar un README generado previamente.
6. Mostrar tests generados previamente.
7. Continuar con la explicación arquitectónica.

La defensa no debería depender completamente de una API externa.

## Plan alternativo ante una indexación lenta

Tener preparado previamente un proyecto ya indexado.

De este modo se puede explicar:

```text
Voy a utilizar este proyecto, que ya he indexado previamente, para no
consumir tiempo de la defensa esperando al procesamiento.
```

Después continuar directamente con el chat.

## Plan alternativo para archivos RAR

Durante la defensa utilizar preferentemente un archivo ZIP.

RAR puede mencionarse como formato soportado y probado, pero ZIP reduce la
dependencia de herramientas externas durante una demostración en otro equipo.

## Checklist técnico antes de la defensa

```text
[ ] PostgreSQL iniciado
[ ] pgvector disponible
[ ] Backend iniciado
[ ] Frontend iniciado
[ ] .env configurado
[ ] API de IA accesible
[ ] Usuario de demo preparado
[ ] Proyecto ZIP preparado
[ ] Proyecto ya indexado como backup
[ ] Preguntas de demo probadas
[ ] README generado previamente como backup
[ ] Tests generados previamente como backup
[ ] Navegador preparado
[ ] Zoom del navegador adecuado
[ ] Notificaciones del sistema desactivadas
```

## Checklist de información sensible

Antes de compartir pantalla comprobar que no sean visibles:

```text
OPENAI_API_KEY
JWT_SECRET_KEY
DATABASE_URL con password
.env
Tokens JWT
Credenciales personales
Terminales con secretos
```

No abrir `.env` durante la defensa.

## Mensaje principal de la defensa

La idea principal que debe quedar clara es:

```text
DevPilot AI transforma el código fuente de un proyecto en una base de
conocimiento vectorial y utiliza RAG para permitir que un desarrollador
consulte, documente y genere tests utilizando el contexto real del
repositorio.
```
