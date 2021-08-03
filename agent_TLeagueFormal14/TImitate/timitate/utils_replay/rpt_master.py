"""Replay Processing Task Master"""
import logging
import os
from collections import deque
import csv

import zmq


# presume the 2-player case
ALLOWED_PLAYER_IDS = (1, 2)


# API: GetReplay
class MsgRequestGetReplay(object):
  def __init__(self):
    pass


class MsgRespondGetReplay(object):
  def __init__(self):
    self.replay_name = None
    self.player_id = None
    self.game_version = None


# API: SendResult
class MsgRequestSendResult(object):
  def __init__(self):
    self.user_data = None
    self.replay_name = None
    self.player_id = None
    self.game_version = None


class MsgRespondSendResult(object):
  def __init__(self):
    self.status = 'success'


# Master
class RPTMaster(object):
  """Replay Processing Task Master.

  Pass in your own result processing function."""
  def __init__(self, port, replay_dir, fun_result=lambda rst: print(rst)):
    context = zmq.Context()
    self._socket = context.socket(zmq.REP)
    self._socket.bind("tcp://0.0.0.0:{}".format(port))

    # init task q
    self._replay_filenames = _get_cur_replay_filenames(replay_dir)
    self._task_q = deque(maxlen=3 * len(self._replay_filenames))
    for f in self._replay_filenames:
      replay_name = f.split('.')[0]
      for player_id in ALLOWED_PLAYER_IDS:
        self._task_q.appendleft((replay_name, player_id))

    # init result q
    self._result_q = deque(maxlen=self._task_q.maxlen)

    # book-keeping
    self._fun_result = fun_result

  def run(self):
    logging.info("Enter RPTMaster.run")
    while True:
      # message loop
      request = self._socket.recv_pyobj()
      if isinstance(request, MsgRequestGetReplay):
        response = self._respond_get_replay(request)
      elif isinstance(request, MsgRequestSendResult):
        response = self._respond_send_result(request)
      else:
        raise RuntimeError("message {} not recognized".format(request))
      self._socket.send_pyobj(response)

  def _respond_get_replay(self, request):
    del request
    replay_name, player_id = None, None
    # choose a replay from the queue
    if self._task_q:
      replay_name, player_id = self._task_q.pop()
      logging.info(
        '_respond_get_replay: task popped, cur task q size: {}'.format(
          len(self._task_q))
      )

    respond = MsgRespondGetReplay()
    respond.replay_name = replay_name
    respond.player_id = player_id
    if len(self._task_q) > 0:
      logging.info(
        '_respond_get_replay: popped replay_name {}, player_id {}'.format(
          replay_name, player_id))
    return respond

  def _respond_send_result(self, request):
    logging.info(
      '_respond_send_result: processing replay_name {}, player_id {}'.format(
        request.replay_name, request.player_id))

    response = MsgRespondSendResult()
    try:
      self._fun_result(request.user_data)
      response.status = 'success'
    except Exception as e:
      response.status = 'error during processing the result\n{}'.format(str(e))

    logging.info('_respond_send_result: status: {}'.format(response.status))
    logging.info('_respond_send_result: task q size {}'.format(
      len(self._task_q)))
    return response


class RPTInfoCSVMaster(object):
  """Replay Processing Task Master.  Creating task from the specs of an info
  CSV file, which supports multiple game core version.

  Pass in your own result processing function."""
  def __init__(self, port, info_csv_path, fun_result=lambda rst: print(rst)):
    context = zmq.Context()
    self._socket = context.socket(zmq.REP)
    self._socket.bind("tcp://0.0.0.0:{}".format(port))

    # init task q
    rpg = _get_replay_name_player_id_game_version(info_csv_path)
    self._task_q = deque(maxlen=3 * len(rpg))
    for replay_name, player_id, game_version in rpg:
      self._task_q.appendleft((replay_name, player_id, game_version))

    # init result q
    self._result_q = deque(maxlen=self._task_q.maxlen)

    # book-keeping
    self._fun_result = fun_result

  def run(self):
    logging.info("Enter RPTMaster.run")
    while True:
      # message loop
      request = self._socket.recv_pyobj()
      if isinstance(request, MsgRequestGetReplay):
        response = self._respond_get_replay(request)
      elif isinstance(request, MsgRequestSendResult):
        response = self._respond_send_result(request)
      else:
        raise RuntimeError("message {} not recognized".format(request))
      self._socket.send_pyobj(response)

  def _respond_get_replay(self, request):
    del request
    replay_name, player_id, game_version = None, None, None
    # choose a replay from the queue
    if self._task_q:
      replay_name, player_id, game_version = self._task_q.pop()
      logging.info(
        '_respond_get_replay: task popped, cur task q size: {}'.format(
          len(self._task_q))
      )

    respond = MsgRespondGetReplay()
    respond.replay_name = replay_name
    respond.player_id = player_id
    respond.game_version = game_version
    if len(self._task_q) > 0:
      logging.info(
        '_respond_get_replay: popped replay_name {}, player_id {}, '
        'game_version {}'.format(replay_name, player_id, game_version)
      )
    return respond

  def _respond_send_result(self, request):
    logging.info(
      '_respond_send_result: processing replay_name {}, player_id {}, '
      'game_version {}'.format(request.replay_name, request.player_id,
                               request.game_version)
    )

    response = MsgRespondSendResult()
    try:
      self._fun_result(request.user_data)
      response.status = 'success'
    except Exception as e:
      response.status = 'error during processing the result\n{}'.format(str(e))

    logging.info('_respond_send_result: status: {}'.format(response.status))
    logging.info('_respond_send_result: task q size {}'.format(
      len(self._task_q)))
    return response


def _get_cur_replay_filenames(replay_dir):
  return [f for f in os.listdir(replay_dir) if f.endswith('.SC2Replay')]


def _get_replay_name_player_id_game_version(info_csv_path):
  with open(info_csv_path, 'r') as f:
    lines = list(csv.DictReader(f))
    return [(line['replay_name'].split('.')[0],  # eg asdf.SC2Replay
             int(line['player_id']),
             '.'.join(line['game_version'].split('.')[0:3]))  # eg 4.8.0.71061
            for line in lines]
