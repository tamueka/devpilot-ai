# DevPilot AI

**DevPilot AI** es una plataforma de asistencia para desarrolladores que permite analizar bases de código mediante Inteligencia Artificial y Retrieval-Augmented Generation (RAG).

El objetivo principal es reducir el tiempo necesario para comprender un proyecto desconocido, permitiendo importar un repositorio, indexar su código fuente y realizar consultas en lenguaje natural con trazabilidad sobre los archivos utilizados para generar cada respuesta.

El proyecto fue desarrollado originalmente como Trabajo Final de Máster y continúa evolucionando como proyecto personal orientado a experimentación con RAG, evaluación de recuperación, generación asistida de código y herramientas para desarrolladores.

---

## Estado del proyecto

Versión estable actual:

```text
v1.0.1
```

La versión `v1.0.0` corresponde al MVP presentado y aprobado como Trabajo Final de Máster.

La versión `v1.0.1` mejora principalmente la reproducibilidad del entorno y la instalación desde un repositorio limpio.

Estado actual:

```text
Backend tests:   236 passed
Frontend tests:  60 passed
Frontend build:  OK
npm audit:       0 vulnerabilities
```

---

## Problema que resuelve

Entrar en una base de código desconocida suele requerir revisar manualmente:

- estructura del proyecto;
- arquitectura;
- servicios;
- componentes;
- modelos;
- dependencias;
- configuración;
- flujos de datos;
- autenticación;
- tests;
- relaciones entre módulos.

DevPilot AI transforma el código fuente en una base de conocimiento consultable mediante IA.

En lugar de recorrer manualmente decenas o cientos de archivos, el desarrollador puede realizar preguntas como:

```text
¿Cómo funciona la autenticación?

¿Dónde se almacena el token JWT?

Explícame la arquitectura principal del proyecto.

¿Qué servicios intervienen en la creación de proyectos?

¿Qué medidas de seguridad existen?

¿Cómo funciona el flujo RAG?

¿Qué archivos participan en esta funcionalidad?
```

La respuesta se genera utilizando contexto recuperado directamente del código indexado.

---

## Funcionalidades principales

DevPilot AI incluye actualmente:

- Registro y autenticación de usuarios.
- Autenticación mediante JWT.
- Aislamiento de proyectos por usuario.
- Creación y eliminación de proyectos.
- Importación de proyectos mediante ZIP.
- Importación de proyectos mediante RAR.
- Extracción segura de archivos.
- Filtrado de archivos sensibles.
- Filtrado de directorios innecesarios.
- Indexación automática del código fuente.
- División del código en chunks.
- Generación de embeddings.
- Almacenamiento vectorial con PostgreSQL y pgvector.
- Búsqueda semántica.
- Chat RAG sobre el proyecto.
- Historial conversacional.
- Visualización de fuentes utilizadas por la IA.
- Generación automática de README.
- Generación de tests unitarios.
- Descarga de contenido generado.
- Protección frente a prompt injection.
- Redacción de secretos.
- Limitación de tamaño de uploads.
- Rate limiting.
- Protección contra accesos IDOR.
- Sanitización de contenido generado.
- CORS restringido.
- Security headers.
- Validación de hosts.

---

## Arquitectura general

La aplicación está dividida en dos grandes componentes:

```text
DevPilot AI
│
├── Frontend
│   └── Angular
│
├── Backend
│   └── FastAPI
│
├── PostgreSQL
│   └── pgvector
│
└── OpenAI API
    ├── embeddings
    └── generación
```

Flujo principal:

```mermaid
flowchart LR
    A[Usuario] --> B[Angular]
    B --> C[FastAPI]
    C --> D[PostgreSQL]
    D --> E[pgvector]
    C --> F[OpenAI API]
```

---

## Flujo RAG

El núcleo de DevPilot AI utiliza Retrieval-Augmented Generation.

El proceso de indexación es:

