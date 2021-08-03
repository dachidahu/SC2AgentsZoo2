from os import path
import os


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
CONFIG_FILE_TMPL = "{}_agent_config.ini"


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


def _write_agent_config_(agent_config_kvs,
                         model_basename,
                         output_configs_dir):
  # write the config
  config_fn = CONFIG_FILE_TMPL.format(model_basename)
  config_path = path.join(output_configs_dir, config_fn)
  print('writing to {}'.format(config_path), flush=True)
  with open(config_path, 'wt') as f:
    f.write(_fill_agent_config_str(CONFIG_TMPL, agent_config_kvs))
    f.flush()
  return config_path


def _get_cur_model_filenames(chkpoints_root_dir):
  return [
    path.basename(f) for f in os.listdir(chkpoints_root_dir)
    if '.model' in f and path.isfile(path.join(chkpoints_root_dir, f))
  ]


if __name__ == '__main__':
  chkpoints_root_dir = '/Users/pengsun/code/DistLadder3/distladder3/bin/tmp_ccc'
  output_configs_dir = '/Users/pengsun/code/DistLadder3/distladder3/bin/tmp_ccc'
  agent_config_kvs = {
    'chkpoints_root_dir': chkpoints_root_dir,
    'model_criterion': 'spec',
    'model_filename': None,
    'n_v': 17,
    'policy_type': 'tpolicies.new_actions.MNet.mnet'
  }

  model_filenames = _get_cur_model_filenames(chkpoints_root_dir)
  for model_fn in model_filenames:
    model_basename = path.splitext(model_fn)[0]
    kvs = agent_config_kvs
    kvs['model_filename'] = model_fn
    print('writing cfg {}'.format(kvs))
    _write_agent_config_(
      agent_config_kvs=kvs,
      model_basename=model_basename,
      output_configs_dir=output_configs_dir
    )
