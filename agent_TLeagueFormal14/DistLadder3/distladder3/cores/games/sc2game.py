import sys
import configparser
import time
import portpicker

from pysc2 import maps
from pysc2 import run_configs
from pysc2.env import sc2_env, lan_server_sc2_env, lan_sc2_env
from s2clientprotocol import sc2api_pb2 as sc_pb

races = {
  "R": sc2_env.Race.random,
  "P": sc2_env.Race.protoss,
  "T": sc2_env.Race.terran,
  "Z": sc2_env.Race.zerg,
}

difficulties = {
  1: sc2_env.Difficulty.very_easy,
  2: sc2_env.Difficulty.easy,
  3: sc2_env.Difficulty.medium,
  4: sc2_env.Difficulty.medium_hard,
  5: sc2_env.Difficulty.hard,
  6: sc2_env.Difficulty.harder,
  7: sc2_env.Difficulty.very_hard,
  8: sc2_env.Difficulty.cheat_vision,
  9: sc2_env.Difficulty.cheat_money,
  10: sc2_env.Difficulty.cheat_insane,
}


class MyLanServerSC2Env(lan_server_sc2_env.LanServerSC2Env):
  def __init__(self,
               _only_use_kwargs=None,
               race=None,
               agent_interface_format=None,
               agent_name=None,
               visualize=False,
               step_mul=None,
               replay_dir=None,
               map_name=None,
               config_port=None,
               disable_fog=False,
               realtime=False,
               remote=None,
               crop_to_playable_area=False,
               show_cloaked=False,
               show_burrowed_shadows=False,
               show_placeholders=False,
               raw_affects_selection=True,
               use_pysc2_feature=False,
               version=None):
    run_config = run_configs.get()
    map_inst = maps.get(map_name)
    if config_port is None:  # Do not use config_port in range 15000-25000
      self._ports = sc2_env._pick_unused_ports(5)
    else:
      self._ports = [config_port] + sc2_env._pick_unused_ports(4)
    if not all(portpicker.is_port_free(p) for p in self._ports):
      sys.exit("Need 5 free ports after the config port.")

    self._sc2_procs = [
      run_config.start(extra_ports=self._ports[1:], timeout_seconds=300,
                       host='127.0.0.1', window_loc=(50, 50), version=version)]

    tcp_port = self._ports[0]
    settings = {
      "remote": remote,
      "game_version": self._sc2_procs[0].version.game_version,
      "realtime": realtime,
      "map_name": map_inst.name,
      "map_path": map_inst.path,
      "map_data": map_inst.data(run_config),
      "ports": {
        "server": {"game": self._ports[1], "base": self._ports[2]},
        "client": {"game": self._ports[3], "base": self._ports[4]},
      }
    }

    create = sc_pb.RequestCreateGame(
      realtime=settings["realtime"],
      local_map=sc_pb.LocalMap(map_path=settings["map_path"]),
      disable_fog=disable_fog)
    create.player_setup.add(type=sc_pb.Participant)
    create.player_setup.add(type=sc_pb.Participant)

    controller = self._sc2_procs[0].controller
    controller.save_map(settings["map_path"], settings["map_data"])
    controller.create_game(create)

    if remote:
      self.ssh_proc = lan_sc2_env.forward_ports(
        remote, self._sc2_procs[0].host, [settings["ports"]["client"]["base"]],
        [tcp_port, settings["ports"]["server"]["base"]])

    print("-" * 80)
    print("Join: agent_vs_agent --host %s --config_port %s" % (
    self._sc2_procs[0].host,
    tcp_port))
    print("-" * 80)

    self.tcp_conn = lan_sc2_env.tcp_server(
      lan_sc2_env.Addr(self._sc2_procs[0].host, tcp_port), settings)

    if remote:
      self.udp_sock = lan_sc2_env.udp_server(
        lan_sc2_env.Addr(self._sc2_procs[0].host,
                         settings["ports"]["client"]["game"]))

      lan_sc2_env.daemon_thread(
        lan_sc2_env.tcp_to_udp,
        (self.tcp_conn, self.udp_sock,
         lan_sc2_env.Addr(self._sc2_procs[0].host,
                          settings["ports"]["server"]["game"])))

      lan_sc2_env.daemon_thread(lan_sc2_env.udp_to_tcp,
                                (self.udp_sock, self.tcp_conn))
    self.raw = not use_pysc2_feature
    interface = self._get_interface(
      agent_interface_format=agent_interface_format,
      require_raw=True, crop_to_playable_area=crop_to_playable_area,
      show_cloaked=show_cloaked, show_burrowed_shadows=show_burrowed_shadows,
      show_placeholders=show_placeholders,
      raw_affects_selection=raw_affects_selection)
    join = sc_pb.RequestJoinGame(race=race, options=interface,
                                 player_name=agent_name)
    join.shared_port = 0  # unused
    join.server_ports.game_port = settings["ports"]["server"]["game"]
    join.server_ports.base_port = settings["ports"]["server"]["base"]
    join.client_ports.add(game_port=settings["ports"]["client"]["game"],
                          base_port=settings["ports"]["client"]["base"])
    controller.join_game(join)

    super(MyLanServerSC2Env, self).__init__(
      race=race,
      agent_interface_format=agent_interface_format,
      visualize=visualize,
      step_mul=step_mul,
      replay_dir=replay_dir,
      controller=controller,
      map_name=map_name)

  def close(self):
    super(MyLanServerSC2Env, self).close()
    if hasattr(self, "tcp_conn") and self.tcp_conn:
      self.tcp_conn.close()
    if hasattr(self, "udp_sock") and self.udp_sock:
      self.udp_sock.close()
    if hasattr(self, "ssh_proc") and self.ssh_proc:
      self.ssh_proc.terminate()
      for _ in range(5):
        if self.ssh_proc.poll() is not None:
          break
        time.sleep(1)
      if self.ssh_proc.poll() is None:
        self.ssh_proc.kill()
        self.ssh_proc.wait()


