#!/bin/bash
# Usage: ./docker_build_run_x299.sh [model_name]
# If a model name is provided, the script will setup Ollama and use the llmnet network.

# DIR is the directory where the script is saved (should be <project_root/scripts)
DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
cd $DIR

MY_UNAME=$(id -un)


IMAGE=agents_udemy:dev

CACHE_FOLDER_ON_HOST=/home/${MY_UNAME}/.cache/
MOUNT_CACHE_FOLDER=" --mount type=bind,source=${CACHE_FOLDER_ON_HOST},target=/home/${MY_UNAME}/.cache"

CODE_FOLDER=/home/${MY_UNAME}/code
MOUNT_CODE_FOLDER="--mount type=bind,source=${CODE_FOLDER},target=${CODE_FOLDER}"

DATA_FOLDER=/home/${MY_UNAME}/data
MOUNT_DATA_FOLDER=" --mount type=bind,source=${DATA_FOLDER},target=${DATA_FOLDER}"

# If a model name is provided, setup Ollama and use the llmnet network.
MODEL_NAME=$1
NETWORK_ARG=""

if [ ! -z "$MODEL_NAME" ]; then
    # Ensure the llmnet network exists
    docker network inspect llmnet >/dev/null 2>&1 || docker network create llmnet

    docker run -d --rm --gpus all --name ollama --network llmnet -p 11434:11434 ollama/ollama

    # Wait until Ollama API is ready
    until curl -s http://localhost:11434 | grep -q 'Ollama'; do
        echo "Waiting for Ollama to be ready..."
        sleep 1
    done

    docker exec -it ollama ollama pull ${MODEL_NAME}
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
 
cd -


