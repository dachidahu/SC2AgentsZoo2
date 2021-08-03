import logging
from os import path
from time import sleep

import zmq

from distladder3.player_manager import _get_cur_model_filenames
from distladder3.player_manager import _write_agent_config_v3
from distladder3.utils import Player
from distladder3.player_manager.player_manager import MsgRequestAppendPlayer
from distladder3.player_manager.player_manager import MsgRespondAppendPlayer


class GreedyChkpointPlayerMaker(object):
  """ A greedy checkpoint player maker.

  For a watched player specified by agent_dir,
  GreedyChkpointPlayerMaker scans the watched_chkpoint_root_dir and generates
  config file for each NN model checkpoint.
  It writes the config files to output_agent_configs_dir.
  It also sends the players to PlayerManager. """
  def __init__(self, player_manager_endpoint, agent_dir, agent_config_kvs,
               watched_chkpoints_root_dir, output_agent_configs_dir):
    self.agent_dir = agent_dir
    self.agent_config_kvs = agent_config_kvs
    self.watched_chkpoints_root_dir = watched_chkpoints_root_dir
    self.output_agent_configs_dir = output_agent_configs_dir

    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self._pm_socket = context.socket(zmq.REQ)
    self._pm_socket.connect("tcp://{}".format(player_manager_endpoint))
    self._pm_socket.setsockopt(zmq.SNDHWM, 4)
    self._pm_socket.setsockopt(zmq.RCVHWM, 4)
    pass

  def run(self):
    logging.info('start watching {}'.format(self.watched_chkpoints_root_dir))

    model_filenames = []
    i_prev_end = len(model_filenames)
    while True:
      logging.info('found #model_filenames: {}'.format(len(model_filenames)))
      logging.info('trying to find newly added model filenames')
      cur_md_fns = _get_cur_model_filenames(self.watched_chkpoints_root_dir)
      for mf in cur_md_fns:
        if mf not in model_filenames:
          logging.info('found new model {}'.format(mf))
          model_filenames.append(mf)

      for ind in range(i_prev_end, len(model_filenames)):
        # write the config
        kvs = self.agent_config_kvs
        kvs['chkpoints_root_dir'] = self.watched_chkpoints_root_dir
        kvs['model_criterion'] = 'spec'
        kvs['model_filename'] = model_filenames[ind]
        model_basename = path.splitext(model_filenames[ind])[0]
        agent_config = _write_agent_config_v3(
          agent_config_kvs=kvs,
          model_basename=model_basename,
          i_cfg=ind,
          output_configs_dir=self.output_agent_configs_dir
        )
        logging.info('done writing cfg {}'.format(agent_config))
        # send the player
        request = MsgRequestAppendPlayer()
        request.player = Player(name=model_basename,
                                agent_dir=self.agent_dir,
                                agent_config=agent_config)
        self._pm_socket.send_pyobj(request)
        response = self._pm_socket.recv_pyobj()
        assert isinstance(response, MsgRespondAppendPlayer)
        logging.info('done sending player, status: {}'.format(response.status))

      # update
      i_prev_end = len(model_filenames)
      t_sleep = 15
      logging.info('sleep {} secs for next scan...'.format(t_sleep))
      sleep(t_sleep)