class sc2game(object):
  def __init__(self, config_file=None, game_id=None, mode='sp',
               map='AbyssalReef', crop_to_playable_area=False,
               show_cloaked=False, show_burrowed_shadows=False,
               show_placeholders=False, raw_affects_selection=True,
               replay_dir=None, port=None, bot_race='Z', difficulty=None,
               race='Z', disable_fog=False, step_mul=8, visualize=False,
               game_version='4.1.2', realtime=False, remote=None,
               game_steps_per_episode=48000, agent_name=None,
               use_pysc2_feature=False):
    '''mode: {'sp', 'host', 'client'}.
         sp for single player game. host & client for multi player game.
       realtime: only works for host.
       remote: remote agent's ip'''
    self.game_id = game_id
    self.map = map
    self.config_port = port  # only used in host and client mode
    self.difficulty = difficulty  # only used in sp mode
    self.bot_race = bot_race  # only used in sp mode
    self.step_mul = step_mul
    self.race = race
    self.disable_fog = disable_fog
    self.visualize = visualize
    self.interface_format = 'feature'
    self.screen_resolution = 64
    self.minimap_resolution = 64
    self.screen_ratio = 1.33
    self.minimap_ratio = 1
    self.camera_width_world_units = 24
    self.replay_dir = replay_dir
    self.game_version = game_version
    self.realtime = realtime
    self.remote = remote
    self.game_steps_per_episode = game_steps_per_episode
    self.agent_name = agent_name or None
    self.crop_to_playable_area = crop_to_playable_area
    self.show_cloaked = show_cloaked
    self.show_burrowed_shadows = show_burrowed_shadows
    self.show_placeholders = show_placeholders
    self.raw_affects_selection = raw_affects_selection
    self.use_pysc2_feature = use_pysc2_feature
    if config_file:
      self.load_config(config_file)
    self.screen_res = (int(self.screen_ratio * self.screen_resolution) // 4 * 4,
                       self.screen_resolution)
    self.minimap_res = (int(self.minimap_ratio * self.minimap_resolution) // 4 * 4,
                       self.minimap_resolution)
    if self.interface_format == 'feature':
      self.agent_interface_format = sc2_env.AgentInterfaceFormat(
        feature_dimensions=sc2_env.Dimensions(
          screen=self.screen_res,
          minimap=self.minimap_res),
        camera_width_world_units=self.camera_width_world_units)
    elif self.interface_format == 'rgb':
      self.agent_interface_format = sc2_env.AgentInterfaceFormat(
        rgb_dimensions=sc2_env.Dimensions(
          screen=self.screen_res,
          minimap=self.minimap_res),
        camera_width_world_units=self.camera_width_world_units)
    else:
      raise NotImplementedError
    assert mode in ['sp', 'host', 'client']
    self.mode = mode
    self.create_env(mode)

  def load_config(self, config_file):
    cf = configparser.ConfigParser()
    cf.read(config_file)
    config_dict = dict(cf.items('config'))
    if 'step_mul' in config_dict:
      self.step_mul = cf.getint('config', 'step_mul')
    if 'race' in config_dict:
      self.race = cf.get('config', 'race')
      assert self.race in races
    if 'disable_fog' in config_dict:
      self.disable_fog = cf.getboolean('config', 'disable_fog')
    if 'visualize' in config_dict:
      self.visualize = cf.getboolean('config', 'visualize')
    if 'interface_format' in config_dict:
      self.interface_format = cf.get('config', 'interface_format')
    if 'screen_resolution' in config_dict:
      self.screen_resolution = cf.getint('config', 'screen_resolution')
    if 'minimap_resolution' in config_dict:
      self.minimap_resolution = cf.getint('config', 'minimap_resolution')
    if 'screen_ratio' in config_dict:
      self.screen_ratio = cf.getfloat('config', 'screen_ratio')
    if 'minimap_ratio' in config_dict:
      self.minimap_ratio = cf.getfloat('config', 'minimap_ratio')
    if 'camera_width_world_units' in config_dict:
      self.camera_width_world_units = cf.getint('config',
                                                'camera_width_world_units')
    if 'crop_to_playable_area' in config_dict:
      self.crop_to_playable_area = cf.getboolean('config',
                                                 'crop_to_playable_area')
    if 'show_cloaked' in config_dict:
      self.show_cloaked = cf.getboolean('config',
                                                 'show_cloaked')
    if 'show_burrowed_shadows' in config_dict:
      self.show_burrowed_shadows = cf.getboolean('config',
                                                 'show_burrowed_shadows')
    if 'show_placeholders' in config_dict:
      self.show_placeholders = cf.getboolean('config',
                                                 'show_placeholders')
    if 'raw_affects_selection' in config_dict:
      self.raw_affects_selection = cf.getboolean('config',
                                                 'raw_affects_selection')
    if 'use_pysc2_feature' in config_dict:
      self.use_pysc2_feature = cf.getboolean('config',
                                             'use_pysc2_feature')

  def create_env(self, mode):
    if mode == 'sp':
      assert self.bot_race in races
      assert self.difficulty in difficulties
      save_replay_episodes = 1 if self.replay_dir else 0
      players = [sc2_env.Agent(races[self.race]),
                 sc2_env.Bot(races[self.bot_race],
                             difficulties[self.difficulty])]
      self.env = sc2_env.SC2Env(map_name=self.map,
                                players=players,
                                step_mul=self.step_mul,
                                agent_interface_format=self.agent_interface_format,
                                agent_names=[self.agent_name],
                                disable_fog=self.disable_fog,
                                visualize=self.visualize,
                                realtime=self.realtime,
                                save_replay_episodes=save_replay_episodes,
                                crop_to_playable_area=self.crop_to_playable_area,
                                show_cloaked=self.show_cloaked,
                                show_burrowed_shadows=self.show_burrowed_shadows,
                                show_placeholders=self.show_placeholders,
                                raw_affects_selection=self.raw_affects_selection,
                                use_pysc2_feature=self.use_pysc2_feature,
                                replay_dir=self.replay_dir)
    elif mode == 'host':
      self.env = MyLanServerSC2Env(race=races[self.race],
                                   agent_interface_format=self.agent_interface_format,
                                   agent_name=self.agent_name,
                                   visualize=self.visualize,
                                   disable_fog=self.disable_fog,
                                   step_mul=self.step_mul,
                                   replay_dir=self.replay_dir,
                                   map_name=self.map,
                                   config_port=self.config_port,
                                   realtime=self.realtime,
                                   remote=self.remote,
                                   version=self.game_version,
                                   crop_to_playable_area=self.crop_to_playable_area,
                                   show_cloaked=self.show_cloaked,
                                   show_burrowed_shadows=self.show_burrowed_shadows,
                                   show_placeholders=self.show_placeholders,
                                   raw_affects_selection=self.raw_affects_selection,
                                   use_pysc2_feature=self.use_pysc2_feature,
                                   )
    elif mode == 'client':
      self.env = lan_sc2_env.LanSC2Env(race=races[self.race],
                                       agent_interface_format=self.agent_interface_format,
                                       agent_name=self.agent_name,
                                       visualize=self.visualize,
                                       step_mul=self.step_mul,
                                       realtime=self.realtime,
                                       replay_dir=self.replay_dir,
                                       config_port=self.config_port,
                                       crop_to_playable_area=self.crop_to_playable_area,
                                       show_cloaked=self.show_cloaked,
                                       show_burrowed_shadows=self.show_burrowed_shadows,
                                       show_placeholders=self.show_placeholders,
                                       raw_affects_selection=self.raw_affects_selection,
                                       use_pysc2_feature=self.use_pysc2_feature,
                                       )
    else:
      raise ValueError("Not supported mode")
    self.env._episode_length = self.game_steps_per_episode

  def run(self, agent):
    import time
    """A run loop to have an agent and an environment interact."""
    total_frames = 0
    start_time = time.time()

    action_spec = self.env.action_spec()
    observation_spec = self.env.observation_spec()
    agent.setup(observation_spec[0], action_spec[0])
    timesteps = self.env.reset()
    agent.reset(timesteps[0])
    while True:
      total_frames += 1
      action = agent.step(timesteps[0])
      if timesteps[0].last():
        break
      timesteps = self.env.step([action])
    elapsed_time = time.time() - start_time
    print("Took %.3f seconds for %s steps: %.3f fps" % (
      elapsed_time, total_frames, total_frames / elapsed_time))
    result = timesteps[0].reward
    return result
