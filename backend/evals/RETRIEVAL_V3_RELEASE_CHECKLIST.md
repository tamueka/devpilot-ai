# Retrieval v3 / v1.2.0 Release Checklist

## 1. Código

- [x] Diagnóstico de fallos de Retrieval v2 completado.
- [x] Path Retrieval mejorado.
- [x] Tests de regresión añadidos.
- [x] `candidate_k = 20` definido para Retrieval v3.
- [x] Best-Rank mantenido como estrategia de fusión.
- [x] Retrieval v3 separado conceptualmente de Retrieval v2.

## 2. Metodología

- [x] Dataset antiguo reclasificado como datos de desarrollo.
- [x] Nuevo benchmark independiente creado.
- [x] Tres repositorios nuevos seleccionados.
- [x] Commits Git congelados.
- [x] 30 preguntas congeladas.
- [x] Expected files verificados.
- [x] Manifest SHA-256 generado.
- [x] Runner independiente preparado.

## 3. Antes de evaluación independiente

- [ ] API con créditos disponibles.
- [ ] Ejecutar tests de evaluaciones.
- [ ] Ejecutar evaluación de desarrollo Retrieval v3.
- [ ] Guardar resultados de desarrollo.
- [ ] Confirmar configuración definitiva.
- [ ] Ejecutar suite completa backend.
- [ ] Verificar integridad del benchmark independiente.
- [ ] Indexar HTTPX.
- [ ] Indexar Vue Router.
- [ ] Indexar FastAPI.
- [ ] Configurar project IDs locales.
- [ ] Preflight independiente correcto.

## 4. Validación independiente

- [ ] Ejecutar una sola vez el benchmark congelado.
- [ ] Guardar salida original sin modificarla.
- [ ] Registrar métricas globales.
- [ ] Registrar métricas por repositorio.
- [ ] Registrar fallos.
- [ ] No realizar tuning sobre esos resultados.

## 5. Calidad final

- [ ] Backend completo verde.
- [ ] Frontend completo verde.
- [ ] Build frontend correcto.
- [ ] `git diff --check` correcto.
- [ ] Working tree limpio.

## 6. Documentación

- [ ] Añadir resultados finales a `docs/retrieval-v3.md`.
- [ ] Actualizar README principal si procede.
- [ ] Preparar release notes de v1.2.0.
- [ ] Documentar limitaciones.

## 7. Release

- [ ] Merge `feature/rag-retrieval-v3` → `develop`.
- [ ] Verificar `develop`.
- [ ] Merge `develop` → `master`.
- [ ] Crear tag `v1.2.0`.
- [ ] Push del tag.
- [ ] Crear GitHub Release `v1.2.0`.