```mermaid
flowchart TD
    A[Proyecto ZIP/RAR]
    --> B[Extracción segura]
    --> C[Filtrado de archivos]
    --> D[Documentos]
    --> E[Chunking]
    --> F[Embeddings]
    --> G[PostgreSQL + pgvector]
```

El flujo de consulta es:

```mermaid
flowchart TD
    A[Pregunta del usuario]
    --> B[Embedding de la consulta]
    --> C[Búsqueda semántica]
    --> D[Chunks relevantes]
    --> E[Construcción del contexto]
    --> F[LLM]
    --> G[Respuesta]
    --> H[Fuentes utilizadas]
```

Esto permite que el modelo responda utilizando información obtenida directamente del repositorio.

---

## Stack tecnológico

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- psycopg
- OpenAI Python SDK
- Pydantic
- PyJWT
- pwdlib
- Argon2
- pytest

### Frontend

- Angular 22
- TypeScript
- Angular Signals
- Reactive Forms
- RxJS
- Standalone Components
- Angular Router
- Tailwind CSS 4
- Vitest

### Infraestructura y herramientas

- Git
- GitHub
- PostgreSQL
- pgvector
- OpenAI API
- npm
- NVM

---

## Arquitectura frontend

El frontend aplica una separación inspirada en Clean Architecture:

```text
presentation
     ↓
application
     ↓
domain
     ↑
infrastructure
```

Estructura simplificada:

```text
src/app/
│
├── core/
│   ├── application/
│   ├── auth/
│   ├── domain/
│   └── infrastructure/
│
├── features/
│   ├── auth/
│   ├── chat/
│   └── projects/
│
└── main-layout/
```

Las dependencias están orientadas hacia el dominio.

La capa de dominio no depende de Angular HTTP ni de detalles concretos de infraestructura.

---

## Arquitectura backend

El backend utiliza una arquitectura modular basada en routers, servicios, seguridad, modelos y esquemas.

```text
backend/app/
│
├── db/
│   ├── database.py
│   └── models.py
│
├── routers/
│   ├── auth.py
│   ├── chat.py
│   ├── conversations.py
│   ├── projects.py
│   └── readme.py
│
├── schemas/
│
├── security/
│
├── services/
│
└── main.py
```

Entre los principales servicios se encuentran:

```text
project_archive_service
project_document_service
project_chunk_service
project_embedding_service
semantic_search_service
rag_service
conversation_service
readme_service
unit_test_service
```

---

## Modelo de datos

Las principales entidades son:

```text
User
Project
Document
Chunk
Conversation
Message
```

Relaciones principales:

```text
User
 └── Projects
      ├── Documents
      │    └── Chunks
      │
      └── Conversations
           └── Messages
```

Los chunks almacenan embeddings vectoriales utilizados posteriormente durante la recuperación semántica.

---

## Archivos procesados

DevPilot AI procesa principalmente archivos de código y configuración.

Extensiones admitidas:

```text
.ts
.js
.jsx
.tsx
.py
.java
.cs
.go
.html
.css
.scss
.md
.json
.yaml
.yml
.xml
```

Durante la indexación se excluyen directorios y archivos que no aportan valor al análisis, como dependencias, builds y artefactos generados.

También se aplican filtros destinados a evitar la indexación accidental de secretos.

---

## Seguridad

La aplicación incorpora diferentes mecanismos de seguridad.

### Seguridad de archivos

La extracción de ZIP y RAR incluye protecciones frente a:

- path traversal;
- rutas absolutas;
- symlinks peligrosos;
- archivos excesivamente grandes;
- archivos comprimidos potencialmente maliciosos;
- número excesivo de archivos;
- extracción total excesiva.

### Protección de secretos

DevPilot AI evita procesar determinados archivos sensibles y aplica mecanismos de redacción sobre contenido potencialmente confidencial.

Ejemplos:

```text
.env
private keys
tokens
passwords
API keys
credentials
```

### Seguridad de autenticación

La autenticación utiliza:

```text
JWT
Argon2
Bearer Authentication
```

