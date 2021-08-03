#!/usr/bin/python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import configparser
import os
from os.path import splitext
from os import path
import pickle
import importlib

import numpy as np
import joblib

from arena.agents.agt_int_wrapper import AgtIntWrapper
from arena.agents.base_agent import BaseAgent as ArenaBaseAgent
from pysc2.agents.base_agent import BaseAgent
from pysc2.lib.typeenums import ABILITY_ID
from tleague.actors.agent import PGAgent
from tleague.utils import import_module_or_data
import tleague.envs.sc2.create_sc2_envs as tleague_sc2_envs


def _read_nash_prob_file(nash_prob_path):
  print('reading nash probability from {}'.format(nash_prob_path))
  d = {}
  with open(nash_prob_path, 'rt') as f:
    for line in f.readlines():
      if line.strip():
        model_fn, prob = line.split(' ')
        d[str(model_fn)] = float(prob)
  return d


def const_gen(x, print_info=''):
  while True:
    if print_info:
      print(print_info)
    yield x


def sample_gen(filenames, probs, verbose=1):
  while True:
    filename = np.random.choice(filenames, p=probs)
    if verbose >= 1:
      print('len(probs): {}'.format(len(probs)))
      print('probs: {}'.format(probs))
      print('sampled model filename: {}'.format(filename))
    yield filename


def _parse_checkpoint_dir(chkpoints_root_dir, checkpoint_sub_dir='', model_filename='',
                          nash_prob_filename='', model_criterion='latest',
                          verbose=1):
  """ parse checkpoint dir

  :param chkpoints_root_dir: e.g., uuu_chkpoints/
  :param checkpoint_sub_dir: e.g., checkpoint_yyyymmddhhmmss
  :param model_criteria: {'latest'|'nash'|'model'|'Model'}
  :return: model_filename from which the NN loads params
  """
  # TODO(pengsun): use a unified filename.dict for both latest and Nash Prob
  if verbose >= 1:
    print('use model_criterion: {}'.format(model_criterion))
  if model_criterion == 'latest':
    # get player model filenames
    filename_list_path = path.join(chkpoints_root_dir, checkpoint_sub_dir,
                                   'filename.list')
    with open(filename_list_path, 'rt') as f:
      model_filenames = [line.strip() for line in f
                         if line.strip().endswith(".model")]
    # thanks to our name conventions, the  model_filename looks like
    # "aaaa:bbbb_YYYYMMDDHHMM.model". just sort it according to the timestamp
    # so that the last one is the latest one
    model_filenames.sort(key=lambda f: splitext(f)[0].split('_')[1])
    model_filename = model_filenames[-1]
    print_info = ''
    if verbose >= 1:
      print_info = 'the latest model filename: {}'.format(model_filename)
    return const_gen(model_filename, print_info)
  elif model_criterion == 'nash':
    model_filename_to_prob = _read_nash_prob_file(
      path.join(chkpoints_root_dir, checkpoint_sub_dir, nash_prob_filename)
    )
    model_filenames = list(model_filename_to_prob.keys())
    probs = list(model_filename_to_prob.values())
    # ** sample the model_filename from Nash Probability **
    probs = np.array(probs)
    probs = probs / probs.sum()
    return sample_gen(model_filenames, probs, verbose)
  elif model_criterion in ['model', 'Model', 'spec']:
    print_info = '' 
    if verbose >= 1:
      print_info = 'Use model filename: {}'.format(model_filename)
    return const_gen(model_filename, print_info)
  else:
    raise ValueError('Unknown model_criterion {}'.format(model_criterion))


class AbandonNoneAgtIntWrapper(AgtIntWrapper):
  def step(self, obs):
    ArenaBaseAgent.step(self, obs)
    obs = self.inter.obs_trans(obs)
    if (self.steps - 1) % self.step_mul == 0:
      if obs is None:
        #print('agt steps {}: obs is None, perform action None'.format(
        #  self.steps), flush=True)
        self.act = None  # arbitrary
      else:
        self.act = self.agent.step(obs)
    act = self.inter.act_trans(self.act)
    return act


