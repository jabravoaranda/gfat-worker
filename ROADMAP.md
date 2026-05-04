# GFAT Worker Roadmap

Este documento es una hoja de ruta viva para evolucionar `gfat-worker` manteniendo su uso operativo actual. No parte de la idea de reescribir el sistema, sino de reducir riesgos, hacer el servicio mas observable y facilitar cambios futuros sin interrumpir el pipeline diario.

## Estado Actual

`gfat-worker` es un servicio operativo para automatizar el procesado LIDAR GFAT/ALHAMBRA. Ejecuta tareas Celery sobre Redis, expone una API FastAPI para lanzar y consultar tareas, y usa Flower para inspeccion operativa.

Flujo principal:

1. Montar datos NAS en `/mnt/RAW` y `/mnt/PRODUCTS`.
2. Convertir medidas LIDAR raw/licel a NetCDF 1a.
3. Generar quicklooks.
4. Convertir medidas a formato SCC.
5. Subir ficheros SCC.
6. Descargar productos SCC.
7. Plotear resultados SCC.

La prioridad de desarrollo debe ser preservar este flujo y mejorar su fiabilidad por capas.

## Principios de Desarrollo

- Mantener compatibilidad con el despliegue actual antes de introducir cambios estructurales.
- Priorizar fallos que puedan detener tareas programadas o producir resultados silenciosamente incorrectos.
- Separar configuracion, secretos, agenda y logica de procesado.
- Hacer cambios pequenos, verificables y con rollback sencillo.
- Documentar cada cambio operativo en este fichero.

## Prioridad 0 - Higiene Operativa Inmediata

Estas acciones reducen riesgo sin cambiar el comportamiento funcional previsto.

### TODO

- [ ] Retirar credenciales reales de `MANUAL.md`.
- [ ] Rotar credenciales si las de `MANUAL.md` son validas o lo han sido.
- [ ] Crear `env.example` con variables requeridas sin valores secretos.
- [ ] Documentar en `README.md` las variables necesarias:
  - `BROKER_URL`
  - `NAS_URL_RAW_DIR`
  - `NAS_URL_PRODUCTS_DIR`
  - credenciales SCC mediante fichero no versionado
- [ ] Confirmar que `.gitignore` cubre todos los secretos locales:
  - `.env`
  - `.env.*`
  - `info_scc_user.yml`
  - rutas locales de datos
- [ ] Revisar si `.vscode/settings.json` debe versionarse o moverse a documentacion local.

### Riesgos Detectados

- `MANUAL.md` contiene usuario y password NAS en claro.
- El repositorio esta sin commits iniciales; antes de publicar o compartir, conviene limpiar secretos y consolidar una primera version segura.

## Prioridad 1 - Estabilidad de Tareas Programadas

Estas acciones atacan fallos que pueden afectar directamente a la operacion automatica.

### TODO

- [ ] Sustituir el calculo de `yesterday` por `date.today() - timedelta(days=1)`.
- [ ] Eliminar claves duplicadas en `worker/scheduled/lidar.py`.
- [ ] Dar nombres unicos y descriptivos a cada tarea programada.
- [ ] Corregir argumentos de tareas programadas para que coincidan con sus firmas reales.
- [ ] Validar todas las entradas de `beat_schedule` al arrancar.
- [ ] Crear una prueba automatica que importe `all_scheduled` y verifique:
  - que no hay nombres duplicados antes de construir el diccionario final
  - que cada tarea existe
  - que cada `args` es compatible con la firma de la tarea
- [ ] Documentar la agenda efectiva en una tabla legible.

### Riesgos Detectados

- `date.today().replace(day=date.today().day - 1)` falla el dia 1 de cada mes.
- Las claves duplicadas en un diccionario Python se pisan silenciosamente.
- Algunas entradas programadas parecen pasar argumentos incompletos o desplazados, especialmente en tareas de descarga SCC.

## Prioridad 2 - Configuracion y Despliegue

Objetivo: que el contenedor sea reproducible y configurable sin editar codigo.

### TODO

- [ ] Mover rutas hardcodeadas a variables de entorno:
  - `RAW_DIR`
  - `PRODUCTS_DIR`
  - `GFATPY_DIR` si realmente debe sobreescribirse
  - ruta de `info_scc_user.yml`
