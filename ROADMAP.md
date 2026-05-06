# GFAT Worker Roadmap

Hoja de ruta viva para evolucionar `gfat-worker` sin romper su uso operativo. El objetivo no es reescribir el sistema, sino hacerlo mas reproducible, observable y facil de mantener en desarrollo local y en el servidor CPD.

## Estado Actual

`gfat-worker` es un servicio operativo para automatizar procesado LIDAR GFAT/ALHAMBRA. Usa:

- FastAPI para lanzar y consultar tareas.
- Celery para ejecutar tareas.
- Redis como broker y backend de resultados.
- `atmolidarpy` como distribucion Python, importada en codigo como `lidarpy`.
- Docker Compose para desarrollo, pruebas y despliegue.

Flujo funcional principal:

1. Leer datos RAW montados en `/mnt/RAW/UGR`.
2. Escribir productos en `/mnt/PRODUCTS/UGR`.
3. Convertir RAW/Licel a NetCDF 1a.
4. Generar quicklooks.
5. Convertir a formato SCC.
6. Subir, descargar y plotear productos SCC cuando proceda.

## Principios

- Mantener el flujo operativo antes de introducir refactors grandes.
- Separar codigo, configuracion, secretos y datos.
- No versionar credenciales ni rutas privadas reales.
- Usar cambios pequenos, probables y reversibles.
- Automatizar pruebas rapidas en cada push a `main`.
- Reservar pruebas pesadas con datos reales para validaciones manuales o releases.

## Prioridad 1 - Seguridad e Higiene

Objetivo: que el repositorio pueda compartirse y desplegarse sin exponer secretos.

### Pendiente

- [ ] Revisar `MANUAL.md` y retirar cualquier credencial real.
- [ ] Rotar credenciales si alguna credencial versionada ha sido valida.
- [ ] Confirmar que no hay secretos en el historial antes de difundir el repositorio.
- [ ] Documentar permisos minimos necesarios para RAW, PRODUCTS y SCC.
- [ ] Revisar si `.vscode/settings.json` debe versionarse o moverse a documentacion local.

### Hecho

- [x] `.gitignore` cubre `.env`, `.env.*`, `info_scc_user.yml`, datos locales y temporales.
- [x] `.env.example` queda versionado sin secretos.
- [x] `DEPLOY.md` documenta que `info_scc_user.yml` vive fuera de Git.

## Prioridad 2 - Despliegue CPD

Objetivo: poder actualizar y recrear el servicio en el servidor del CPD de forma limpia.

### Hecho

- [x] `compose.prod.yml` para produccion.
- [x] `api`, `worker` y `redis` separados en produccion.
- [x] Redis con volumen persistente.
- [x] `restart: unless-stopped` en servicios de produccion.
- [x] RAW montado como solo lectura.
- [x] PRODUCTS montado con escritura.
- [x] `info_scc_user.yml` montado como fichero externo de solo lectura.
- [x] Flower queda en perfil opcional `ops` y bindeado a `127.0.0.1` por defecto.
- [x] `scripts/deploy.sh` actualiza desde GitHub, reconstruye contenedores y hace rollback basico si la API no levanta.
- [x] `DEPLOY.md` documenta instalacion inicial, configuracion, actualizacion, logs, parada, Flower y rollback.

### Pendiente

- [ ] Probar `scripts/deploy.sh` en un servidor Linux real.
- [ ] Decidir si el despliegue CPD usara imagen construida localmente o imagen publicada en GitHub Container Registry.
- [ ] Anadir `GET /health` para healthcheck semantico mas claro que `GET /`.
- [ ] Anadir `GET /version` con commit/version y backend LIDAR, sin datos sensibles.
- [ ] Documentar un procedimiento de backup/limpieza para el volumen Redis si crece demasiado.

## Prioridad 3 - Estabilidad de Agenda Celery

Objetivo: evitar fallos silenciosos en tareas programadas.

### Pendiente