Los endpoints protegidos validan que el recurso solicitado pertenece al usuario autenticado.

### Seguridad del RAG

Se incluyen pruebas destinadas a comprobar:

- prompt injection;
- filtrado de secretos;
- aislamiento de usuarios;
- sanitización del contenido generado;
- prevención de URLs JavaScript;
- manejo seguro de errores.

### Seguridad HTTP

También se incluyen:

- CORS restringido;
- TrustedHost;
- security headers;
- límites de tamaño;
- rate limiting.

---

## Requisitos del sistema

### Requisitos del backend

Se recomienda:

```text
Python 3.13 o Python 3.14
PostgreSQL
pgvector
```

La instalación limpia de esta versión se ha validado correctamente con:

```text
Python 3.14.0
```

El proyecto fue desarrollado originalmente utilizando Python 3.13.

### Requisitos del frontend

La versión validada es:

```text
Node.js 26.4.0
npm 11.17.0
```

El repositorio incluye un archivo:

```text
.nvmrc
```

con la versión recomendada de Node.js.

### Servicios externos

Para utilizar las funcionalidades de IA es necesario disponer de una API key válida de OpenAI.

---

## Clonar el proyecto

```powershell
git clone https://github.com/tamueka/devpilot-ai.git
cd devpilot-ai
```

También es posible utilizar SSH:

```powershell
git clone git@github.com:tamueka/devpilot-ai.git
cd devpilot-ai
```

---

## Configuración del backend

Accede al directorio:

```powershell
cd backend
```

Crea un entorno virtual:

```powershell
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

En Linux/macOS:

```bash
source .venv/bin/activate
```

Actualiza pip:

```powershell
python -m pip install --upgrade pip
```

Instala las dependencias de ejecución:

```powershell
python -m pip install -r requirements.txt
```

Comprueba las dependencias:

```powershell
python -m pip check
```

El resultado esperado es:

```text
No broken requirements found.
```

---

## Dependencias de desarrollo del backend

Para ejecutar tests y herramientas de desarrollo:

```powershell
python -m pip install -r requirements-dev.txt
```

Este archivo incluye las dependencias de ejecución y herramientas como:

```text
pytest
black
bandit
pip-audit
```

---

## Variables de entorno

Copia:

```text
backend/.env.example
```

como:

```text
backend/.env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

Configura las variables necesarias:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
OPENAI_API_KEY=your_openai_api_key
RAG_MODEL=your_model_name
JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Nunca subas el archivo `.env` al repositorio.

El `.gitignore` del proyecto lo excluye automáticamente.

---

## Configuración de PostgreSQL

DevPilot AI necesita PostgreSQL con la extensión `pgvector`.

En PostgreSQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Puedes comprobarla mediante:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

La base de datos puede ejecutarse localmente o mediante un servicio PostgreSQL compatible con pgvector.

---

## Migraciones de base de datos

Con el entorno virtual activado:

```powershell
cd backend
python -m alembic upgrade head
```

Para comprobar la revisión actual:

```powershell
python -m alembic current
```

Alembic creará la estructura necesaria de base de datos.

---

## Arrancar el backend

Desde:

```text
backend/
```

ejecuta:

```powershell
python -m uvicorn app.main:app --reload
```

El backend estará disponible en:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

## Configuración del frontend

Desde la raíz del proyecto:

```powershell
cd frontend\devpilot-frontend
```

Comprueba Node.js:

```powershell
node --version
```

La versión recomendada es:

```text
v26.4.0
```

Comprueba npm:

```powershell
npm --version
```

Versión validada:

```text
11.17.0
```

Instala exactamente las dependencias definidas en `package-lock.json`:

```powershell
npm ci
```

Se recomienda utilizar `npm ci` en lugar de `npm install` para obtener una instalación reproducible.

---

## Arrancar el frontend

```powershell
npm start
```

La aplicación estará disponible normalmente en:

```text
http://localhost:4200
```

El frontend espera por defecto el backend de desarrollo en:

