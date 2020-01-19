# tf-agents from guyk
this file includes some instructions for running the code that was cloned from my repository.  
## Installation 
**DON'T DO:**  
In the original README file, at the installation section they instruct to install tf-agents
`pip install --user tf-agents`  
using --user from within virtual env doesnt make sense as it installs in `$HOME/.local/python3.6/site-packages` and any change in the code will be ignored    
Please ignore this section and instead....

**Do the following:**  
`pip install gin-config` - to install the gin config that is needed as part of the tf-agent  
`pip install tensorflow_probability` - if was not done already

## Running the colab notebooks
In order to find the code repository (assuming we havent pip installed tf-agents), one need to add the following at the beginning of the notebook:  
```python 
import os
import sys
print('inserting the following to path',os.path.abspath('../..'))
sys.path.insert(0,os.path.abspath('../..'))
```

and at the last cell, run:  
`sys.path.remove(os.path.abspath('../..'))`  

## Running the code from command line
To run from command line, you'll have to add the project root to the PYTHONPATH.
this can be done by editing the `.bashrc` file as follows:
```shell script
export PYTHONPATH=$PYTHONPATH:$HOME/PycharmProjects/remote/MLA/RL/agents   
``` 
Alternatively, you can run from the command line:
```shell script
PYTHONPATH=$PYTHONPATH:$HOME/PycharmProjects/remote/MLA/RL/agents <command line to run the script>
```
If you want to run tensorboard to view the learning curve in live, run the following:
`tensorboard --logdir <logdir> --bind_all `
and then connect from your local machine by feeding the address: `xxx.xxx.xxx.xxx:6006` in the explorer 
(i.e. listening on port 6006)

Note that I've also started to create a `run_script.sh` file that will run the script along with tensorboard.
but it's still WIP.




## Running the code from Pycharm (remote debugging)
To run from Pycharm **on the server**, you'll have to set the interpreter to user remote ssh interpreter.
Basically, the Pycharm sets the project root s.t. the imports will work even if tf-agent wasnt pip-installed.
**And indeed so it happens !**
So nothing to do here.
 



 