- [ ] Sustituir cualquier calculo manual de ayer por `date.today() - timedelta(days=1)`.
- [ ] Eliminar o prevenir claves duplicadas en `worker/scheduled/lidar.py`.
- [ ] Dar nombres unicos y descriptivos a cada tarea programada.
- [ ] Corregir argumentos de tareas programadas para que coincidan con sus firmas reales.
- [ ] Validar todas las entradas de `beat_schedule` al arrancar.
- [ ] Documentar la agenda efectiva en una tabla legible.

### Riesgos

- Las claves duplicadas en un diccionario Python se pisan silenciosamente.
- Una tarea programada con argumentos desplazados puede fallar horas despues del despliegue.

## Prioridad 4 - Robustez LIDAR/SCC

Objetivo: que las tareas fallen de forma explicita, trazable y recuperable.

### Hecho

- [x] Runtime migrado a Python 3.11.
- [x] `atmolidarpy==0.1.0` instalado en la imagen del worker.
- [x] El codigo importa `lidarpy`.
- [x] Retirada la dependencia runtime de `gfatpy`.
- [x] `worker/lidar_backend.py` centraliza imports LIDAR y error explicito si falta `atmolidarpy`.
- [x] Validada conversion SCC real con fixtures de `atmolidarpy`: ALHAMBRA `2023-08-30`, SCC `781`, intervalo `03:15-03:45`, salida `20230830gra0315.nc`.

### Pendiente

- [ ] Dividir `worker/tasks/lidar.py` en modulos mas pequenos:
  - conversion NetCDF
  - quicklooks
  - conversion SCC
  - transferencia SCC
  - plotting SCC
  - utilidades comunes
- [ ] Extraer funciones internas anidadas para probarlas directamente.
- [ ] Validar entradas de tareas con modelos o funciones dedicadas:
  - `lidar_name`
  - `target_date`
  - `scc_id`
  - intervalos horarios
  - canales quicklook
- [ ] Revisar manejo de `measurements` cuando no existe el directorio de datos.
- [ ] Corregir validacion de `minus45_files` en conversion SCC depolarization.
- [ ] Hacer que cada tarea devuelva una estructura consistente:
  - estado
  - mensaje
  - ficheros creados
  - ficheros omitidos
  - errores recuperables
- [ ] Asegurar limpieza de temporales en bloques `finally` cuando se extraen ZIPs.

### Riesgos

- `worker/tasks/lidar.py` concentra demasiadas responsabilidades.
- Los resultados de tareas aun mezclan strings, listas y mensajes libres.
- Algunas ramas de error pueden dejar estados parciales o temporales sin limpiar.

## Prioridad 5 - Observabilidad y Operacion

Objetivo: saber que paso, cuando paso y que accion tomar.

### Pendiente

- [ ] Definir formato de logs uniforme con:
  - task id Celery
  - task name
  - lidar
  - fecha objetivo
  - SCC id
  - fichero procesado
- [ ] Anadir `GET /health`.
- [ ] Anadir `GET /version`.
- [ ] Documentar uso operativo de Flower.
- [ ] Definir politica de reintentos por tipo de tarea:
  - conversion local
  - subida SCC
  - descarga SCC
- [ ] Anadir timeouts configurables para operaciones de red SCC.
- [ ] Guardar resumen diario de ejecucion en producto o log persistente.
- [ ] Evaluar alertas por email o webhook para tareas criticas fallidas.

## Prioridad 6 - API de Operacion

Objetivo: que lanzar tareas manuales sea seguro para operadores.

### Hecho

- [x] `TaskQueueInput` conserva enteros y estructuras en `args`/`kwargs`.
- [x] `TaskQueueDetailsResponse` acepta resultados estructurados.
- [x] La API serializa excepciones de Celery como JSON.

### Pendiente

- [ ] Crear endpoints especificos para tareas frecuentes:
  - `POST /lidar/nc-convert`
  - `POST /lidar/quicklook`
  - `POST /lidar/scc/convert`
  - `POST /lidar/scc/send`
  - `POST /lidar/scc/download`
  - `POST /lidar/scc/plot`
