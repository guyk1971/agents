#!/bin/bash
# Usage: ./docker_build_run_lws.sh [WITH_OLLAMA=true]
# If WITH_OLLAMA=true, the script will setup Ollama and use the llmnet network.
# If WITH_OLLAMA=false (default) the script will use the default network.

# DIR is the directory where the script is saved (should be <project_root/scripts)
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd $DIR

MY_UNAME=$(id -un)


IMAGE=gaisb_12_3:dev

CACHE_FOLDER_ON_HOST=/home/${MY_UNAME}/.cache/
MOUNT_CACHE_FOLDER=" --mount type=bind,source=${CACHE_FOLDER_ON_HOST},target=/home/${MY_UNAME}/.cache"

CODE_FOLDER=/home/${MY_UNAME}/code
MOUNT_CODE_FOLDER="--mount type=bind,source=${CODE_FOLDER},target=${CODE_FOLDER}"

DATA_FOLDER=/home/${MY_UNAME}/data
MOUNT_DATA_FOLDER=" --mount type=bind,source=${DATA_FOLDER},target=${DATA_FOLDER}"

# Parse WITH_OLLAMA argument (default: true)
WITH_OLLAMA=false
if [[ "$1" == "WITH_OLLAMA="* ]]; then
    WITH_OLLAMA="${1#WITH_OLLAMA=}"
    shift
fi

# Only run Ollama setup if WITH_OLLAMA is true
if [[ "$WITH_OLLAMA" == "true" || "$WITH_OLLAMA" == "True" ]]; then
    # Ensure the llmnet network exists
    docker network inspect llmnet >/dev/null 2>&1 || docker network create llmnet

    MODEL_NAME=qwen3:8b
    docker run -d --rm --gpus all --name ollama --network llmnet -p 11434:11434 ollama/ollama

    # Wait until Ollama API is ready
    until curl -s http://localhost:11434 | grep -q 'Ollama'; do
        echo "Waiting for Ollama to be ready..."
        sleep 1
    done

    docker exec -it ollama ollama pull ${MODEL_NAME}
fi

# If WITH_OLLAMA is true, use --network llmnet, else use default network
NETWORK_ARG=""
if [[ "$WITH_OLLAMA" == "true" || "$WITH_OLLAMA" == "True" ]]; then
    NETWORK_ARG="--network llmnet"
fi

docker run \
    --gpus \"device=all\" \
    --privileged \
    $NETWORK_ARG \
    --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 -it --rm \
    --mount type=bind,source=${DIR}/..,target=${DIR}/.. \
    ${MOUNT_CODE_FOLDER} \
    ${MOUNT_CACHE_FOLDER} \
    ${MOUNT_DATA_FOLDER} \
    --shm-size=8g \
    ${IMAGE}

# -v /var/run/docker.sock:/var/run/docker.sock \
# ${MOUNT_CODE_FOLDER} \
# ${MOUNT_DATA_FOLDER} \
# --name dlr  \
# -p 8888:8888 -p 6006:6006 \
# --mount type=bind,source=${DIR}/..,target=${DIR}/.. \
 
cd -