- [ ] Evitar depender de rutas absolutas de `site-packages` cuando se pueda importar desde `gfatpy`.
- [ ] Fijar versiones de dependencias directas y revisar dependencias transitivas criticas.
- [ ] Decidir si `gfatpy==0.14.13` debe estar en `requirements.txt` o solo en `Dockerfile`, pero no duplicar criterios.
- [ ] Anadir `healthcheck` a `docker-compose.yml` para:
  - API FastAPI
  - Redis
  - worker Celery
- [ ] Separar procesos en contenedores distintos o documentar por que `worker -B` y API viven juntos.
- [ ] Crear comandos operativos claros:
  - build
  - up
  - logs
  - entrar en worker
  - lanzar tarea manual

### Riesgos Detectados

- `start.sh` lanza Celery en background y Uvicorn en foreground. Si Celery muere, el contenedor puede seguir vivo por la API.
- La ruta de `gfatpy` esta acoplada a Python 3.10 y al layout interno del contenedor.

## Prioridad 3 - Robustez de Tareas LIDAR

Objetivo: que los errores sean explicitos, trazables y no dejen estados parciales confusos.

### TODO

- [ ] Migrar dependencias LIDAR desde `gfatpy.lidar` a `lidarpy` cuando `lidarpy` tenga una release estable en PyPI.
- [ ] Dividir `worker/tasks/lidar.py` en modulos mas pequenos:
  - conversion NetCDF
  - quicklooks
  - conversion SCC
  - transferencia SCC
  - plotting SCC
  - utilidades comunes
- [ ] Extraer funciones internas anidadas para que puedan probarse directamente.
- [ ] Validar entradas de tareas con modelos Pydantic o funciones de validacion:
  - `lidar_name`
  - `target_date`
  - `scc_id`
  - intervalos horarios
  - canales quicklook
- [ ] Normalizar tipos: evitar depender de que Celery reciba numeros como strings.
- [ ] Revisar manejo de `measurements` cuando no se encuentra ningun directorio.
- [ ] Corregir validacion de `minus45_files` en conversion depolarization SCC.
- [ ] Hacer que cada tarea devuelva una estructura consistente:
  - estado
  - mensaje
  - ficheros creados
  - ficheros omitidos
  - errores recuperables
- [ ] Asegurar limpieza de temporales en bloques `finally` cuando se extraen ZIPs.

### Riesgos Detectados

- Algunas ramas pueden dejar variables sin definir si no se encuentran datos.
- Hay funciones grandes con varias responsabilidades, lo que dificulta probar y razonar sobre fallos.
- Los resultados devueltos alternan entre `str`, `list[str]` y mensajes de error libres.

## Prioridad 3.1 - Migracion de `gfatpy` a `lidarpy`

Objetivo: desacoplar `gfat-worker` del antiguo submodulo `gfatpy.lidar` y consumir una dependencia LIDAR versionada y publica.

### Contexto

El repositorio local `C:\Users\Fizico\Documents\github\lidarpy` corresponde a `jabravoaranda/lidarpy`. Su `README.md` indica que `lidarpy` es un paquete standalone migrado desde `gfatpy.lidar`. El paquete ya tiene estructura `src/lidarpy`, `pyproject.toml`, tests, documentacion y workflow de publicacion PyPI mediante Trusted Publishing.

El nombre de distribucion previsto en PyPI es `atmolidarpy`, mientras que el paquete Python se importara como `lidarpy`. En `gfat-worker`, esto significa que `requirements.txt` debe depender de `atmolidarpy==...`, pero el codigo debe usar imports `lidarpy.*`.

### Mapeo Inicial de Imports

Imports actuales en `gfat-worker` que ya tienen equivalente aparente en `lidarpy`:

- `gfatpy.lidar.utils.types.LidarName` -> `lidarpy.utils.types.LidarName`
- `gfatpy.lidar.utils.utils.LIDAR_INFO` -> `lidarpy.utils.utils.LIDAR_INFO`
- `gfatpy.lidar.utils.utils.licel_to_datetime` -> `lidarpy.utils.utils.licel_to_datetime`
- `gfatpy.lidar.nc_convert.measurement.to_measurements` -> `lidarpy.nc_convert.measurement.to_measurements`
- `gfatpy.lidar.plot.quicklook.quicklook_from_file` -> `lidarpy.plot.quicklook.quicklook_from_file`
- `gfatpy.utils.io.find_nearest_filepath` -> `lidarpy.general_utils.io.find_nearest_filepath`
- `gfatpy.utils.io.read_yaml` -> `lidarpy.general_utils.io.read_yaml`

