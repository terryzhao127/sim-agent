# Sim Agent

The observation of agents in Pommerman is not the same as the game state. Not only can the items (such as Extra Bomb item) not be seen, but agents cannot know the number of ammo others have with only the current observation. However, we can simulate most of them by preceding observations, which the `SimAgent` in this repo does.

However, there are some inevitable limitations which are [explained here](#explation-for-inaccuracy), which `SimAgent` has tried to diminish.

## Getting Started

### Creating environment

```
git clone --recurse-submodules git@github.com:guikarist/sim-agent.git
cd sim-agent
conda env create -f pommerman/env.yml
conda activate pommerman
```

### Usage

To use the Sim Agent, all you need to do is:
1. Subclass the `SimAgent` class in `sim_agent.py`.
1. Implement the `_act(self, obs, action_space)` method. Or after investigating the logics, you can override `act(self, obs, action_space)` for advanced usages.

### Details of Sim Agent

The recorded information of `SimAgent` is:

* `List[_Item] self._items`

    A list of items which are observable on the board. The information of `_Item()` is:

    * `_Pos self.pos` The position of an item
    * `_ItemType self.type` The type of an item

* `List[_Bomb] self._bombs`

    A list of bombs which are observable on the board. The information of `_Bomb()` is:

    * `_Pos self.pos` The position of a bomb
    * `_Agent self.bomber` The bomber of a bomb
    * `BlastStrengthType self.blast_strength` The blast strength of a bomb
    * `ActionType self.first_moving_direction` The first moving direction of a bomb
    * `bool self.has_been_moved` The moving state of a bomb (True *once the bomb has been moved before*)
    * `BombLifeType self.life` The life of a bomb **(This may be INACCURATE when the bomb `has_been_moved`)**

* `List[_Agent] self._agents`

    A list of alive agents in the game. The information of `_Agent()` is:

    * `_Pos self.pos`: The agent position
    * `AgentIdType self.id` The agent id (e.g., `0`)
    * `AgentValueType self.value` The agent value (e.g., `10`)
    * `AmmoType self.ammo` The number of ammo of an agent **(This may be INACCURATE)**
    * `bool self.can_kick`: The ability to kick bombs of an agent **(This may be INACCURATE)**
    * `BlastStrengthType self.blast_strength`: The blast strength of an anget **(This may be INACCURATE)**

## Test

For the correctness of the simulation, tests are necessary.

### Normal Test

This will test `add_ability()` of `_Agent`, games of one `SimAgent` with three `RandomAgent`, and games of one `SimAgent` with three `SimpleAgent`.

```
python test_sim_agent.py
```

### Test with PlayerAgent

This will initialize games with one `PlayerAgent`, one `SimAgent` and two `_IdleAgent` (which does nothing but stop), where you can test manually by playing.

```
python test_sim_agent.py TestSimAgent._test_simulation_by_player_agent
```

## Explation for Inaccuracy

*The simulation is impossible to be perfect and here is an example:*

It is possible for an agent to get an item while no others see: if at some step, these three things happen at the same time: *a box is destroyed by flame of bombs*, *an agent move to the position of this box* and *there is an item below this box*.

Thus, when this kind of situations happen, these information of agent simulation cannot be accurate:

1. ammo
1. blast strength
1. the ability to kick a bomb

## Reference

[Pommerman Environment](https://www.pommerman.com/)
