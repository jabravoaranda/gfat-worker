# Despliegue en servidor CPD

Este documento describe el despliegue estable de `gfat-worker` en un servidor Linux con Docker Compose.

## Principios

- El codigo vive en Git.
- La imagen Docker contiene el codigo y las dependencias.
- La configuracion real vive fuera del repositorio.
- Los datos RAW se montan en solo lectura.
- Los productos se montan con escritura.
- Redis persiste sus datos en un volumen Docker.
- Flower no se expone publicamente por defecto.

## Estructura Recomendada

```text
/opt/gfat-worker/
  repo/                 # checkout Git
  .env.production       # configuracion local, no versionada
  info_scc_user.yml     # credenciales/config SCC, no versionado
```

## Instalacion Inicial

1. Instalar Docker Engine y el plugin de Docker Compose.
2. Crear el directorio base:

```bash
sudo mkdir -p /opt/gfat-worker
sudo chown "$USER":"$USER" /opt/gfat-worker
```

3. Clonar el repositorio:

```bash
git clone git@github.com:jabravoaranda/gfat-worker.git /opt/gfat-worker/repo
cd /opt/gfat-worker/repo
```

4. Crear la configuracion local:

```bash
cp .env.example /opt/gfat-worker/.env.production
```

5. Editar `/opt/gfat-worker/.env.production` con las rutas reales del servidor:

```bash
RAW_HOST_DIR=/mnt/RAW/UGR
PRODUCTS_HOST_DIR=/mnt/PRODUCTS/UGR
INFO_SCC_CONFIG_HOST_PATH=/opt/gfat-worker/info_scc_user.yml
API_BIND=127.0.0.1
API_PORT=8000
```

6. Crear `/opt/gfat-worker/info_scc_user.yml` a partir de `worker/info_scc_example.yml` y rellenar credenciales reales fuera de Git.

## Primer Arranque

```bash
cd /opt/gfat-worker/repo
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml up -d --build
```

Comprobar estado:

```bash
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml ps
curl -fsS http://127.0.0.1:8000/
```

## Actualizacion

El script `scripts/deploy.sh` actualiza desde GitHub, reconstruye la imagen y recrea contenedores.

```bash
cd /opt/gfat-worker/repo
APP_DIR=/opt/gfat-worker/repo \
ENV_FILE=/opt/gfat-worker/.env.production \
scripts/deploy.sh
```

Por defecto despliega `origin/main`. Tambien se puede desplegar un tag o commit concreto:

```bash
APP_DIR=/opt/gfat-worker/repo \
ENV_FILE=/opt/gfat-worker/.env.production \
scripts/deploy.sh v0.1.0
```

Si la API no levanta tras la actualizacion, el script vuelve al commit anterior y recrea los contenedores.

## Logs

```bash
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml logs -f api
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml logs -f worker
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml logs -f redis
```

## Flower

Flower esta en un perfil opcional y se bindea a `127.0.0.1` por defecto.

```bash
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml --profile ops up -d flower
```

Si se necesita acceder desde fuera del servidor, usar tunel SSH o un reverse proxy autenticado.

## Parada

```bash
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml down
```

No usar `-v` en produccion salvo que se quiera borrar el volumen persistente de Redis.

## Rollback Manual

El despliegue guarda el commit anterior en `.deploy-previous-commit`.

```bash
cd /opt/gfat-worker/repo
previous="$(cat .deploy-previous-commit)"
git checkout --detach "$previous"
docker compose --env-file /opt/gfat-worker/.env.production -f compose.prod.yml up -d --build --remove-orphans
```

## Tarea de Diagnostico

Desde la API se puede comprobar que el worker ve `lidarpy`:

```bash
curl -fsS -X POST http://127.0.0.1:8000/task_queue \
  -H 'Content-Type: application/json' \
  -d '{"task_name":"tasks.misc.lidar_backend_status","args":[],"kwargs":{}}'
```

Consultar el resultado con el `id` devuelto:

```bash
curl -fsS http://127.0.0.1:8000/task_queue/<task-id>
```
