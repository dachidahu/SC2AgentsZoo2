from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pysc2.lib import point, UNIT_TYPEID
from s2clientprotocol import sc2api_pb2 as sc_pb, ui_pb2 as sc_ui


def cmd_with_pos(ability_id, x, y, tags, shift):
  action = sc_pb.Action()
  action.action_raw.unit_command.ability_id = ability_id
  action.action_raw.unit_command.target_world_space_pos.x = x
  action.action_raw.unit_command.target_world_space_pos.y = y
  for u_tag in tags:
    action.action_raw.unit_command.unit_tags.append(u_tag)
  action.action_raw.unit_command.queue_command = shift
  return action


def cmd_with_tar(ability_id, target_tag, tags, shift):
  action = sc_pb.Action()
  action.action_raw.unit_command.ability_id = ability_id
  action.action_raw.unit_command.target_unit_tag = target_tag
  for u_tag in tags:
    action.action_raw.unit_command.unit_tags.append(u_tag)
  action.action_raw.unit_command.queue_command = shift
  return action


def cmd_without_arg(ability_id, tags, shift):
  action = sc_pb.Action()
  action.action_raw.unit_command.ability_id = ability_id
  for u_tag in tags:
    action.action_raw.unit_command.unit_tags.append(u_tag)
  action.action_raw.unit_command.queue_command = shift
  return action


def cmd_camera(x, y):
  action = sc_pb.Action()
  action.action_raw.camera_move.center_world_space.x = x
  action.action_raw.camera_move.center_world_space.y = y
  return action


def cmd_build_lurkerden(x, y, u):
  action = sc_pb.Action()
  action.action_raw.unit_command.ability_id = 1163
  action.action_raw.unit_command.target_world_space_pos.x = x
  action.action_raw.unit_command.target_world_space_pos.y = y
  action.action_raw.unit_command.unit_tags.append(u.tag)
  return action


def noop():
  return sc_pb.Action()


def move_camera(pos):
  return cmd_camera(pos.x, pos.y)


def select_rect(select_add, screen, screen2):
  """Select units within a rectangle."""
  action = sc_pb.Action()
  select = action.action_feature_layer.unit_selection_rect
  out_rect = select.selection_screen_coord.add()
  screen_rect = point.Rect(screen, screen2)
  screen_rect.tl.assign_to(out_rect.p0)
  screen_rect.br.assign_to(out_rect.p1)
  select.selection_add = bool(select_add)
  return action


def select_many_rect(select_add, point_list):
  """Select units within many rectangles."""
  action = sc_pb.Action()
  select = action.action_feature_layer.unit_selection_rect
  for p in point_list:
    out_rect = select.selection_screen_coord.add()
    screen_rect = point.Rect(p, p)
    screen_rect.tl.assign_to(out_rect.p0)
    screen_rect.br.assign_to(out_rect.p1)
  select.selection_add = bool(select_add)
  return action


def control_group(control_group_id, ctrl, shift, alt):
  """Act on a control group, selecting, setting, etc."""
  action = sc_pb.Action()
  select = action.action_ui.control_group

  mod = sc_ui.ActionControlGroup
  if not ctrl and not shift and not alt:
    select.action = mod.Recall
  elif ctrl and not shift and not alt:
    select.action = mod.Set
  elif not ctrl and shift and not alt:
    select.action = mod.Append
  elif not ctrl and not shift and alt:
    select.action = mod.SetAndSteal
  elif not ctrl and shift and alt:
    select.action = mod.AppendAndSteal
  else:
    return  # unknown
  select.control_group_index = control_group_id
  return action


def select_u_by_pos(x, y):
  new_point = point.Point(int(x), int(y))
  return select_rect(select_add=False, screen=new_point, screen2=new_point)


def select_units_by_pos(xy_list):   ## our own defined select_units
  new_point_list = []
  for x, y in xy_list:
    new_point_list.append(point.Point(int(x), int(y)))
  return select_many_rect(select_add=False, point_list=new_point_list)


def select_units_by_tags(tags):   ## need game core to support: set raw_affect_selection to True
  action = sc_pb.Action()
  action.action_raw.unit_command.ability_id = 0
  for u_tag in tags:
    action.action_raw.unit_command.unit_tags.append(u_tag)
  return action


def select_idle_worker(ctrl, shift):
  """Select an idle worker."""
  action = sc_pb.Action()
  mod = sc_ui.ActionSelectIdleWorker
  if ctrl:
    select_worker = mod.AddAll if shift else mod.All
  else:
    select_worker = mod.Add if shift else mod.Set
  action.action_ui.select_idle_worker.type = select_worker
  return action


def select_army(shift):
  """Select the entire army."""
  action = sc_pb.Action()
  action.action_ui.select_army.selection_add = shift
  return action


def select_larva():
  """Select all larva."""
  action = sc_pb.Action()
  action.action_ui.select_larva.SetInParent()  # Adds the empty proto field.
  return action


def unload(unload_id):
  """Unload a unit from a transport/bunker/nydus/etc."""
  action = sc_pb.Action()
  action.action_ui.cargo_panel.unit_index = unload_id
  return action


def build_queue(build_queue_id):
  """Cancel a unit in the build queue."""
  action = sc_pb.Action()
  action.action_ui.production_panel.unit_index = build_queue_id
  return action


def cmd_screen_ui(ability_id, queued, screen):
  """Do a command that needs a point on the screen."""
  action = sc_pb.Action()
  action_cmd = action.action_feature_layer.unit_command
  action_cmd.ability_id = ability_id
  action_cmd.queue_command = queued
  # screen.assign_to(action_cmd.target_screen_coord)
  action_cmd.target_screen_coord.x = int(screen[0])
  action_cmd.target_screen_coord.y = int(screen[1])
  return action


def cmd_screen_raw(ability_id, queued, tags, world_pos):
  return cmd_with_pos(ability_id=ability_id, x=world_pos[0], y=world_pos[1],
                      tags=tags, shift=queued)


def cmd_quick_ui(ability_id, queued):
  """Do a quick command like 'Stop' or 'Stim'."""
  action = sc_pb.Action()
  action_cmd = action.action_feature_layer.unit_command
  action_cmd.ability_id = ability_id
  action_cmd.queue_command = queued
  return action


def cmd_quick_raw(ability_id, queued, tags):
  # if train, only train one larva (4.7.1 seems already fixed the bug)
  # ab_name = ZERG_ABILITIES[z_ab_map[ability_id][0]][0]
  # if ab_name in z_train_tar_map:
  #   for tag, tp in zip(tags, types):
  #     if tp == UNIT_TYPEID.ZERG_LARVA.value:
  #       return cmd_without_arg(ability_id=ability_id, tags=[tag], shift=queued)
  # if morph, only morph one unit (4.7.1 seems already fixed the bug)
  # if ab_name in z_morph_tar_map:
  #   for tag, tp in zip(tags, types):
  #     if tp == z_morph_tar_map[ab_name][0]:
  #       return cmd_without_arg(ability_id=ability_id, tags=[tag], shift=queued)
  return cmd_without_arg(ability_id=ability_id, tags=tags, shift=queued)


def cmd_unit_raw(ability_id, queued, tags, target_tag):
  return cmd_with_tar(ability_id=ability_id, target_tag=target_tag, tags=tags, shift=queued)