class StatAgtIntWrapper(AgtIntWrapper):
  """Statistics for all actions counting."""
  def __init__(self, agt, inter):
    super(StatAgtIntWrapper, self).__init__(agt, inter)
    self._reset_stat()

  def _reset_stat(self):
    self._info = {}
    self._ab_dict = dict([(ab.value, 0) for ab in ABILITY_ID])
    self._SeqLevDist = None

  def _action_stat(self, raw_act, actions, done=False):
    for action in raw_act:
      if action.action_raw.unit_command.ability_id in self._ab_dict:
        self._ab_dict[action.action_raw.unit_command.ability_id] += 1
    if done:
      for k, v in self._ab_dict.items():
        if v > 0:
          self._info[ABILITY_ID(k).name] = v

  def _obs_stat(self, raw_obs, obs):
    required_keys = ['Z_BUILD_ORDER', 'Z_BUILD_ORDER_COORD',
                     'IMM_BUILD_ORDER', 'IMM_BUILD_ORDER_COORD']
    key = 'agt-zstat-dist'
    if isinstance(obs, dict) and set(required_keys) <= set(obs):
      if np.sum(obs['Z_BUILD_ORDER']) > 0:
        if self._SeqLevDist is None:
          self._SeqLevDist = tleague_sc2_envs.SeqLevDist_with_Coord(
            obs['Z_BUILD_ORDER'], obs['Z_BUILD_ORDER_COORD'])
        self._info[key] = self._SeqLevDist.lev_dist(obs['IMM_BUILD_ORDER'],
                                                    obs['IMM_BUILD_ORDER_COORD'])
    else:
      print(f"WARN: cannot find the fields {required_keys} for agent")

  def reset(self, obs, inter_kwargs={}):
    super(StatAgtIntWrapper, self).reset(obs, inter_kwargs=inter_kwargs)
    self._reset_stat()

  def step(self, raw_obs):
    super(AgtIntWrapper, self).step(raw_obs)
    done = raw_obs.last()
    obs = self.inter.obs_trans(raw_obs)
    if (self.steps - 1) % self.step_mul == 0:
      if obs is None:
        act = None  # arbitrary
      else:
        self._obs_stat(raw_obs, obs)
        act = self.agent.step(obs)
    raw_act = self.inter.act_trans(act)
    self._action_stat(raw_act, act, done)
    if done:
      root_interf = self.inter.unwrapped()
      if not hasattr(root_interf, 'cur_zstat_fn'):
        print("Cannot find the field 'cur_zstat_fn' for the root interface {}".format(root_interf))
      else:
        self._info['agt-zstat'] = root_interf.cur_zstat_fn
      print(f'Info: {self._info}', flush=True)
    return raw_act