```text
http://127.0.0.1:8000
```

---

## Build del frontend

Para generar el build de producción:

```powershell
npm run build
```

La versión `v1.0.1` ha sido validada mediante una instalación limpia utilizando:

```text
npm ci
npm run build
```

con resultado correcto.

---

## Tests del backend

Instala primero las dependencias de desarrollo:

```powershell
cd backend
python -m pip install -r requirements-dev.txt
```

Ejecuta:

```powershell
python -m pytest
```

Resultado validado en `v1.0.1`:

```text
236 passed
```

También puedes ejecutar los tests en modo verbose:

```powershell
python -m pytest -v
```

---

## Tests del frontend

Desde:

```text
frontend/devpilot-frontend
```

ejecuta:

```powershell
npm test
```

Resultado validado:

```text
Test Files  13 passed
Tests       60 passed
```

Vitest utiliza modo watch durante desarrollo.

Pulsa:

```text
q
```

para finalizar.

---

## Validación de instalación limpia

La reproducibilidad de `v1.0.1` ha sido comprobada creando entornos completamente nuevos.

### Validación limpia del backend

Proceso utilizado:

```text
nuevo virtualenv
        ↓
requirements-dev.txt
        ↓
pip check
        ↓
pytest
```

Resultado:

```text
No broken requirements found.

236 tests passed
```

### Validación limpia del frontend

Proceso utilizado:

```text
eliminar node_modules
        ↓
npm ci
        ↓
npm run build
        ↓
npm test
```

Resultado:

```text
Build correcto
60 tests passed
0 vulnerabilities
```

---

## Flujo de uso

Una vez frontend y backend están funcionando:

```text
1. Registrar usuario
2. Iniciar sesión
3. Crear proyecto
4. Seleccionar ZIP o RAR
5. Subir archivo
6. Esperar indexación
7. Abrir chat
8. Realizar preguntas
9. Consultar fuentes recuperadas
10. Generar README o tests
```

---

## Ejemplo de consulta RAG

Una consulta típica podría ser:

```text
Explícame la arquitectura principal de este proyecto.
```

DevPilot AI realiza:

```text
Pregunta
   ↓
Embedding
   ↓
pgvector
   ↓
Top-K chunks
   ↓
Contexto
   ↓
LLM
   ↓
Respuesta + fuentes
```

---

## Generación de README

DevPilot AI puede analizar el código indexado y generar documentación técnica del proyecto.

El resultado puede:

- visualizarse;
- copiarse;
- descargarse.

La generación utiliza información recuperada del propio proyecto.

---

## Generación de tests

El usuario puede seleccionar un documento del proyecto y solicitar la generación de tests unitarios.

El sistema utiliza:

```text
archivo seleccionado
+
contexto relacionado
+
RAG
+
LLM
```

para generar una propuesta de tests.

En la versión actual los tests son generados, pero no se ejecutan automáticamente sobre el repositorio.

La ejecución automática y corrección iterativa forman parte de futuras evoluciones.

---

## Endpoints principales

### Autenticación

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Proyectos

```text
GET    /projects
POST   /projects
DELETE /projects/{project_id}
```

También existen operaciones para subida e indexación de proyectos.

### Conversaciones

```text
GET /conversations/...
```

### Chat RAG

```text
POST /chat/...
```

### Generación de README

```text
POST /readme/...
```

La especificación completa puede consultarse mediante Swagger:

```text
http://127.0.0.1:8000/docs
```

También está documentada en:

```text
docs/api.md
```

---

## Documentación adicional

El repositorio incluye:

```text
docs/
├── api.md
├── architecture.md
├── demo.md
└── setup.md
```

### Arquitectura detallada

```text
docs/architecture.md
```

Incluye:

- arquitectura frontend;
- arquitectura backend;
- RAG;
- autenticación;
- persistencia;
- seguridad;
- decisiones de diseño.

### Instalación detallada

```text
docs/setup.md
```

### API

```text
docs/api.md
```

