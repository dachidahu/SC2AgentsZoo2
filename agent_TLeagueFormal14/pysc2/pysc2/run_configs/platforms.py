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
"""Configs for how to run SC2 from a normal install on various platforms."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
from absl import logging
import os
import platform
import subprocess
import sys

from absl import flags

from pysc2.lib import sc_process
from pysc2.run_configs import lib

# https://github.com/Blizzard/s2client-proto/blob/master/buildinfo/versions.json
# Generate with bin/gen_versions.py
VERSIONS = {ver.game_version: ver for ver in [
    lib.Version("3.16.1", 55958, "5BD7C31B44525DAB46E64C4602A81DC2", None),
    lib.Version("3.17.0", 56787, "DFD1F6607F2CF19CB4E1C996B2563D9B", None),
    lib.Version("3.17.1", 56787, "3F2FCED08798D83B873B5543BEFA6C4B", None),
    lib.Version("3.17.2", 56787, "C690FC543082D35EA0AAA876B8362BEA", None),
    lib.Version("3.18.0", 57507, "1659EF34997DA3470FF84A14431E3A86", None),
    lib.Version("3.19.0", 58400, "2B06AEE58017A7DF2A3D452D733F1019", None),
    lib.Version("3.19.1", 58400, "D9B568472880CC4719D1B698C0D86984", None),
    lib.Version("4.0.0", 59587, "9B4FD995C61664831192B7DA46F8C1A1", None),
    lib.Version("4.0.2", 59587, "B43D9EE00A363DAFAD46914E3E4AF362", None),
    lib.Version("4.1.0", 60196, "1B8ACAB0C663D5510941A9871B3E9FBE", None),
    lib.Version("4.1.1", 60321, "5C021D8A549F4A776EE9E9C1748FFBBC", None),
    lib.Version("4.1.2", 60321, "33D9FE28909573253B7FC352CE7AEA40", None),
    lib.Version("4.2.0", 62347, "C0C0E9D37FCDBC437CE386C6BE2D1F93", None),
    lib.Version("4.2.1", 62848, "29BBAC5AFF364B6101B661DB468E3A37", None),
    lib.Version("4.2.2", 63454, "3CB54C86777E78557C984AB1CF3494A0", None),
    lib.Version("4.3.0", 64469, "C92B3E9683D5A59E08FC011F4BE167FF", None),
    lib.Version("4.3.1", 65094, "E5A21037AA7A25C03AC441515F4E0644", None),
    lib.Version("4.3.2", 65384, "B6D73C85DFB70F5D01DEABB2517BF11C", None),
    lib.Version("4.4.0", 65895, "BF41339C22AE2EDEBEEADC8C75028F7D", None),
    lib.Version("4.4.1", 66668, "C094081D274A39219061182DBFD7840F", None),
    lib.Version("4.5.0", 67188, "2ACF84A7ECBB536F51FC3F734EC3019F", None),
    lib.Version("4.5.1", 67188, "6D239173B8712461E6A7C644A5539369", None),
    lib.Version("4.6.0", 67926, "7DE59231CBF06F1ECE9A25A27964D4AE", None),
    lib.Version("4.6.1", 67926, "BEA99B4A8E7B41E62ADC06D194801BAB", None),
    lib.Version("4.6.2", 69232, "B3E14058F1083913B80C20993AC965DB", None),
    lib.Version("4.7.0", 70154, "8E216E34BC61ABDE16A59A672ACB0F3B", None),
    lib.Version("4.7.1", 70154, "94596A85191583AD2EBFAE28C5D532DB", None),
    lib.Version("4.8.0", 71061, "760581629FC458A1937A05ED8388725B", None),
    lib.Version("4.8.1", 71523, "FCAF3F050B7C0CC7ADCF551B61B9B91E", None),
    lib.Version("4.8.2", 71663, "FE90C92716FC6F8F04B74268EC369FA5", None),
    lib.Version("4.8.3", 72282, "0F14399BBD0BA528355FF4A8211F845B", None),
    lib.Version("4.8.4", 73286, "CD040C0675FD986ED37A4CA3C88C8EB5", None),
    lib.Version("4.8.6", 73620, "AA18FEAD6573C79EF707DF44ABF1BE61", None),
    lib.Version("4.9.0", 74071, "70C74A2DCA8A0D8E7AE8647CAC68ACCA", None),
    lib.Version("4.9.1", 74456, "218CB2271D4E2FA083470D30B1A05F02", None),
    lib.Version("4.9.2", 74741, "614480EF79264B5BD084E57F912172FF", None),
    lib.Version("4.9.3", 75025, "C305368C63621480462F8F516FB64374", None),
    lib.Version("4.10.0", 75689, "B89B5D6FA7CBF6452E721311BFBC6CB2", None),
    lib.Version("4.10.1", 75800, "DDFFF9EC4A171459A4F371C6CC189554", None),
]}

flags.DEFINE_enum("sc2_version", None, sorted(VERSIONS.keys()),
                  "Which version of the game to use.")
FLAGS = flags.FLAGS


def _get_version(game_version):
  if game_version.count(".") == 1:
    game_version += ".0"
  if game_version not in VERSIONS:
    raise ValueError("Unknown game version: %s. Known versions: %s" % (
        game_version, sorted(VERSIONS.keys())))
  return VERSIONS[game_version]


def _read_execute_info(path, parents):
  """Read the ExecuteInfo.txt file and return the base directory."""
  path = os.path.join(path, "StarCraft II/ExecuteInfo.txt")
  if os.path.exists(path):
    with open(path, "rb") as f:  # Binary because the game appends a '\0' :(.
      for line in f:
        parts = [p.strip() for p in line.decode("utf-8").split("=")]
        if len(parts) == 2 and parts[0] == "executable":
          exec_path = parts[1].replace("\\", "/")  # For windows compatibility.
          for _ in range(parents):
            exec_path = os.path.dirname(exec_path)
          return exec_path


class LocalBase(lib.RunConfig):
  """Base run config for public installs."""

  def __init__(self, base_dir, exec_name, cwd=None, env=None):
    base_dir = os.path.expanduser(base_dir)
    cwd = cwd and os.path.join(base_dir, cwd)
    super(LocalBase, self).__init__(
        replay_dir=os.path.join(base_dir, "Replays"),
        data_dir=base_dir, tmp_dir=None, cwd=cwd, env=env)
    self._exec_name = exec_name

  def start(self, version=None, **kwargs):
    """Launch the game."""
    if not os.path.isdir(self.data_dir):
      raise sc_process.SC2LaunchError(
          "Expected to find StarCraft II installed at '%s'. If it's not "
          "installed, do that and run it once so auto-detection works. If "
          "auto-detection failed repeatedly, then set the SC2PATH environment "
          "variable with the correct location." % self.data_dir)

    version = version or FLAGS.sc2_version
    if isinstance(version, lib.Version) and not version.data_version:
      # This is for old replays that don't have the embedded data_version.
      version = _get_version(version.game_version)
    elif isinstance(version, str):
      version = _get_version(version)
    elif not version:
      versions_dir = os.path.join(self.data_dir, "Versions")
      version_prefix = "Base"
      versions_found = [int(v[len(version_prefix):])
                        for v in os.listdir(versions_dir)
                        if v.startswith(version_prefix)]
      if not versions_found:
        raise sc_process.SC2LaunchError(
            "No SC2 Versions found in %s" % versions_dir)
      build_version = max(versions_found)
      version = lib.Version(None, build_version, None, None)
    if version.build_version < VERSIONS["3.16.1"].build_version:
      raise sc_process.SC2LaunchError(
          "SC2 Binaries older than 3.16.1 don't support the api.")
    exec_path = os.path.join(
        self.data_dir, "Versions/Base%s" % version.build_version,
        self._exec_name)

    if not os.path.exists(exec_path):
      raise sc_process.SC2LaunchError("No SC2 binary found at: %s" % exec_path)

    return sc_process.StarcraftProcess(
        self, exec_path=exec_path, version=version, **kwargs)


class Windows(LocalBase):
  """Run on Windows."""

  def __init__(self):
    exec_path = (os.environ.get("SC2PATH") or
                 _read_execute_info(os.path.expanduser("~/Documents"), 3) or
                 "C:/Program Files (x86)/StarCraft II")
    super(Windows, self).__init__(exec_path, "SC2_x64.exe", "Support64")

  @classmethod
  def priority(cls):
    if platform.system() == "Windows":
      return 1


class Cygwin(LocalBase):
  """Run on Cygwin. This runs the windows binary within a cygwin terminal."""

  def __init__(self):
    super(Cygwin, self).__init__(
        os.environ.get("SC2PATH",
                       "/cygdrive/c/Program Files (x86)/StarCraft II"),
        "SC2_x64.exe", "Support64")

  @classmethod
  def priority(cls):
    if sys.platform == "cygwin":
      return 1


class MacOS(LocalBase):
  """Run on MacOS."""

  def __init__(self):
    exec_path = (os.environ.get("SC2PATH") or
                 _read_execute_info(os.path.expanduser(
                     "~/Library/Application Support/Blizzard"), 6) or
                 "/Applications/StarCraft II")
    super(MacOS, self).__init__(exec_path, "SC2.app/Contents/MacOS/SC2")

  @classmethod
  def priority(cls):
    if platform.system() == "Darwin":
      return 1


class Linux(LocalBase):
  """Config to run on Linux."""

  known_mesa = [  # In priority order
      "libOSMesa.so",
      "libOSMesa.so.8",  # Ubuntu 16.04
      "libOSMesa.so.6",  # Ubuntu 14.04
  ]

  def __init__(self):
    base_dir = os.environ.get("SC2PATH", "~/StarCraftII")
    base_dir = os.path.expanduser(base_dir)
    env = copy.deepcopy(os.environ)
    env["LD_LIBRARY_PATH"] = ":".join(filter(None, [
        os.environ.get("LD_LIBRARY_PATH"),
        os.path.join(base_dir, "Libs/")]))
    super(Linux, self).__init__(base_dir, "SC2_x64", env=env)

  @classmethod
  def priority(cls):
    if platform.system() == "Linux":
      return 1

  def start(self, **kwargs):
    extra_args = kwargs.pop("extra_args", [])

    # Figure out whether the various GL libraries exist since SC2 sometimes
    # fails if you ask to use a library that doesn't exist.
    libs = subprocess.check_output(["/sbin/ldconfig", "-p"]).decode()
    libs = {lib.strip().split()[0] for lib in libs.split("\n") if lib}
    if "libEGL.so" in libs:  # Prefer hardware rendering.
      extra_args += ["-eglpath", "libEGL.so"]
    else:
      for mesa_lib in self.known_mesa:  # Look for a software renderer.
        if mesa_lib in libs:
          extra_args += ["-osmesapath", mesa_lib]
          break
      else:
        logging.info("No GL library found, so RGB rendering will be disabled. "
                     "For software rendering install libosmesa.")

    return super(Linux, self).start(extra_args=extra_args, **kwargs)
