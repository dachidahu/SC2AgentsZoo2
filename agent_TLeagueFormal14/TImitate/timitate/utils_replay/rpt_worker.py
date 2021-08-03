"""Replay Processing Task Master"""
import logging
from random import randint
from time import sleep
from enum import IntEnum

import zmq

from timitate.utils_replay.rpt_master import MsgRequestGetReplay
from timitate.utils_replay.rpt_master import MsgRespondGetReplay
from timitate.utils_replay.rpt_master import MsgRequestSendResult
from timitate.utils_replay.rpt_master import MsgRespondSendResult

class RPTWorkerStatus(IntEnum):
  ok = 0
  no_new_repaly = 1


# Worker
class RPTWorker(object):
  """Replay Processing Task Worker."""
  def __init__(self, master_endpoint, max_try=5,
               fun_proc_replay=lambda **x: None):
    context = zmq.Context()
    self._master_socket = context.socket(zmq.REQ)
    self._master_socket.connect("tcp://{}".format(master_endpoint))
    #self._master_socket.setsockopt(zmq.SNDHWM, 4)
    #self._master_socket.setsockopt(zmq.RCVHWM, 4)
    logging.info('connecting to {}'.format(master_endpoint))

    self._max_try = max_try
    self._fun_proc_replay = fun_proc_replay

  def run(self):
    logging.info('enter run')
    while True:
      status = self._run_one_replay()
      if status == RPTWorkerStatus.no_new_repaly:
        time_sleep = randint(0, 5)
        logging.info('waiting {} secs...'.format(time_sleep))
        sleep(time_sleep)

  def _run_one_replay(self):
    logging.info('enter _run_one_replay')

    # try to get a replay
    response = self._request_get_replay()
    kwargs = {
      'replay_name': response.replay_name,
      'player_id': response.player_id
    }
    if response.game_version is not None:
      kwargs['game_version'] = response.game_version
    if response.replay_name is None:
      logging.info('No new replay to be analyzed.')
      return RPTWorkerStatus.no_new_repaly

    # do the analyzing job
    n_try = self._max_try
    while True:
      try:
        result = self._fun_proc_replay(**kwargs)
        n_try = 0
      except Exception as e:
        logging.warning('n_try: {}, error during fun_proc_replay\n:{}'.format(
          n_try, str(e)))
        result = None
        n_try -= 1
      if n_try <= 0:
        break

    # and send the result
    response = self._request_send_result(result, **kwargs)
    logging.info('leave _run_one_replay')
    return RPTWorkerStatus.ok

  def _request_get_replay(self):
    logging.info('enter _request_get_replay')
    request = MsgRequestGetReplay()
    self._master_socket.send_pyobj(request)
    response = self._master_socket.recv_pyobj()
    isinstance(response, MsgRespondGetReplay)
    logging.info('leave _request_get_replay')
    return response

  def _request_send_result(self, result, replay_name, player_id,
                           game_version=None):
    logging.info('enter _request_send_result')
    request = MsgRequestSendResult()
    request.user_data = result
    request.replay_name = replay_name
    request.player_id = player_id
    request.game_version = game_version
    self._master_socket.send_pyobj(request)
    response = self._master_socket.recv_pyobj()
    isinstance(response, MsgRespondSendResult)
    logging.info('leave _request_send_result, status {}'.format(
      response.status))
    return response