- [ ] Mantener `/task_queue` como endpoint generico para administracion avanzada.
- [ ] Mejorar respuesta de consulta de tarea:
  - fecha de creacion
  - fecha de inicio
  - fecha de fin
  - traceback resumido si falla
- [ ] Anadir ejemplos `curl` y JSON en `README.md`.
- [ ] Crear una pequena coleccion de requests de ejemplo para operacion diaria.

## Prioridad 7 - Pruebas y CI

Objetivo: detectar roturas antes de desplegar.

### Hecho

- [x] Tests configurados con `uv` y `pyproject.toml`.
- [x] Tests rapidos de imports, modelos API, tareas registradas, agenda, fechas e intervalos.
- [x] `docker-compose.test.yml` para integracion API + Redis + Celery.
- [x] `scripts/smoke_docker.ps1` para smoke local en Windows.
- [x] GitHub Actions en cada push a `main` y pull request.
- [x] CI ejecuta `uv run pytest -q`.
- [x] CI construye Docker y comprueba API, Celery y backend `lidarpy`.

### Pendiente

- [ ] Anadir pruebas con filesystem temporal para rutas de salida.
- [ ] Anadir pruebas unitarias para errores de tareas LIDAR sin tocar NAS.
- [ ] Anadir mocks/fixtures para SCC sin subir ni descargar datos reales.
- [ ] Anadir lint/format con `ruff`.
- [ ] Evaluar `mypy` o `pyright` sin bloquear el flujo operativo.
- [ ] Documentar una validacion manual de release con datos reales.

### Validaciones Pesadas

No deben ejecutarse en cada commit.

- [ ] Definir un caso real ALHAMBRA de referencia con fecha concreta.
- [ ] Ejecutar conversion NetCDF real.
- [ ] Ejecutar quicklook real.
- [x] Ejecutar conversion SCC real para intervalo controlado.
- [ ] Subir a SCC solo en entorno autorizado.
- [ ] Descargar productos SCC.
- [ ] Plotear productos SCC.
- [ ] Comparar productos generados con referencia conocida.

## Prioridad 8 - Evolucion Funcional

Ideas para crecer sin romper el nucleo operativo.

- [ ] Soportar multiples lidares mediante configuracion externa.
- [ ] Separar agenda por instrumento o estacion.
- [ ] Permitir activar/desactivar tareas programadas por entorno.
- [ ] Crear perfiles de SCC por sistema/configuracion.
- [ ] Anadir dry-run para validar inputs antes de lanzar conversiones largas.
- [ ] Generar reporte diario automatico de productos creados.
- [ ] Evaluar persistencia de metadatos de ejecucion en una base de datos ligera si Redis no es suficiente.

## Backlog Tecnico

- [ ] Revisar nombres de variables de entorno en `docker-compose.yml` y documentarlos de forma consistente.
- [ ] Revisar imports no usados en `worker/tasks/lidar.py`.
- [ ] Centralizar constantes como `ALHAMBRA`, canales y SCC IDs.
- [ ] Evitar strings magicos para patrones de fichero.
- [ ] Normalizar mayusculas/minusculas de `ALHAMBRA` vs `alhambra`.
- [ ] Anadir `README` de arquitectura con diagrama simple del flujo.
- [ ] Crear script de diagnostico local para comprobar mounts, Redis, SCC config y tareas registradas.

## Registro de Decisiones

### 2026-05-04

- Se crea este roadmap como documento vivo.
- Se prioriza estabilizar el sistema operativo existente antes de refactors amplios.
- La primera linea de trabajo es agenda Celery, secretos y configuracion.

### 2026-05-06

- `gfat-worker` deja de depender de `gfatpy` en runtime.
- La dependencia LIDAR runtime es `atmolidarpy`; el codigo importa `lidarpy`.
- Produccion usa `compose.prod.yml`; desarrollo y test conservan sus compose propios.
- En produccion no se monta codigo como volumen, solo configuracion y datos.
- Flower es opcional y no queda expuesto publicamente por defecto.