### Demostración

```text
docs/demo.md
```

---

## Estructura del repositorio

```text
devpilot-ai/
│
├── .gitignore
├── .nvmrc
├── README.md
│
├── backend/
│   ├── .env.example
│   ├── alembic/
│   ├── app/
│   ├── tests/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── requirements-dev.txt
│
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── demo.md
│   └── setup.md
│
└── frontend/
    └── devpilot-frontend/
        ├── public/
        ├── src/
        ├── angular.json
        ├── package.json
        ├── package-lock.json
        └── tsconfig.json
```

---

## Limitaciones actuales

La versión actual presenta algunas limitaciones conocidas.

### Evaluación del RAG

La recuperación muestra las fuentes utilizadas, pero todavía no existe un benchmark automatizado que permita medir objetivamente:

- Hit Rate;
- Recall@K;
- MRR;
- fidelidad;
- relevancia;
- latencia;
- coste.

Esta es una de las principales líneas de evolución posteriores a la versión `v1.0.x`.

### Recuperación únicamente vectorial

La recuperación actual está basada principalmente en embeddings y búsqueda vectorial.

Está previsto investigar:

```text
Vector Search
vs
Hybrid Search
vs
Hybrid Search + Reranking
```

### Tests generados no ejecutados automáticamente

DevPilot AI genera tests, pero todavía no dispone de un ciclo automático:

```text
generar
→ ejecutar
→ capturar errores
→ corregir
→ reejecutar
```

Cualquier futura ejecución de código generado deberá realizarse en un entorno aislado y con aprobación humana.

### Indexación completa

Actualmente la importación está orientada principalmente a archivos ZIP/RAR.

Una futura integración con Git permitirá realizar indexación incremental a partir de los archivos modificados en cada commit.

---

## Roadmap

Las siguientes iteraciones previstas incluyen:

```text
v1.1
RAG Evaluation
├── dataset de evaluación
├── Hit@K
├── Recall@K
├── MRR
├── latencia
├── fidelidad
└── coste

v1.2
Hybrid Retrieval
├── Vector Search
├── PostgreSQL Full Text Search
└── Reciprocal Rank Fusion

v1.3
Reranking

v1.4
Executable Test Generation
├── generación
├── ejecución aislada
├── captura de errores
├── reparación
└── aprobación humana

v2.0
Git Integration
├── GitHub
├── GitLab
├── commit tracking
├── git diff
└── incremental indexing
```

---

## Estrategia de ramas

La rama estable es:

```text
master
```

El desarrollo continúa desde:

```text
develop
```

Las funcionalidades se desarrollan en ramas específicas:

```text
feature/*
fix/*
```

Ejemplo:

```text
master
│
├── v1.0.0
│
└── v1.0.1
     │
     └── develop
          │
          └── feature/rag-evaluation
```

---

## Versionado

DevPilot AI utiliza versionado semántico:

```text
MAJOR.MINOR.PATCH
```

Ejemplos:

```text
v1.0.0
Primera versión estable presentada como TFM.

v1.0.1
Mejoras de instalación y reproducibilidad.

v1.1.0
Próxima versión orientada a evaluación cuantitativa del RAG.
```

---

## Buenas prácticas para contribuir

Antes de crear un commit:

Backend:

```powershell
python -m pip check
python -m pytest
```

Frontend:

```powershell
npm run build
npm test
```

No deben incluirse:

```text
.env
.venv
.venv-test
node_modules
dist
storage
API keys
passwords
tokens
```

---

## Autor

**Samuel Ruiz de la Rosa**

Software Engineer / Frontend Developer

Proyecto desarrollado inicialmente como Trabajo Final de Máster y continuado como proyecto personal orientado a Inteligencia Artificial aplicada al desarrollo de software.

---

## Licencia

Actualmente el proyecto no define una licencia pública específica.

Si el repositorio va a utilizarse como proyecto open source, deberá añadirse una licencia explícita antes de permitir reutilización o distribución del código.