Imports actuales que requieren decision antes de migrar:

- `gfatpy.GFATPY_DIR`
- `gfatpy.lidar.scc.scc_access`
- `gfatpy.lidar.scc.plot.scc_zip.SCC_zipfile`
- `gfatpy.lidar.scc.transfer.check_measurement_id_in_scc`
- `gfatpy.lidar.scc.licel2scc.licel2scc`
- `gfatpy.lidar.scc.licel2scc.licel2scc_depol`

En la inspeccion inicial de `lidarpy` no se ha visto un paquete `lidarpy.scc`. Por tanto, la migracion puede hacerse en dos fases: primero `nc_convert` y `quicklook`; despues SCC, cuando esa parte este migrada o se decida mantener temporalmente en otra dependencia.

### Plan de Migracion

- [ ] Publicar o instalar `atmolidarpy` desde GitHub en entorno de pruebas antes de tocar produccion.
- [ ] Anadir `atmolidarpy` como dependencia en el worker:
  - desarrollo: `lidarpy @ git+ssh://git@github.com/jabravoaranda/lidarpy.git@develop`
  - produccion: `atmolidarpy==0.1.x` cuando este publicado en PyPI
- [ ] Subir el contenedor base de `gfat-worker` a Python 3.11 si `lidarpy` mantiene `requires-python = ">=3.11.11,<3.12"`.
- [ ] Migrar primero `task_nc_convert` y `task_quicklook`.
- [ ] Crear tests o scripts de verificacion con una fecha ALHAMBRA controlada para comparar outputs `gfatpy` vs `lidarpy`.
- [ ] Mantener temporalmente los imports SCC desde `gfatpy` si `lidarpy` no incluye todavia SCC.
- [x] Extraer una capa adaptadora `worker/lidar_backend.py` para concentrar imports y evitar cambios dispersos en tareas Celery.
- [ ] Una vez validado, retirar imports directos `gfatpy.lidar.*` del worker.
- [ ] Eliminar rutas hardcodeadas a `/usr/local/lib/python3.10/site-packages/gfatpy`.

### Preparacion de `lidarpy` para PyPI

- [ ] Confirmar que `pyproject.toml` usa `name = "atmolidarpy"` y mantiene `packages = ["src/lidarpy"]`.
- [ ] Confirmar que instalar `atmolidarpy` permite `import lidarpy`.
- [ ] Ejecutar tests de `lidarpy` en limpio antes de publicar.
- [ ] Ejecutar build y `twine check`.
- [ ] Confirmar que el wheel incluye datos runtime:
  - `lidarpy/info/*.yml`
  - `lidarpy/plot/info.yml`
  - `lidarpy/nc_convert/configs/*.toml`
  - assets necesarios
- [ ] Confirmar que el sdist/wheel no incluyen fixtures RAW grandes, caches, temporales ni documentos internos.
- [ ] Revisar versionado: publicar `0.1.0` solo si la API de `nc_convert` y `quicklook` se considera usable por `gfat-worker`.
- [ ] Definir politica de compatibilidad:
  - cambios bugfix: `0.1.x`
  - cambios de API: `0.2.0` mientras este en fase alpha
  - API estable para worker: objetivo `1.0.0`

### Criterios de Aceptacion

- `gfat-worker` puede construir una imagen Docker con `atmolidarpy` instalado e importar `lidarpy`.
- La tarea `tasks.lidar.task_nc_convert` genera los mismos productos esperados para una fecha de prueba.
- La tarea `tasks.lidar.task_quicklook` genera quicklook compatible para ALHAMBRA.
- La parte SCC sigue funcionando igual que antes o queda explicitamente marcada como dependencia temporal de `gfatpy`.
- El despliegue productivo puede fijar una version concreta de `lidarpy`.

## Prioridad 4 - Observabilidad y Operacion

Objetivo: saber que paso, cuando paso y que accion tomar.

### TODO

- [ ] Definir formato de logs uniforme con:
  - task id Celery
  - task name
  - lidar
  - fecha objetivo
  - scc id
  - fichero procesado
- [ ] Anadir endpoint API de salud: `GET /health`.
- [ ] Anadir endpoint API de version/configuracion no sensible: `GET /version`.
- [ ] Documentar uso de Flower en README.
- [ ] Definir politica de reintentos por tipo de tarea:
  - conversion local
  - subida SCC
  - descarga SCC
