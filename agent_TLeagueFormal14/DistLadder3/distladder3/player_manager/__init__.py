import os
from os import path
import logging
from copy import deepcopy


CONFIG_TMPL = (
  "[config]\n"
  "chkpoints_root_dir={}\n"
  "checkpoint_sub_dir={}\n"
  "n_v={}\n"
  "model_criterion={}\n"
  "nash_prob_filename={}\n"
  "model_filename={}\n"
  "policy_type={}\n"
  "verbose=1\n"
)
CONFIG_TMPL_DICT = {
  "chkpoints_root_dir": None,
  "checkpoint_sub_dir": None,
  "n_v": 1,
  "model_criterion": None,
  "nash_prob_filename": None,
  "model_filename": None,
  "policy_type": None,
  "verbose": 1
}
CONFIG_FILE_TMPL = "agent_config_{}.ini"
CONFIG_FILE_TMPL_V2 = "{}_agent_config_{}.ini"


def _get_cur_model_filenames(chkpoints_root_dir):
  return [
    path.basename(f) for f in os.listdir(chkpoints_root_dir)
    if '.model' in f and path.isfile(path.join(chkpoints_root_dir, f))
  ]


def _fill_agent_config_str(config_tmpl, kvs):
  config_filled = ""
  for line in config_tmpl.split("\n"):
    r = line.split('=')
    if len(r) != 2:
      newline = line + "\n"
    else:
      k, v = r[0], r[1]
      # overwrite with kvs passed in (if any)
      if k in kvs:
        v = kvs[k]
      # translate to the real empty
      if v == '{}':
        v = ''
      newline = "{}={}\n".format(k, v)
    config_filled += newline
  return config_filled


def _write_agent_config(agent_config_kvs,
                        i_cfg,
                        output_configs_dir):
  # write the config
  config_fn = CONFIG_FILE_TMPL.format(i_cfg + 1)
  config_path = path.join(output_configs_dir, config_fn)
  logging.info('iter {}: writing to {}'.format(i_cfg, config_path))
  with open(config_path, 'wt') as f:
    f.write(_fill_agent_config_str(CONFIG_TMPL, agent_config_kvs))
    f.flush()


def _write_agent_config_v2(agent_config_kvs,
                           model_basename,
                           i_cfg,
                           output_configs_dir):
  # write the config
  config_fn = CONFIG_FILE_TMPL_V2.format(model_basename, i_cfg + 1)
  config_path = path.join(output_configs_dir, config_fn)
  logging.info('iter {}: writing to {}'.format(i_cfg, config_path))
  with open(config_path, 'wt') as f:
    f.write(_fill_agent_config_str(CONFIG_TMPL, agent_config_kvs))
    f.flush()
  return config_path


def _write_agent_config_v3(agent_config_kvs,
                           model_basename,
                           i_cfg,
                           output_configs_dir):
  # reconstruct the config dict
  cfg = deepcopy(CONFIG_TMPL_DICT)
  cfg.update(agent_config_kvs)  # union semantics
  # write the config
  config_fn = CONFIG_FILE_TMPL_V2.format(model_basename, i_cfg + 1)
  config_path = path.join(output_configs_dir, config_fn)
  logging.info('iter {}: writing to {}'.format(i_cfg, config_path))
  with open(config_path, 'wt') as f:
    # write header
    f.write("[config]\n")
    # write key-value for each line
    for k, v in cfg.items():
      f.write("{}={}\n".format(k, v if v is not None else ""))
    f.flush()
  return config_path