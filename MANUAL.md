# Docker Cheat Sheet

#Useful
NAS_URL_RAW="//<nas-host>/RAW"
NAS_URL_PRODUCTS="//<nas-host>/PRODUCTS"
NAS_USER="<nas-user>"
NAS_PASSWORD="<nas-password>"


## Main instructions

### Build docker-compose
docker-compoase build

### Build docker-compose ignoring cache
docker-compose build --no-cache

### Access to the worker bash (command line)
docker exec -it gfat-worker-worker-1 /bin/bash

### Edit .env to provide required information
- NAS_RAW_PATH="Z://"
- NAS_PRODUCTS_PATH="W://"

## Basic Docker Commands

- **List Running Containers:**
  ```bash
  docker ps
  ```

- **List All Containers (Including Stopped):**
  ```bash
  docker ps -a
  ```

- **Start a Stopped Container:**
  ```bash
  docker start <container_id_or_name>
  ```

- **Stop a Running Container:**
  ```bash
  docker stop <container_id_or_name>
  ```

- **Remove a Stopped Container:**
  ```bash
  docker rm <container_id_or_name>
  ```

## Accessing a Container

- **Access the Terminal of a Running Container with Bash:**
  ```bash
  docker exec -it <container_id_or_name> /bin/bash
  ```

  ```bash
  docker exec -it  /bin/bash
  ```

- **Access the Terminal with `sh` if Bash is Unavailable:**
  ```bash
  docker exec -it <container_id_or_name> /bin/sh
  ```

## Viewing and Managing Logs

- **View Logs of a Container:**
  ```bash
  docker logs <container_id_or_name>
  ```

## Working with Volumes and Paths

- **Example for Mounting Volumes in `docker-compose.yaml`:**
  ```yaml
  volumes:
    - ${NAS_RAW_PATH}:/mnt/RAW
    - ${NAS_PRODUCTS_PATH}:/mnt/PRODUCTS
  ```

## Example Docker Compose Commands

- **Start Services Defined in `docker-compose.yaml`:**
  ```bash
  docker-compose up
  ```

- **Stop and Remove Containers, Networks, and Volumes Created by `docker-compose up`:**
  ```bash
  docker-compose down
  ```

## Python and Pip Inside Containers

- **Check Installed Python Packages and Their Locations:**
  ```bash
  pip show gfatpy
  ```

- **Find Where a Python Package Is Installed:**
  ```bash
  python -c "import gfatpy; print(gfatpy.__file__)"
  ```

## Debugging and Permissions

- **Verify and Modify Permissions of a Script (`start.sh` Example):**
  ```bash
  ls -l /usr/src/app/start.sh
  chmod +x /usr/src/app/start.sh
  ```

## Additional Tips

- **Force Rebuild an Image:**
  ```bash
  docker-compose build --no-cache
  ```

- **Delete All Containers (Use with Caution):**
  ```bash
  docker rm $(docker ps -a -q)
  ```

- **Delete All Images (Use with Caution):**
  ```bash
  docker rmi $(docker images -q)
  ```