- [ ] Anadir timeouts configurables para operaciones de red SCC.
- [ ] Guardar resumen de ejecucion diario en producto o log persistente.
- [ ] Evaluar alertas por email o webhook cuando una tarea critica falla repetidamente.

### Indicadores Recomendados

- Numero de tareas ejecutadas por dia.
- Tareas fallidas por tipo.
- Tiempo medio de conversion NetCDF.
- Tiempo medio de procesamiento SCC.
- Numero de ficheros SCC subidos, descargados y ploteados.
- Ultima fecha con quicklook generado correctamente.

## Prioridad 5 - API y Experiencia de Usuario Tecnico

Objetivo: que lanzar tareas manuales sea seguro y facil para operadores.

### TODO

- [ ] Expandir modelos de API para soportar argumentos mas ricos que `float | str`.
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

## Prioridad 6 - Pruebas

Objetivo: cubrir los errores que mas probablemente rompen operacion.

### TODO

- [ ] Configurar `pytest`.
- [ ] Anadir prueba de importacion del worker.
- [ ] Anadir prueba de registro de tareas Celery.
- [ ] Anadir prueba de coherencia de `beat_schedule`.
- [ ] Anadir pruebas unitarias para parsing de fechas e intervalos.
- [ ] Anadir pruebas con filesystem temporal para rutas de salida.
- [ ] Crear fixtures minimas o mocks para `gfatpy`.
- [ ] Anadir comprobacion de tipos con `mypy` o `pyright` si no bloquea el flujo actual.
- [ ] Anadir lint/format con `ruff`.

### Orden Sugerido

1. Pruebas de agenda Celery.
2. Pruebas de validacion de argumentos.
3. Pruebas de tareas sin tocar NAS ni SCC.
4. Pruebas de integracion opcionales con datos controlados.

## Prioridad 7 - Seguridad y Gestion de Secretos

Objetivo: que el repositorio pueda compartirse sin exponer credenciales ni detalles sensibles.

### TODO

- [ ] Confirmar que no hay secretos en commits antes de publicar.
- [ ] Anadir instrucciones para crear `info_scc_user.yml` desde `worker/info_scc_example.yml`.
- [ ] Documentar permisos minimos necesarios para NAS y SCC.
- [ ] Evitar imprimir credenciales o rutas sensibles en logs.
- [ ] Evaluar uso de Docker secrets o gestor externo si el despliegue lo permite.

## Prioridad 8 - Evolucion Funcional

Ideas para crecer sin romper el nucleo operativo.

### TODO

- [ ] Soportar multiples lidares mediante configuracion externa.
- [ ] Separar agenda por instrumento o estacion.
- [ ] Permitir activar/desactivar tareas programadas por entorno.
- [ ] Crear perfiles de SCC por sistema/configuracion.
- [ ] Anadir dry-run para validar que existen inputs antes de lanzar conversiones largas.
- [ ] Generar reporte diario automatico de productos creados.
- [ ] Evaluar persistencia de metadatos de ejecucion en base de datos ligera si Redis no es suficiente.

## Backlog Tecnico

- [ ] Revisar nombres de variables de entorno en `docker-compose.yml` y documentarlos de forma consistente.
- [ ] Revisar si `Measurement`, `MeasurementType` y otros imports no usados deben eliminarse.
- [ ] Centralizar constantes como `ALHAMBRA`, canales y SCC IDs.
- [ ] Evitar strings magicos para patrones de fichero.
- [ ] Normalizar mayusculas/minusculas de `ALHAMBRA` vs `alhambra`.
- [ ] Anadir `README` de arquitectura con diagrama simple del flujo.
- [ ] Crear script de diagnostico local para comprobar mounts, Redis, SCC config y tareas registradas.

## Registro de Decisiones

### 2026-05-04

- Se crea este roadmap como documento vivo.
- Se prioriza estabilizar el sistema operativo existente antes de hacer refactors amplios.
- Se identifica como primera linea de trabajo la agenda Celery, secretos y configuracion.

## Acciones Completadas

- [x] Revision inicial de estructura del repositorio.
- [x] Identificacion del flujo operativo principal.
- [x] Creacion de hoja de ruta inicial.
- [x] Preparacion inicial del worker para importar `lidarpy` cuando `atmolidarpy` este instalado, manteniendo fallback a `gfatpy`.
