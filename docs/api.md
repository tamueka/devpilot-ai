# API de DevPilot AI

## Introducción

DevPilot AI expone una API REST desarrollada con FastAPI.

Durante el desarrollo local la URL base es:

```text
http://127.0.0.1:8000
```

FastAPI genera además documentación interactiva automáticamente:

```text
Swagger
http://127.0.0.1:8000/docs

ReDoc
http://127.0.0.1:8000/redoc
```

Este documento describe los endpoints principales utilizados por el frontend y
su responsabilidad dentro de la aplicación.

## Autenticación

La mayor parte de la API requiere autenticación mediante JWT.

Después de iniciar sesión, el frontend envía:

```http
Authorization: Bearer <access_token>
```

Si el token no existe, es inválido o ha expirado, la API responde normalmente:

```http
401 Unauthorized
```

## Registro de usuario

```http
POST /auth/register
```

Crea un nuevo usuario.

Ejemplo de petición:

```json
{
  "email": "usuario@example.com",
  "password": "password-seguro"
}
```

La contraseña no se almacena en texto plano.

El backend utiliza hashing basado en Argon2.

## Inicio de sesión

```http
POST /auth/login
```

Autentica al usuario y devuelve un access token JWT.

Ejemplo conceptual de respuesta:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

El frontend almacena el token en `sessionStorage`.

## Usuario autenticado

```http
GET /auth/me
```

Devuelve los datos del usuario asociado al token enviado en la petición.

Este endpoint también permite al frontend restaurar la sesión después de
recargar la aplicación.

## Proyectos

Los endpoints de proyectos están agrupados bajo:

```text
/projects
```

Todas las operaciones privadas validan el usuario autenticado.

## Crear proyecto

```http
POST /projects
```

Crea un nuevo proyecto y lo asigna al usuario autenticado.

Ejemplo:

```json
{
  "name": "Angular Ecommerce",
  "description": "Proyecto de comercio electrónico"
}
```

Respuesta:

```json
{
  "id": "uuid",
  "name": "Angular Ecommerce",
  "description": "Proyecto de comercio electrónico",
  "status": "CREATED",
  "uploaded_file": null
}
```

Código esperado:

```http
201 Created
```

## Listar proyectos

```http
GET /projects
```

Devuelve únicamente los proyectos pertenecientes al usuario autenticado.

Ejemplo conceptual:

```json
[
  {
    "id": "uuid",
    "name": "Angular Ecommerce",
    "description": "Proyecto Angular",
    "status": "INDEXED",
    "uploaded_file": "storage/projects/.../project.zip"
  }
]
```

La consulta está filtrada por `owner_id`.

## Obtener proyecto

```http
GET /projects/{project_id}
```

Devuelve un proyecto concreto.

Ejemplo:

```text
GET /projects/550e8400-e29b-41d4-a716-446655440000
```

El backend valida que el proyecto pertenezca al usuario autenticado.

Si el proyecto no existe o pertenece a otro usuario:

```http
404 Not Found
```

Este comportamiento evita revelar la existencia de recursos pertenecientes a
otros usuarios.

## Subir e indexar proyecto

```http
POST /projects/{project_id}/upload
```

Importa un archivo comprimido y ejecuta el pipeline de indexación.

La petición utiliza:

```text
multipart/form-data
```

Campo:

```text
file
```

Formatos admitidos:

```text
.zip
.rar
```

Ejemplo conceptual:

```http
POST /projects/{project_id}/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

El proceso ejecutado es:

```text
Upload
  ↓
Validación
  ↓
Extracción segura
  ↓
Filtrado
  ↓
Documents
  ↓
Chunks
  ↓
Embeddings
  ↓
pgvector
  ↓
