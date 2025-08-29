# Environment scripts

this folder includes bash scripts that can be used to set up the environment for the project. The scripts are used to install the required packages and set up the environment variables.  
you can either build a conda environment using the `create_gai.sh` script,  
or build a docker image (recommended).


## Docker Environment
first, from teh project root folder run:
```bash
./env_scripts/docker_build_run_lws.sh
```  

this will build the docker image and run the container.
then you'll have to perform a 'post-build' installations from within the container:
1. install huggingface transformers from source:  
   the assumption is that this project is in `/home/guy/code/study/git/guyk1971/gen_ai_sb`. in that case, you should `git clone` the transformers repo to `/home/guy/code/study/git/clones` and then:
    ```bash
    cd /home/guy/code/study/git/clones/transformers
    pip install -e .
    ```
1. install TRL library from source:
   the same assumption and procedure as for transformers, but the path is `/home/guy/code/study/git/clones/trl`
   ```bash
    cd /home/guy/code/study/git/clones/trl
    pip install -e .
    ```
1. Install additional required optimization packages:
   ```bash
    pip install deepspeed accelerate bitsandbytes peft 
    ```
1. run vs code and attach to the container. This will install the vs-code server inside the container.
1. install any necessary extensions in vs-code:
    - python
    - github copilot   
    
Now the container is ready for development. its time to commit it to an image

1. temporarily detach from the container (ctrl-p ctrl-q)
2. commit the container to an image:
    ```bash
    docker commit <container_id> guyk1971/genai_sb:dev
    ```   
    where `<container_id>` is the id of the running container. you can get it by running `docker ps` and looking at the `CONTAINER ID` column. or just use the container name
3. re-attch to the container:
    ```bash
    docker attach <container_id>
    ```   
    or just use the container name

from now on, you can use the `docker_run_lws.sh` script to run the container.