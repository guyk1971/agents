#!/usr/bin/env bash
# the idea is to use it as follows:
# run_script.sh tf_agents/agents/dqn/examples/v2/train_eval.py --gpu 1 --root_dir 'root_dir'

if [[ $PYTHONPATH != *$PWD* ]]; then
  export PYTHONPATH=$PYTHONPATH:$PWD
fi
echo $PYTHONPATH
exec "$@"

#while [ "$1" != "" ]; do
#    case $1 in
#        -f | --file )           shift
#                                filename=$1
#                                ;;
#        -i | --interactive )    interactive=1
#                                ;;
#        -h | --help )           usage
#                                exit
#                                ;;
#        * )                     usage
#                                exit 1
#    esac
#    shift
#done

#tensorboard --logdir $HOME/tmp/dqn/gym/CartPole-v0/  --bind_all &
#python tf_agents/agents/dqn/examples/v2/train_eval.py --gpu 1 \
#  --root_dir=$HOME/tmp/dqn/gym/CartPole-v0/ --alsologtostderr