INDEXED
```

Los estados intermedios del proyecto son:

```text
CREATED
EXTRACTED
INDEXED_FILES
CHUNKED
INDEXED
```

### Archivo incorrecto

Si el archivo no tiene extensión ZIP o RAR:

```http
400 Bad Request
```

### Archivo demasiado grande

El tamaño máximo de upload configurado es:

```text
50 MB
```

Si se supera:

```http
413 Content Too Large
```

Ejemplo de respuesta:

```json
{
  "detail": "El archivo comprimido supera el tamaño máximo permitido de 50 MB."
}
```

### Archivo comprimido inseguro

La API también puede devolver:

```http
400 Bad Request
```

si detecta entradas inseguras como:

```text
Path Traversal
Rutas absolutas
Symlinks
Archivos demasiado grandes
Archives manipulados
```

## Eliminar proyecto

```http
DELETE /projects/{project_id}
```

Elimina completamente un proyecto perteneciente al usuario.

La operación elimina los datos relacionados en base de datos y posteriormente
el almacenamiento local asociado.

Respuesta:

```http
204 No Content
```

La eliminación está protegida mediante ownership.

Un usuario no puede eliminar un proyecto perteneciente a otro usuario.

## Documentos de un proyecto

```http
GET /projects/{project_id}/documents
```

Devuelve los documentos indexados de un proyecto.

El proyecto debe encontrarse en estado:

```text
INDEXED
```

Ejemplo conceptual:

```json
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "path": "src/app/app.ts",
    "filename": "app.ts",
    "extension": ".ts",
    "language": "typescript",
    "size": 2048
  }
]
```

Si el proyecto todavía no está completamente indexado:

```http
409 Conflict
```

Esta operación se utiliza principalmente para seleccionar el archivo sobre el
que se generarán tests unitarios.

## Chat RAG

```http
POST /chat
```

Realiza una pregunta sobre un proyecto indexado.

Ejemplo de petición:

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "¿Cómo funciona la autenticación?",
  "top_k": 5
}
```

Para continuar una conversación existente:

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "7cf36719-63ae-4dcb-86ac-5736274a15b7",
  "message": "¿Y dónde se guarda el token?",
  "top_k": 5
}
```

`conversation_id` es opcional.

Si no se proporciona, DevPilot crea una nueva conversación.

## Flujo interno del chat

```text
POST /chat
   ↓
Validación de usuario
   ↓
Validación de ownership
   ↓
Proyecto INDEXED
   ↓
Embedding de pregunta
   ↓
Búsqueda semántica
   ↓
Top-K chunks
   ↓
Historial de conversación
   ↓
LLM
   ↓
Guardar respuesta
   ↓
Respuesta + fuentes
```

El frontend utiliza normalmente:

```text
top_k = 5
```

## Respuesta del chat

La respuesta contiene información equivalente a:

```json
{
  "conversation_id": "uuid",
  "answer": "La aplicación utiliza...",
  "sources": [
    {
      "path": "src/app/core/auth/auth.store.ts",
      "language": "typescript",
      "chunk_index": 0,
      "excerpt": "..."
    }
  ]
}
```

Las fuentes permiten al usuario conocer qué partes del proyecto fueron
utilizadas para construir la respuesta.

## Errores del chat

### Proyecto inexistente

```http
404 Not Found
```

### Proyecto no indexado

```http
409 Conflict
```

### Conversación inexistente

```http
404 Not Found
```

### Conversación perteneciente a otro proyecto

La API rechaza el uso de una conversación que no corresponda al proyecto
indicado.

### Error interno del proveedor de IA

Los detalles internos del proveedor no deben enviarse al cliente.

La API utiliza mensajes controlados para evitar exponer:

```text
API keys
Tokens
Paths internos
Stack traces
Configuración sensible
```

## Historial de conversaciones

El chat guarda las conversaciones y sus mensajes.

El frontend dispone de operaciones para:

```text
Obtener conversaciones de un proyecto
Obtener una conversación concreta
Recuperar sus mensajes
Continuar una conversación existente
```

Las rutas exactas disponibles para estas operaciones pueden consultarse en el
OpenAPI generado por FastAPI:

```text
http://127.0.0.1:8000/docs
```

La creación de nuevas conversaciones se realiza automáticamente desde
`POST /chat` cuando no se proporciona `conversation_id`.

## Generar README

```http
POST /projects/{project_id}/readme
```

Genera documentación Markdown a partir del proyecto indexado.

Ejemplo:

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "es"
}
```

El `project_id` enviado en el cuerpo debe corresponder con el identificador de
la URL.

El proyecto debe estar:

```text
INDEXED
```

## Flujo de generación del README

```text
Proyecto
   ↓
Semantic Search
   ↓
Contexto relevante
   ↓
ReadmeService
   ↓
LLM
   ↓
Markdown
   ↓
Fuentes
```

Ejemplo conceptual de respuesta:

```json
{
  "content": "# Proyecto\n\nDescripción...",
  "sources": [
    {
      "path": "src/app/app.ts",
      "language": "typescript"
    }
  ]
}
```

El frontend permite posteriormente:

```text
Visualizar
Copiar
Descargar README.md
```

