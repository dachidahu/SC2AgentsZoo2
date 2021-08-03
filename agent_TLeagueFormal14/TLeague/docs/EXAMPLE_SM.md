# Examples that Run in a Single Machine

## Pong-2p
Pong-2p is a a simple two-agent competitive game for pong.
For each agent,
the observation is a (84, 84, 4) stacked image of screen pixels,
and the action is Discrete(6).
See Appendix I of https://arxiv.org/abs/1907.09467

Pong-2p is good for sanity check.
See the following examples for training with Pong-2p:
* [SelfPlay+PPO](EXAMPLE_PONG2P_SP_PPO.md)

## StarCraft II
See the following:
* [SelfPlay+PPO2](EXAMPLE_SC2_SP_PPO2.md)
* [SelfPlay+PPO+InfServer](EXAMPLE_SC2_SP_PPO_INFSERVER.md)
* [SelfPlay+Vtrace](EXAMPLE_SC2_SP_VTRACE.md)

TODO: examples for Imitation Learning?

## For ViZDoom
See the following:
* [SelfPlay+PPO](EXAMPLE_VD_SP_PPO.md)

## For Pommerman
See the following:
* [PFSP+PPO]

## Terminology:
* `unroll_length`: how long the trajectory is when computing the RL Value Function using bootstrap. It must be a multiple of `batch_size`.
* `rollout_length`: the length for RNN BPTT. `rollout_length`= `rollout_len` in the `policy_config`.
* `rm_size`: size for Replay Memory. It must be a multiple of `unroll_length`. .