# coding=utf-8
# Copyright 2018 The TF-Agents Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Edited by guyk1971

"""Train and Eval DQN.

To run DQN on CartPole:
```bash
tensorboard --logdir <log_dir> --bind_all

python dqn_hands_on_be.py --alsologtostderr  --n_experiments 3 --exp_json <json file name> --gpu 0 \
  [--root_dir=$HOME/share/Data/MLA/agents/]
```
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import time
# pp=os.path.dirname(os.path.abspath( __file__ )).split(os.path.sep)
# pp=os.path.join(*pp[:pp.index('tf_agents')])
# if 'PYTHONPATH' in os.environ:
#     if pp not in os.environ['PYTHONPATH']:
#         print('appending to PYTHONPATH')
#         os.environ['PYTHONPATH']+= ':'+pp
# else:
#     print('creating PYTHONPATH')
#     os.environ['PYTHONPATH'] = pp
# print(os.environ['PYTHONPATH'])

from absl import app
from absl import flags
from absl import logging
import random
import numpy as np
import tensorflow as tf
import json
from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import dynamic_step_driver
from tf_agents.environments import suite_gym
from tf_agents.environments import tf_py_environment
from tf_agents.environments.examples import masked_cartpole  # pylint: disable=unused-import
from tf_agents.eval import metric_utils
from tf_agents.metrics import tf_metrics
from tf_agents.networks import q_network
from tf_agents.networks import q_rnn_network
from tf_agents.policies import random_tf_policy
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.utils import common
from tf_agents.utils.my_utils import set_gpu_device
from tqdm import tqdm

# add a default path for the root dir. it will be $HOME/share/Data/MLA/agents
# (e.g. /home/aahds_1/share/Data/MLA/agents)
DEFAULT_ROOT_DIR = os.path.join(os.path.expanduser('~'),'share','Data','MLA','agents')

# @gin.configurable
def train_eval(
        root_dir,
        env_name='CartPole-v0',
        num_iterations=100000,
        train_sequence_length=1,
        # Params for QNetwork
        fc_layer_params=(100,),
        # Params for QRnnNetwork
        input_fc_layer_params=(50,),
        lstm_size=(20,),
        output_fc_layer_params=(20,),

        # Params for collect
        initial_collect_steps=1000,
        collect_steps_per_iteration=1,
        epsilon_greedy=0.1,
        replay_buffer_capacity=100000,
        # Params for target update
        target_update_tau=0.05,
        target_update_period=5,
        # Params for train
        train_steps_per_iteration=1,
        batch_size=64,
        learning_rate=1e-3,
        n_step_update=1,
        gamma=0.99,
        reward_scale_factor=1.0,
        gradient_clipping=None,
        use_tf_functions=True,
        # Params for eval
        num_eval_episodes=10,
        eval_interval=1000,
        # Params for checkpoints
        train_checkpoint_interval=10000,
        policy_checkpoint_interval=5000,
        rb_checkpoint_interval=20000,
        # Params for summaries and logging
        log_interval=1000,
        summary_interval=1000,
        summaries_flush_secs=10,
        debug_summaries=False,
        summarize_grads_and_vars=False,
        eval_metrics_callback=None,
        **kwargs):

    # todo: save local parameters to file as a json (see my_vpg)
    """A simple train and eval for DQN."""
    root_dir = os.path.expanduser(root_dir)
    train_dir = os.path.join(root_dir, 'train')
    eval_dir = os.path.join(root_dir, 'eval')

    tf.compat.v1.reset_default_graph()
    train_summary_writer = tf.compat.v2.summary.create_file_writer(
        train_dir, flush_millis=summaries_flush_secs * 1000)
    train_summary_writer.set_as_default()

    eval_summary_writer = tf.compat.v2.summary.create_file_writer(
        eval_dir, flush_millis=summaries_flush_secs * 1000)
    eval_metrics = [
        tf_metrics.AverageReturnMetric(buffer_size=num_eval_episodes),
        tf_metrics.AverageEpisodeLengthMetric(buffer_size=num_eval_episodes)
    ]

    global_step = tf.compat.v1.train.get_or_create_global_step()
    with tf.compat.v2.summary.record_if(
            lambda: tf.math.equal(global_step % summary_interval, 0)):
        tf_env = tf_py_environment.TFPyEnvironment(suite_gym.load(env_name))
        eval_tf_env = tf_py_environment.TFPyEnvironment(suite_gym.load(env_name))

        if train_sequence_length != 1 and n_step_update != 1:
            raise NotImplementedError(
                'train_eval does not currently support n-step updates with stateful '
                'networks (i.e., RNNs)')

        if train_sequence_length > 1:
            q_net = q_rnn_network.QRnnNetwork(
                tf_env.observation_spec(),
                tf_env.action_spec(),
                input_fc_layer_params=input_fc_layer_params,
                lstm_size=lstm_size,
                output_fc_layer_params=output_fc_layer_params)
        else:
            q_net = q_network.QNetwork(
                tf_env.observation_spec(),
                tf_env.action_spec(),
                fc_layer_params=fc_layer_params)
            train_sequence_length = n_step_update

        # TODO(b/127301657): Decay epsilon based on global step, cf. cl/188907839
        tf_agent = dqn_agent.DqnAgent(
            tf_env.time_step_spec(),
            tf_env.action_spec(),
            q_network=q_net,
            epsilon_greedy=epsilon_greedy,
            n_step_update=n_step_update,
            target_update_tau=target_update_tau,
            target_update_period=target_update_period,
            optimizer=tf.compat.v1.train.AdamOptimizer(learning_rate=learning_rate),
            td_errors_loss_fn=common.element_wise_squared_loss,
            gamma=gamma,
            reward_scale_factor=reward_scale_factor,
            gradient_clipping=gradient_clipping,
            debug_summaries=debug_summaries,
            summarize_grads_and_vars=summarize_grads_and_vars,
            train_step_counter=global_step)
        tf_agent.initialize()

        train_metrics = [
            tf_metrics.NumberOfEpisodes(),
            tf_metrics.EnvironmentSteps(),
            tf_metrics.AverageReturnMetric(),
            tf_metrics.AverageEpisodeLengthMetric(),
        ]

        eval_policy = tf_agent.policy
        collect_policy = tf_agent.collect_policy

        replay_buffer = tf_uniform_replay_buffer.TFUniformReplayBuffer(
            data_spec=tf_agent.collect_data_spec,
            batch_size=tf_env.batch_size,
            max_length=replay_buffer_capacity)

        collect_driver = dynamic_step_driver.DynamicStepDriver(
            tf_env,
            collect_policy,
            observers=[replay_buffer.add_batch] + train_metrics,
            num_steps=collect_steps_per_iteration)

        train_checkpointer = common.Checkpointer(
            ckpt_dir=train_dir,
            agent=tf_agent,
            global_step=global_step,
            metrics=metric_utils.MetricsGroup(train_metrics, 'train_metrics'))
        policy_checkpointer = common.Checkpointer(
            ckpt_dir=os.path.join(train_dir, 'policy'),
            policy=eval_policy,
            global_step=global_step)
        rb_checkpointer = common.Checkpointer(
            ckpt_dir=os.path.join(train_dir, 'replay_buffer'),
            max_to_keep=1,
            replay_buffer=replay_buffer)

        train_checkpointer.initialize_or_restore()
        rb_checkpointer.initialize_or_restore()

        if use_tf_functions:
            # To speed up collect use common.function.
            collect_driver.run = common.function(collect_driver.run)
            tf_agent.train = common.function(tf_agent.train)

        initial_collect_policy = random_tf_policy.RandomTFPolicy(
            tf_env.time_step_spec(), tf_env.action_spec())

        # Collect initial replay data.
        logging.info(
            'Initializing replay buffer by collecting experience for %d steps with '
            'a random policy.', initial_collect_steps)
        dynamic_step_driver.DynamicStepDriver(
            tf_env,
            initial_collect_policy,
            observers=[replay_buffer.add_batch] + train_metrics,
            num_steps=initial_collect_steps).run()

        results = metric_utils.eager_compute(
            eval_metrics,
            eval_tf_env,
            eval_policy,
            num_episodes=num_eval_episodes,
            train_step=global_step,
            summary_writer=eval_summary_writer,
            summary_prefix='Metrics',
        )
        if eval_metrics_callback is not None:
            eval_metrics_callback(results, global_step.numpy())
        metric_utils.log_metrics(eval_metrics)

        time_step = None
        policy_state = collect_policy.get_initial_state(tf_env.batch_size)

        timed_at_step = global_step.numpy()
        time_acc = 0

        # Dataset generates trajectories with shape [Bx2x...]
        dataset = replay_buffer.as_dataset(
            num_parallel_calls=3,
            sample_batch_size=batch_size,
            num_steps=train_sequence_length + 1).prefetch(3)
        iterator = iter(dataset)

        def train_step():
            experience, _ = next(iterator)
            return tf_agent.train(experience)

        if use_tf_functions:
            train_step = common.function(train_step)

        for _ in tqdm(range(num_iterations)):
            start_time = time.time()
            time_step, policy_state = collect_driver.run(
                time_step=time_step,
                policy_state=policy_state,
            )
            for _ in range(train_steps_per_iteration):
                train_loss = train_step()
            time_acc += time.time() - start_time

            if global_step.numpy() % log_interval == 0:
                logging.info('step = %d, loss = %f', global_step.numpy(),
                             train_loss.loss)
                steps_per_sec = (global_step.numpy() - timed_at_step) / time_acc
                logging.info('%.3f steps/sec', steps_per_sec)
                tf.compat.v2.summary.scalar(
                    name='global_steps_per_sec', data=steps_per_sec, step=global_step)
                timed_at_step = global_step.numpy()
                time_acc = 0

            for train_metric in train_metrics:
                train_metric.tf_summaries(
                    train_step=global_step, step_metrics=train_metrics[:2])

            if global_step.numpy() % train_checkpoint_interval == 0:
                train_checkpointer.save(global_step=global_step.numpy())

            if global_step.numpy() % policy_checkpoint_interval == 0:
                policy_checkpointer.save(global_step=global_step.numpy())

            if global_step.numpy() % rb_checkpoint_interval == 0:
                rb_checkpointer.save(global_step=global_step.numpy())

            if global_step.numpy() % eval_interval == 0:
                results = metric_utils.eager_compute(
                    eval_metrics,
                    eval_tf_env,
                    eval_policy,
                    num_episodes=num_eval_episodes,
                    train_step=global_step,
                    summary_writer=eval_summary_writer,
                    summary_prefix='Metrics',
                )
                if eval_metrics_callback is not None:
                    eval_metrics_callback(results, global_step.numpy())
                metric_utils.log_metrics(eval_metrics)
        return train_loss


def save_params(params,dir):
    with open(os.path.join(dir, "params.json"), 'w') as out:
        out.write(json.dumps(params, separators=(',\n','\t:\t'), sort_keys=True))


def run_experiment(exp_params):

    seed = exp_params['seed']
    # set the seed in all environments
    tf.random.set_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    logging.info('set seed to {0} and creating folder for results'.format(seed))

    root_dir = os.path.join(exp_params['root_dir'],str(seed))
    os.makedirs(root_dir)
    exp_params['root_dir']=root_dir
    train_eval(**exp_params)
    return

def_exp_params={'env_name':'CartPole-v0',
                'num_iterations':100000,
                'train_sequence_length':1,
                # Params for QNetwork
                'fc_layer_params':(100,),
                # Params for QRnnNetwork
                'input_fc_layer_params':(50,),
                'lstm_size':(20,),
                'output_fc_layer_params':(20,),
                # Params for collect
                'initial_collect_steps':1000,
                'collect_steps_per_iteration':1,
                'epsilon_greedy':0.1,
                'replay_buffer_capacity':100000,
                # Params for target update
                'target_update_tau':0.05,
                'target_update_period':5,
                # Params for train
                'train_steps_per_iteration':1,
                'batch_size':64,
                'learning_rate':1e-3,
                'n_step_update':1,
                'gamma':0.99,
                'reward_scale_factor':1.0,
                'gradient_clipping':None,
                'use_tf_functions':True,
                # Params for eval
                'num_eval_episodes':10,
                'eval_interval':1000,
                # Params for checkpoints
                'train_checkpoint_interval':10000,
                'policy_checkpoint_interval':5000,
                'rb_checkpoint_interval':20000,
                # Params for summaries and logging
                'log_interval':1000,
                'summary_interval':1000,
                'summaries_flush_secs':10,
                'debug_summaries':False,
                'summarize_grads_and_vars':False,
                'eval_metrics_callback':None
               }



def main(_):
    FLAGS.alsologtostderr = True
    logging.set_verbosity(logging.INFO)

    tf.compat.v1.enable_v2_behavior()  # according to documentation, we dont need to call it...
    # gin.parse_config_files_and_bindings(FLAGS.gin_file, FLAGS.gin_param)
    set_gpu_device(FLAGS.gpu)
    root_dir = FLAGS.root_dir        # assuming the root dir already exists

    # root dir is where the results of the experiments are saved. each experiment in its own folder
    # <exp name>_<env name>_<time>
    if root_dir is None:
        root_dir = DEFAULT_ROOT_DIR
    assert (os.path.exists(root_dir)), 'root dir {0} does not exist. create it first'.format(DEFAULT_ROOT_DIR)

    # take default parameters from default json file
    experiment_params = def_exp_params

    # read the parameters from json. if only filename provided, look at the default path for jsons
    if FLAGS.exp_json:
        json_name = os.path.splitext(os.path.basename(FLAGS.exp_json))[0]
        if os.path.isfile(FLAGS.exp_json):   # if the full path is given and there's a file, read it
            logging.info('loading configuration from '+FLAGS.exp_json)
            with open(FLAGS.exp_json,'r') as f:
                experiment_params = json.load(f)
        elif os.path.isfile(os.path.join(root_dir,'jsons',FLAGS.exp_json)):
            json_path = os.path.join(root_dir,'jsons',FLAGS.exp_json)
            logging.info('loading configuration from ' + json_path)
            with open(json_path,'r') as f:
                experiment_params = json.load(f)
    else:
        json_name = 'dqn_default'

    # create results file (if not already exist)
    root_dir = os.path.join(root_dir,'results')
    if not(os.path.exists(root_dir)):
        os.makedirs(root_dir)

    # exp_root_dir = experiment_params['env_name'] + '_' + json_file + '_' + time.strftime("%d-%m-%Y_%H-%M-%S")
    exp_root_dir = json_name + '_' + time.strftime("%d-%m-%Y_%H-%M-%S")
    experiment_params['root_dir'] = os.path.join(root_dir,exp_root_dir)
    os.makedirs(experiment_params['root_dir'])
    logging.get_absl_handler().use_absl_log_file(log_dir=experiment_params['root_dir'])


    for e in range(FLAGS.n_experiments):
        seed = FLAGS.seed + 10*e
        experiment_params['seed'] = seed
        experiment_params['root_dir'] = os.path.join(root_dir, exp_root_dir)
        run_experiment(experiment_params)

if __name__ == '__main__':
    # flags.mark_flag_as_required('root_dir')
    # Command line arguments
    flags.DEFINE_string('root_dir', os.getenv('TEST_UNDECLARED_OUTPUTS_DIR'),
                        'Root directory for writing logs/summaries/checkpoints.')

    flags.DEFINE_string('exp_json', None,
                        'experiment parameters json file')

    flags.DEFINE_integer('n_experiments', 1,
                         'Number of experiments to run (with different seeds)')

    flags.DEFINE_integer('seed', 1,
                         'the base seed to work with')

    flags.DEFINE_string('gpu', '0',
                        'gpu ID to use. see nvidia-smi for gpu ids or -1 to use the cpu')
    flags.DEFINE_multi_string('gin_file', None, 'Paths to the gin-config files.')
    flags.DEFINE_multi_string('gin_param', None, 'Gin binding parameters.')

    FLAGS = flags.FLAGS
    app.run(main)
