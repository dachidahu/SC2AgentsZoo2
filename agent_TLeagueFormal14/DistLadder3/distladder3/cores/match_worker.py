import copy
import uuid
from time import sleep
import time
from random import randint
import subprocess
import os
import logging

import zmq

from distladder3.utils import get_ip_address
from distladder3.utils import create_sc2_cmd
from distladder3.cores.match_server import MsgRequestStartMatchOnWorker
from distladder3.cores.match_server import MsgRespondStartMatchOnWorker
from distladder3.cores.match_server import MsgRequestSendMatchResultFromWorker
from distladder3.cores.match_server import MsgRespondSendMatchResultFromWorker
from distladder3.utils import PgnMatch


class MatchWorker(object):
  def __init__(self, match_server_ep, timeout):
    context = zmq.Context()
    context.setsockopt(zmq.TCP_KEEPALIVE, 1)
    context.setsockopt(zmq.TCP_KEEPALIVE_CNT, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
    context.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
    self.match_server_socket = context.socket(zmq.REQ)
    self.match_server_socket.connect("tcp://{}".format(match_server_ep))
    self.match_server_socket.setsockopt(zmq.SNDHWM, 4)
    self.match_server_socket.setsockopt(zmq.RCVHWM, 4)
    self.worker_id = get_ip_address() + '_' + str(uuid.uuid1())
    logging.info('Worker ID: ' + self.worker_id)
    self.timeout = timeout
    if self.timeout:
      self.poller = zmq.Poller()
      self.poller.register(self.match_server_socket, zmq.POLLIN)

  def request_start_match_on_worker(self):
    logging.info('MatchWorker: enter request_start_match_on_worker')
    request = MsgRequestStartMatchOnWorker()
    self.match_server_socket.send_pyobj(request)
    if self.timeout:
      if not self.poller.poll(self.timeout * 1000):  # timeout in milliseconds
        raise ConnectionError("request_start_match_on_worker timeout when "
                              "sending request: {}".format(request))

    response = self.match_server_socket.recv_pyobj()
    isinstance(response, MsgRespondStartMatchOnWorker)
    logging.info('MatchWorker: leave request_start_match_on_worker')
    return response

  def request_send_match_result_from_worker(self, players, result, info=None,
                                            match_id=None):
    logging.info('MatchWorker: enter request_send_match_result_from_worker')
    # create pgn match
    pgn_match = PgnMatch()
    pgn_match.event = match_id
    pgn_match.site = self.worker_id
    pgn_match.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    pgn_match.round = 1  # TODO(pengsun): any chance to get the real round?
    pgn_match.white = players[0].name
    pgn_match.black = players[1].name
    pgn_match.result = result
    # create request
    request = MsgRequestSendMatchResultFromWorker()
    request.pgn_match = pgn_match
    request.info = info
    request.match_id = match_id

    self.match_server_socket.send_pyobj(request)
    if self.timeout:
      if not self.poller.poll(self.timeout * 1000):  # timeout in milliseconds
        raise ConnectionError(
          "request_send_match_result_from_worker timeout when sending "
          "request: {}".format(request)
        )

    response = self.match_server_socket.recv_pyobj()
    assert isinstance(response, MsgRespondSendMatchResultFromWorker)
    logging.info('MatchWorker: leave request_send_match_result')
    return response

  def run_game(self, **kwargs):
    raise NotImplementedError

  def run(self, **kwargs):
    logging.info('MatchWorker: enter run')
    while True:
      time_sleep = randint(0, 5)
      try:
        self.run_game(**kwargs)
      except Exception as e:
        logging.info('error during run_game: {}'.format(e))
        time_sleep = randint(15, 30)
      logging.info('waiting {} secs...'.format(time_sleep))
      sleep(time_sleep)


class SC2MatchWorker(MatchWorker):
  """ SC2 Match Worker.

  The python binary as virtualenv trick is described here:
  https://cloud.tencent.com/developer/ask/189193
  """

  def __init__(self, match_server_ep, game_version, map, log_dir='/tmp/',
               timeout=None, game_steps_per_episode=48000):
    super(SC2MatchWorker, self).__init__(match_server_ep, timeout)
    self.log_dir = log_dir
    self.game_version = game_version
    self.map = map
    self.game_steps_per_episode = game_steps_per_episode

  def run_game(self, port):
    logging.info('SC2MatchWorker: enter run_game')
    logging.info('SC2MatchWorker: game_version {}'.format(self.game_version))

    response_start_match = self.request_start_match_on_worker()
    assert isinstance(response_start_match, MsgRespondStartMatchOnWorker)

    # Run the game (if any) to get results
    if response_start_match.match is None:
      raise ValueError('response_start_match: no new match.')
    players = list(response_start_match.match.players)
    logging.info('SC2MatchWorker.run_game: players: ' +
                 str([player.name for player in players]))
    game_dir = os.path.join(self.log_dir, response_start_match.match.match_id)
    os.mkdir(game_dir)

    result = None
    info = 'Log files: ' + game_dir
    # TODO(pengsun): trim the logics below
    tmp_players = [copy.deepcopy(p) for p in players]
    if players[0].name == players[1].name:
      tmp_players[0].name = '1-' + players[0].name
      tmp_players[1].name = '2-' + players[1].name
    if 'Default_AI' in tmp_players[0].name or 'Default_AI' in tmp_players[1].name:
      if 'Default_AI' in tmp_players[0].name:
        bot_id, agent_id = 0, 1
      else:
        bot_id, agent_id = 1, 0
      bot_level = tmp_players[bot_id].name.split('_')[-1]
      script = create_sc2_cmd(
        tmp_players[agent_id],
        'sp',
        game_dir,
        bot_level=bot_level,
        game_version=self.game_version,
        map=self.map,
        game_steps_per_episode=self.game_steps_per_episode
      )
      log_file = open(os.path.join(game_dir, tmp_players[agent_id].name + '.log'),
                      'w')
      err_file = open(os.path.join(game_dir, tmp_players[agent_id].name + '.err'),
                      'w')
      log_file.write(script + '\n')
      log_file.flush()
      child1 = subprocess.Popen(script, stdout=log_file, stderr=err_file,
                                shell=True)
      child1.wait()
      log_file.close()
      err_file.close()
      if child1.returncode != 0:
        print(tmp_players[agent_id].name + ' crushed with ' +
              str(child1.returncode), flush=True)
        result = -1
        info += ' Error:' + tmp_players[agent_id].name + ' crushed with ' + str(
          child1.returncode)
    else:
      agent_id = 0
      script = create_sc2_cmd(
        tmp_players[0],
        'host',
        game_dir,
        port=port,
        game_version=self.game_version,
        map=self.map,
        game_steps_per_episode=self.game_steps_per_episode
      )
      log_file = open(os.path.join(game_dir, tmp_players[0].name + '.log'), 'w')
      err_file = open(os.path.join(game_dir, tmp_players[0].name + '.err'), 'w')
      log_file.write(script + '\n')
      log_file.flush()
      child1 = subprocess.Popen(script, stdout=log_file, stderr=subprocess.PIPE,
                                shell=True)
      while True:
        line = child1.stderr.readline()
        if line:
          err_file.write(str(line) + '\n')
        else:
          break
        if 'Waiting for connection' in str(line):
          break

      script = create_sc2_cmd(
        tmp_players[1],
        'client',
        port=port,
        game_version=self.game_version,
        map=self.map,
        game_steps_per_episode=self.game_steps_per_episode
      )
      log_file_1 = open(os.path.join(game_dir, tmp_players[1].name + '.log'), 'w')
      err_file_1 = open(os.path.join(game_dir, tmp_players[1].name + '.err'), 'w')
      log_file_1.write(script + '\n')
      log_file_1.flush()
      child2 = subprocess.Popen(script, stdout=log_file_1, stderr=err_file_1,
                                shell=True)
      while True:
        line = child1.stderr.readline()
        if line:
          err_file.write(str(line) + '\n')
        else:
          break
      child1.wait()
      child2.wait()
      log_file.close()
      err_file.close()
      log_file_1.close()
      err_file_1.close()
      if child1.returncode != 0:
        print(tmp_players[0].name + ' crushed with ' + str(child1.returncode),
              flush=True)
        result = -1
        info += ' Error: ' + tmp_players[0].name + ' crushed with ' + str(
          child1.returncode)
      if child2.returncode != 0:
        print(tmp_players[1].name + ' crushed with ' + str(child2.returncode),
              flush=True)
        if child1.returncode != 0:
          result = 0
        else:
          result = 1
        info += ' Error: ' + tmp_players[1].name + ' crushed with ' + str(
          child2.returncode)
    if result is None:  # No player crashed
      result = self._read_result(
        os.path.join(game_dir, tmp_players[agent_id].name + '.log'))
    if agent_id == 1:  # if Default AI vs. Agent, result should be reverse
      result = -result

    # send result
    response_send_result = self.request_send_match_result_from_worker(
      players,
      result,
      info=info,
      match_id=response_start_match.match.match_id,
    )
    logging.info('response_send_result.status: {}'.format(
      response_send_result.status))

    logging.info(
      'SC2MatchClient: leave run_game, player 0 result: {}'.format(result)
     )
    return

  def _read_result(self, file_path):
    with open(file_path, 'r') as f:
      list1 = f.readlines()
    result = list1[-1].strip('\n').split(':')
    assert len(result) == 2 and result[0] == 'Result'
    return int(result[1])