## Errores de generación de README

Puede responder:

```http
400 Bad Request
```

si los identificadores de proyecto no coinciden.

```http
404 Not Found
```

si el proyecto no existe o no pertenece al usuario.

```http
409 Conflict
```

si el proyecto todavía no está indexado.

```http
422 Unprocessable Content
```

si no existe contexto suficiente para generar documentación.

```http
500 Internal Server Error
```

si el servicio de IA no está disponible.

Los errores internos sensibles no se devuelven directamente al cliente.

## Generar tests unitarios

```http
POST /projects/{project_id}/unit-tests
```

Genera tests para un documento concreto.

Ejemplo:

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "7cf36719-63ae-4dcb-86ac-5736274a15b7",
  "framework": null
}
```

Opcionalmente puede indicarse un framework:

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "7cf36719-63ae-4dcb-86ac-5736274a15b7",
  "framework": "Vitest"
}
```

El backend valida que:

```text
El usuario sea propietario del proyecto
El proyecto exista
El proyecto esté INDEXED
El document_id pertenezca al proyecto
El project_id del body coincida con la URL
```

## Respuesta de generación de tests

Ejemplo conceptual:

```json
{
  "content": "describe('App', () => { ... });",
  "suggested_filename": "app.spec.ts",
  "sources": [
    {
      "path": "src/app/app.ts",
      "language": "typescript"
    }
  ]
}
```

La API genera también un nombre de archivo sugerido según el lenguaje.

Ejemplos:

```text
TypeScript → app.spec.ts
JavaScript → app.test.js
Python → test_app.py
```

## Errores de generación de tests

Los códigos relevantes incluyen:

```text
400  project_id inconsistente
401  usuario no autenticado
404  proyecto o documento inexistente
409  proyecto no indexado
422  documento o contexto no válido
429  rate limit
500  servicio de IA o generación no disponible
```

## Rate limiting

Las operaciones de mayor coste disponen de limitación de peticiones.

Entre ellas se encuentran operaciones como:

```text
Chat
Uploads
Generación de README
Generación de tests
```

Cuando el límite se supera:

```http
429 Too Many Requests
```

## Ownership

DevPilot AI utiliza el usuario autenticado como parte del control de acceso.

Conceptualmente:

```text
Request
   ↓
JWT
   ↓
Current User
   ↓
Resource lookup
   ↓
owner_id == current_user.id
   ↓
Allowed
```

Para evitar filtraciones de información, el acceso a recursos pertenecientes a
otro usuario puede responder como recurso inexistente:

```http
404 Not Found
```

## CORS

Durante desarrollo se permite el frontend configurado, por ejemplo:

```text
http://localhost:4200
```

Los métodos necesarios incluyen:

```text
GET
POST
DELETE
OPTIONS
```

`OPTIONS` es utilizado por el navegador para las peticiones CORS preflight.

## Formato de errores

FastAPI devuelve habitualmente errores funcionales mediante:

```json
{
  "detail": "Mensaje de error"
}
```

El frontend utiliza el campo `detail` para proporcionar feedback al usuario
cuando es seguro mostrarlo.

## Resumen de endpoints principales

| Método | Endpoint | Función |
| --- | --- | --- |
| POST | `/auth/register` | Registrar usuario |
| POST | `/auth/login` | Iniciar sesión |
| GET | `/auth/me` | Obtener usuario actual |
| POST | `/projects` | Crear proyecto |
| GET | `/projects` | Listar proyectos |
| GET | `/projects/{project_id}` | Obtener proyecto |
| POST | `/projects/{project_id}/upload` | Importar e indexar |
| DELETE | `/projects/{project_id}` | Eliminar proyecto |
| GET | `/projects/{project_id}/documents` | Listar documentos |
| POST | `/chat` | Consultar proyecto mediante RAG |
| POST | `/projects/{project_id}/readme` | Generar README |
| POST | `/projects/{project_id}/unit-tests` | Generar tests |

## Swagger como referencia definitiva

Este documento resume la API desde el punto de vista funcional.

La referencia técnica generada directamente desde el código debe consultarse
en:

```text
http://127.0.0.1:8000/docs
```

Swagger muestra automáticamente:

```text
Endpoints
Schemas
Request bodies
Response models
Validaciones
Códigos HTTP
```

Por tanto, `docs/api.md` proporciona la explicación arquitectónica y funcional,
mientras que OpenAPI actúa como contrato técnico ejecutable.