class Agent(BaseAgent):
  """ TLeague Agent, for agent_TLeagueFormal14

  On each episode start, it uses a fixed model.
  It derives from PySC2.agents.BaseAgent and aggregates an Interface and a
  PPOAgent. The Interface version can be specified in the config file """

  def __init__(self, agent_config):
    super(Agent, self).__init__()
    # parse agent config ini
    print('reading config from {}'.format(agent_config))
    agt_cfg = configparser.ConfigParser()
    agt_cfg.read(agent_config)
    ###
    # basic config
    ###
    self._policy = import_module_or_data(agt_cfg.get('config', 'policy_type'))
    self._chkpoints_root_dir = agt_cfg.get('config', 'chkpoints_root_dir')
    self._use_gpu_id = agt_cfg.getint('config', 'use_gpu_id', fallback=-1)
    ###
    # interface defined in tleague and the related configs
    ###
    self._zstat_zeroing_prob = agt_cfg.getfloat('config', 'zstat_zeroing_prob',
                                                fallback=0.0)
    self._zstat_category = agt_cfg.get('config', 'zstat_category',
                                       fallback=None)
    self._interface_func_name = agt_cfg.get('config',
                                            'tleague_interface_func_name')
    self._stat = agt_cfg.getboolean('config', 'stat', fallback=False)
    inter_config = {}
    inter_config['zstat_data_src'] = agt_cfg.get(
      'config', 'tleague_interface_config.zstat_data_src')
    inter_config['mmr'] = agt_cfg.getint('config',
                                         'tleague_interface_config.mmr')
    inter_config['dict_space'] = agt_cfg.getboolean(
      'config', 'tleague_interface_config.dict_space')
    inter_config['max_bo_count'] = agt_cfg.getint(
      'config',
      'tleague_interface_config.max_bo_count'
    )
    inter_config['max_bobt_count'] = agt_cfg.getint(
      'config',
      'tleague_interface_config.max_bobt_count'
    )
    inter_config['correct_pos_radius'] = agt_cfg.getfloat(
      'config',
      'tleague_interface_config.correct_pos_radius'
    )
    inter_config['zmaker_version'] = agt_cfg.get(
      'config',
      'tleague_interface_config.zmaker_version'
    )
    inter_config['inj_larv_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.inj_larv_rule'
    )
    inter_config['mof_lair_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.mof_lair_rule',
    )
    inter_config['ban_zb_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.ban_zb_rule',
    )
    inter_config['ban_rr_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.ban_rr_rule',
    )
    inter_config['hydra_spire_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.hydra_spire_rule',
    )
    inter_config['overseer_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.overseer_rule',
    )
    inter_config['expl_map_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.expl_map_rule',
    )
    inter_config['baneling_rule'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.baneling_rule',
    )
    inter_config['correct_building_pos'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.correct_building_pos'
    )
    inter_config['add_cargo_to_units'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.add_cargo_to_units'
    )
    inter_config['crop_to_playable_area'] = agt_cfg.getboolean(
      'config',
      'tleague_interface_config.crop_to_playable_area'
    )
    # enforcing squared output_map_size
    tmp = agt_cfg.getint('config', 'tleague_interface_config.output_map_size')
    inter_config['output_map_size'] = (tmp, tmp)
    inter_config['verbose'] = agt_cfg.getint('config',
                                             'tleague_interface_config.verbose')
    # model loading related configs
    self._model_criterion = agt_cfg.get('config', 'model_criterion',
                                        fallback='latest')
    if self._model_criterion in ['model', 'Model', 'spec']:
      self._model_filename = agt_cfg.get('config', 'model_filename')
      self._checkpoint_sub_dir = ''
    else:
      self._model_filename = ''
      self._checkpoint_sub_dir = agt_cfg.get('config', 'checkpoint_sub_dir')
    if self._model_criterion == 'nash':
      self._nash_prob_filename = agt_cfg.get('config', 'nash_prob_filename')
    else:
      self._nash_prob_filename = ''

    # verbosity
    self._verbose = agt_cfg.getint('config', 'verbose', fallback=1)
    ###
    # policy_config
    ###
    pc = {}
    pc['test'] = agt_cfg.getboolean('config', 'policy_config.test')
    pc['use_loss_type'] = agt_cfg.get('config', 'policy_config.use_loss_type')
    pc['use_value_head'] = agt_cfg.getboolean('config',
                                              'policy_config.use_value_head')
    pc['use_self_fed_heads'] = agt_cfg.getboolean(
      'config', 'policy_config.use_self_fed_heads'
    )
    pc['use_lstm'] = agt_cfg.getboolean('config', 'policy_config.use_lstm')
    pc['lstm_layer_norm'] = agt_cfg.getboolean('config',
                                               'policy_config.lstm_layer_norm')
    pc['lstm_cell_type'] = agt_cfg.get('config', 'policy_config.lstm_cell_type')
    pc['forget_bias'] = agt_cfg.getfloat('config', 'policy_config.forget_bias',
                                         fallback=1.0)
    pc['nlstm'] = agt_cfg.getint('config', 'policy_config.nlstm')
    pc['hs_len'] = agt_cfg.getint('config', 'policy_config.hs_len')
    pc['lstm_duration'] = agt_cfg.getint('config',
                                         'policy_config.lstm_duration')
    pc['n_v'] = agt_cfg.getint('config', 'policy_config.n_v')
    pc['use_base_mask'] = agt_cfg.getboolean('config',
                                             'policy_config.use_base_mask')
    pc['vec_embed_version'] = agt_cfg.get('config',
                                          'policy_config.vec_embed_version')
    pc['last_act_embed_version'] = agt_cfg.get(
      'config',
      'policy_config.last_act_embed_version'
    )
    pc['zstat_embed_version'] = agt_cfg.get('config',
                                            'policy_config.zstat_embed_version')
    pc['zstat_index_base_wavelen'] = agt_cfg.getfloat(
      'config',
      'policy_config.zstat_index_base_wavelen',
      fallback=-1.0,
    )
    pc['temperature'] = agt_cfg.getfloat('config', 'policy_config.temperature')
    pc['gather_batch'] = agt_cfg.getboolean('config',
                                            'policy_config.gather_batch')
    pc['trans_version'] = agt_cfg.get('config', 'policy_config.trans_version')
    pc['embed_for_action_heads'] = agt_cfg.get(
      'config', 'policy_config.embed_for_action_heads'
    )
    pc['ab_n_blk'] = agt_cfg.getint('config', 'policy_config.ab_n_blk')
    pc['ab_n_skip'] = agt_cfg.getint('config', 'policy_config.ab_n_skip')
    pc['use_astar_glu'] = agt_cfg.getboolean('config',
                                             'policy_config.use_astar_glu')
    pc['use_astar_func_embed'] = agt_cfg.getboolean(
      'config',
      'policy_config.use_astar_func_embed'
    )
    pc['pos_logits_mode'] = agt_cfg.get('config',
                                        'policy_config.pos_logits_mode')
    pc['pos_n_blk'] = agt_cfg.getint('config', 'policy_config.pos_n_blk')
    pc['pos_n_skip'] = agt_cfg.getint('config', 'policy_config.pos_n_skip')
    # other policy configs that must be set when performing step-by-step unroll
    pc['rollout_len'] = 1
    pc['batch_size'] = 1

    self._inter = getattr(tleague_sc2_envs, self._interface_func_name)(
      **inter_config
    )
    self.model_gen = _parse_checkpoint_dir(self._chkpoints_root_dir,
                                           self._checkpoint_sub_dir,
                                           self._model_filename,
                                           self._nash_prob_filename,
                                           self._model_criterion,
                                           self._verbose)

    # create the internal PGAgent
    ob_space = self._inter.observation_space
    ac_space = self._inter.action_space
    if self._verbose >= 1:
      print('agent_TLeagueFormal12.__init__')
      print('ob_space', ob_space)
      print('ac_space', ac_space)
    self._pg_agt = PGAgent(self._policy, ob_space, ac_space, scope_name='self',
                           policy_config=pc, use_gpu_id=self._use_gpu_id)
    self._load_next_model_for_pg_agt() # load an available model immediately


    if self._use_gpu_id >= 0:
      # always do the tf graph pre-build to eliminate the delay on game start
      # NOTE: as for tf 1.15, this pre-build tricks only works for GPU, NOT
      # works for CPU, no idea why
      self._pg_agt.step(ob_space.sample())
    # then create the internal wrapped agent based on the PPOAgent
    if self._stat:
      self._agent = StatAgtIntWrapper(self._pg_agt, self._inter)
    else:
      self._agent = AbandonNoneAgtIntWrapper(self._pg_agt, self._inter)

  def _load_next_model_for_pg_agt(self):
    model_fn = next(self.model_gen)
    model_path = os.path.join(self._chkpoints_root_dir, model_fn)
    print("_load_next_model_for_pg_agt: loading model from {}".format(
      model_path), flush=True)
    model = joblib.load(model_path)
    if self._model_criterion == 'model':
      self._pg_agt.load_model(model)
    else:
      np_params = model.model
      self._pg_agt.load_model(np_params)

  def reset(self, obs):
    super(Agent, self).reset()
    # reset Interface
    obs_high = self._inter.reset(
      obs,
      zeroing_prob=self._zstat_zeroing_prob,  # zstat zeroing probability
      zstat_category=self._zstat_category,  # zstat category
      distrib=None  # None means uniform sampling
    )
    # reset
    self._pg_agt.reset(obs_high)
    if self._model_criterion == 'nash':
      # nash could sample another model; otherwise a constant model
      self._load_next_model_for_pg_agt()
    # NOTE(pengsun): do NOT call _agent.reset(), as PPOAgent has no setup()
    # method. This is fine, as all the reset() routines have been done above.
    #self._agent.reset(obs)
    print('done reset', flush=True)

  def step(self, obs):
    if obs.observation.game_loop % 100 == 0:
      print(obs.observation.game_loop, flush=True)
    return self._agent.step(obs)
