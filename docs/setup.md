# Instalación y puesta en marcha de DevPilot AI

## Introducción

Este documento describe cómo preparar el entorno local de DevPilot AI desde
cero.

La solución está compuesta por:

```text
Frontend
Angular

Backend
FastAPI

Base de datos
PostgreSQL + pgvector

Servicios de IA
OpenAI API
```

La estructura general esperada es:

```text
devpilot-ai/
│
├── backend/
├── docs/
└── frontend/
    └── devpilot-frontend/
```

## Requisitos previos

Antes de comenzar es necesario disponer de las siguientes herramientas.

### Git

Comprobar instalación:

```powershell
git --version
```

### Node.js

Comprobar instalación:

```powershell
node --version
```

También debe estar disponible npm:

```powershell
npm --version
```

### Python

DevPilot AI utiliza Python 3.13.

Comprobar:

```powershell
python --version
```

### PostgreSQL

Debe existir una instalación local de PostgreSQL.

Comprobar:

```powershell
psql --version
```

### pgvector

La instancia PostgreSQL debe disponer de la extensión `vector`.

### 7-Zip

En Windows se recomienda 7-Zip para facilitar el procesamiento de archivos RAR.

Instalación mediante `winget`:

```powershell
winget install --id 7zip.7zip -e
```

La instalación habitual es:

```text
C:\Program Files\7-Zip\7z.exe
```

## Clonar el repositorio

Ejecutar:

```powershell
git clone <URL_DEL_REPOSITORIO>
```

Entrar en el proyecto:

```powershell
cd devpilot-ai
```

## Configuración del backend

Acceder al directorio:

```powershell
cd backend
```

### Crear el entorno virtual

```powershell
python -m venv .venv
```

### Activar el entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Una vez activado debería aparecer algo similar a:

```text
(.venv) PS C:\...\devpilot-ai\backend>
```

### Actualizar pip

```powershell
python -m pip install --upgrade pip
```

### Instalar dependencias

```powershell
pip install -r requirements.txt
```

## Configuración de PostgreSQL

Crear la base de datos que utilizará DevPilot AI.

Ejemplo:

```sql
CREATE DATABASE devpilot;
```

Conectarse a la base de datos:

```sql
\c devpilot
```

Activar pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verificar la extensión:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

El resultado debería incluir:

```text
vector
```

## Variables de entorno del backend

Dentro de:

```text
backend/
```

debe existir:

```text
.env.example
```

Crear una copia:

```powershell
Copy-Item .env.example .env
```

Configurar los valores reales únicamente en `.env`.

Ejemplo de estructura:

```env
DATABASE_URL=
OPENAI_API_KEY=
RAG_MODEL=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## DATABASE_URL

El formato utilizado con Psycopg es:

```text
postgresql+psycopg://usuario:password@host:puerto/base_de_datos
```

Ejemplo local:

```env
DATABASE_URL=postgresql+psycopg://devpilot_user:password@localhost:5432/devpilot
```

Las credenciales deben adaptarse a la configuración local de PostgreSQL.

## OPENAI_API_KEY

Debe configurarse una clave válida para acceder a los servicios utilizados por
DevPilot AI.

```env
OPENAI_API_KEY=<clave>
```

La clave nunca debe añadirse al repositorio.

## RAG_MODEL

Configura el modelo de generación utilizado por el backend.

```env
RAG_MODEL=<modelo>
```

El modelo puede cambiar sin necesidad de modificar la lógica principal de la
aplicación.

## Configuración JWT

La autenticación utiliza JWT.

Ejemplo:

```env
JWT_SECRET_KEY=<secreto_seguro>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

El secreto debe ser suficientemente largo y aleatorio.

No debe reutilizarse el valor mostrado en `.env.example`.

## Migraciones de base de datos

Con el entorno virtual activo y desde `backend`:

```powershell
alembic upgrade head
```

Esto aplica todas las migraciones pendientes.

Para consultar el estado:

```powershell
alembic current
```

Para consultar el historial:

```powershell
alembic history
```

## Iniciar el backend

Desde:

```text
devpilot-ai/backend
```

ejecutar:

```powershell
uvicorn app.main:app --reload
```

La API debería quedar disponible en:

```text
http://127.0.0.1:8000
```

## Swagger

FastAPI expone documentación interactiva.

Abrir:

```text
http://127.0.0.1:8000/docs
```

También puede utilizarse:

```text
http://127.0.0.1:8000/redoc
```

## Verificar el backend

Antes de continuar puede comprobarse que el código Python compila:

```powershell
python -m compileall app
```

También puede ejecutarse la suite completa:

```powershell
python -m pytest -v
```

## Configuración del frontend

Abrir otra terminal.

Desde la raíz del repositorio:

```powershell
cd frontend\devpilot-frontend
```

## Instalar dependencias del frontend

```powershell
npm install
```

## Iniciar Angular

Ejecutar:

```powershell
npm start
```

o, si se desea utilizar directamente Angular CLI:

```powershell
npx ng serve
```

La aplicación debería estar disponible en:

```text
http://localhost:4200
```

## Comunicación frontend-backend

Durante desarrollo, el frontend utiliza la API disponible en:

```text
http://127.0.0.1:8000
```

La configuración debe mantenerse en los archivos de entorno de Angular.

Ejemplo conceptual:

```typescript
export const environment = {
    production: false,
    apiUrl: 'http://127.0.0.1:8000',
};
```

## CORS

El backend debe aceptar el origen del frontend de desarrollo:

```text
http://localhost:4200
```

DevPilot AI mantiene CORS restringido a los orígenes configurados.

No se recomienda utilizar:

```text
*
```

en producción.

## Verificar el frontend

Ejecutar la suite:

```powershell
npm run test -- --watch=false
```

Verificar el build:

```powershell
npm run build
```

## Arranque completo

El flujo habitual de trabajo requiere dos terminales.

### Terminal del backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Terminal del frontend

```powershell
cd frontend\devpilot-frontend
npm start
```

Después abrir:

```text
http://localhost:4200
```

## Primer uso

Una vez iniciados frontend y backend:

1. Abrir la aplicación.
2. Registrar un usuario.
3. Iniciar sesión.
4. Crear un proyecto.
5. Subir un archivo ZIP o RAR.
6. Esperar a que el proyecto quede indexado.
7. Abrir el chat.
8. Realizar una consulta sobre el código.
9. Generar un README.
10. Generar tests unitarios.

## Importación de proyectos

Los archivos soportados son:

```text
.zip
.rar
```

El proyecto comprimido puede contener código fuente en extensiones como:

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

## Archivos que no deben subirse al repositorio

La siguiente información debe permanecer fuera de Git:

```text
.env
API keys
JWT secrets
Passwords
Private keys
Archivos generados localmente
Entornos virtuales
Storage de proyectos importados
```

## Comprobar .gitignore

Desde la raíz:

```powershell
git status
```

Para verificar específicamente que `.env` está ignorado:

```powershell
git check-ignore -v backend/.env
```

Debe aparecer una regla de `.gitignore`.

## Problemas frecuentes

### PowerShell no permite activar el entorno virtual

Puede aparecer un error relacionado con la política de ejecución.

Para la sesión actual puede utilizarse:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después:

```powershell
.\.venv\Scripts\Activate.ps1
```

### PostgreSQL no conecta

Revisar:

```text
Host
Puerto
Usuario
Contraseña
Base de datos
```

También comprobar:

```powershell
psql --version
```

y que el servicio PostgreSQL está iniciado.

### pgvector no está disponible

Comprobar:

```sql
SELECT *
FROM pg_available_extensions
WHERE name = 'vector';
```

Si no aparece, debe instalarse pgvector para la versión de PostgreSQL
utilizada.

### Error al procesar RAR

Comprobar la instalación de 7-Zip.

Ruta habitual:

```text
C:\Program Files\7-Zip\7z.exe
```

También puede comprobarse:

```powershell
Get-Command 7z -ErrorAction SilentlyContinue
```

### El frontend no puede acceder al backend

Comprobar que FastAPI está iniciado en:

```text
http://127.0.0.1:8000
```

y Angular en:

```text
http://localhost:4200
```

También debe comprobarse la configuración CORS del backend.

### Error 401

Puede significar:

```text
Token ausente
Token expirado
Token inválido
Sesión cerrada
```

Volver a iniciar sesión suele generar un nuevo token.

### La subida de proyecto falla

Comprobar:

```text
Formato ZIP o RAR
Tamaño del archivo
Contenido del archivo
Entradas inseguras
Symlinks
Archivos excesivamente grandes
```

El backend rechaza archivos comprimidos que incumplen sus políticas de
seguridad.

## Ejecución de tests antes de entregar

### Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m compileall app
python -m pytest -v
```

### Frontend

```powershell
cd frontend\devpilot-frontend
npm run test -- --watch=false
npm run build
```

Ambos bloques deben finalizar correctamente antes de considerar una versión
lista para entregar.

## Checklist de entorno

Antes de probar la aplicación comprobar:

```text
[ ] PostgreSQL iniciado
[ ] Base de datos creada
[ ] pgvector habilitado
[ ] backend/.env creado
[ ] DATABASE_URL configurada
[ ] OPENAI_API_KEY configurada
[ ] JWT_SECRET_KEY configurada
[ ] entorno virtual activado
[ ] dependencias Python instaladas
[ ] migraciones aplicadas
[ ] FastAPI iniciado
[ ] dependencias Angular instaladas
[ ] Angular iniciado
```

## Checklist de validación final

```text
[ ] Registro funciona
[ ] Login funciona
[ ] Restauración de sesión funciona
[ ] Creación de proyecto funciona
[ ] ZIP funciona
[ ] RAR funciona
[ ] Reindexación funciona
[ ] Chat RAG funciona
[ ] Fuentes del chat aparecen
[ ] README IA funciona
[ ] Generación de tests funciona
[ ] Eliminación de proyecto funciona
[ ] Backend tests pasan
[ ] Frontend tests pasan
[ ] Angular build pasa
[ ] Python compileall pasa
```

## Entorno de desarrollo recomendado

La aplicación ha sido desarrollada principalmente en Windows utilizando:

```text
Windows 11
Visual Studio Code
PowerShell
Python virtual environments
Node.js / npm
PostgreSQL
```

No obstante, tanto Angular como FastAPI pueden ejecutarse también en sistemas
Linux o macOS realizando los ajustes correspondientes en comandos y rutas.

## Resultado esperado

Después de completar correctamente esta guía deben estar disponibles:

```text
Frontend
http://localhost:4200

Backend
http://127.0.0.1:8000

Swagger
http://127.0.0.1:8000/docs

PostgreSQL
localhost:5432
```

Con este entorno, DevPilot AI queda preparado para crear proyectos, indexar
repositorios y utilizar las funcionalidades RAG de la aplicación.
