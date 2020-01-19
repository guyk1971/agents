from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import random
import numpy as np
import tensorflow as tf
import json
from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import dynamic_step_driver
from tf_agents.environments import suite_gym
from tf_agents.environments import tf_py_environment
from tf_agents.eval import metric_utils
from tf_agents.metrics import tf_metrics
from tf_agents.networks import q_network
from tf_agents.networks import q_rnn_network
from tf_agents.policies import random_tf_policy
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.utils import common
from tf_agents.utils.my_utils import set_gpu_device


def main():
    env_name='FrozenLake8x8-v0'
    # env_name = 'CartPole-v0'
    # env_name = 'NChain-v0'
    # env_name = 'LunarLanderContinuous-v2'
    # env_name='MountainCarContinuous-v0'
    # env_name = 'Copy-v0'
    example_environment = tf_py_environment.TFPyEnvironment(suite_gym.load(env_name))
    example_policy = random_tf_policy.RandomTFPolicy(example_environment.time_step_spec(),
                                                    example_environment.action_spec())
    time_step = example_environment.reset()
    action_step=example_policy.action(time_step)
    time_step=example_environment.step(action_step.action)
    print(time_step)
    return




if __name__ == '__main__':
    # flags.mark_flag_as_required('root_dir')
    # Command line arguments
    main()
