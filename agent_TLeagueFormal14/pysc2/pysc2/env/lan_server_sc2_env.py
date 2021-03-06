# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A Starcraft II environment for playing LAN games agent vs agent
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pysc2 import run_configs
from pysc2.env import sc2_env
from pysc2.lib import run_parallel


class RestartException(Exception):
    pass


class LanServerSC2Env(sc2_env.SC2Env):
    """A Starcraft II environment for playing vs humans over LAN.

    This owns a single instance, and expects to join a game hosted by some other
    script, likely play_vs_agent.py.
    """

    def __init__(self,  # pylint: disable=invalid-name
                 _only_use_kwargs=None,
                 race=None,
                 agent_interface_format=None,
                 discount=1.,
                 visualize=False,
                 step_mul=None,
                 realtime=False,
                 replay_dir=None,
                 controller=None,
                 update_game_info=False,
                 crop_to_playable_area=False,
                 show_cloaked=False,
                 show_burrowed_shadows=False,
                 show_placeholders=False,
                 raw_affects_selection=True,
                 use_pysc2_feature=True,
                 map_name=None):
        if _only_use_kwargs:
            raise ValueError(
                "All arguments must be passed as keyword arguments.")

        if agent_interface_format is None:
            raise ValueError("Please specify agent_interface_format.")

        if not race:
            race = sc2_env.Race.random

        self._num_agents = 1
        self._discount = discount
        self._step_mul = step_mul or 8
        self._realtime = realtime
        self._save_replay_episodes = 1 if replay_dir else 0
        self._replay_dir = replay_dir

        self._score_index = -1  # Win/loss only.
        self._score_multiplier = 1
        self._episode_length = 0  # No limit.

        self._map_name = map_name
        self._update_game_info = update_game_info
        self.raw = not use_pysc2_feature

        self._run_config = run_configs.get()
        self._parallel = run_parallel.RunParallel()  # Needed for multiplayer.

        self._controllers = [controller]

        interface = self._get_interface(
            agent_interface_format=agent_interface_format,
            require_raw=True, crop_to_playable_area=crop_to_playable_area,
            show_cloaked=show_cloaked,
            show_burrowed_shadows=show_burrowed_shadows,
            show_placeholders=show_placeholders,
            raw_affects_selection=raw_affects_selection)

        self._finalize([agent_interface_format], [interface], visualize)

    def _restart(self):
        # Can't restart since it's not clear how you'd coordinate that with the
        # other players.
        raise RestartException("Can't restart")

    def close(self):
        super(LanServerSC2Env, self).close()
