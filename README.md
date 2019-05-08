# Sim Agent

The observation of agents in Pommerman is not the same as the game state. Not only can the items (such as Extra Bomb item) not be seen, but agents cannot know the number of ammo others have with only the current observation. However, we can simulate most of them by preceding observations, which the `SimAgent` in this repo do.

However, there are some inevitable limitations which are [explained here](#explation-for-inaccuracy)

## Getting Started

### Creating environment

```
git clone --recurse-submodules git@github.com:guikarist/sim-agent.git
conda env create -f env.yml
conda activate pommerman
```

### Usage

To use the SimAgent, all you need to do is:
1. Subclass the `SimAgent` class in `sim_agent.py`.
1. Implement the `_act(self, obs, action_space)` method. Or after investigating the logics, you can override `act(self, obs, action_space)` for advanced usages. 

### Details of SimAgent

The recorded information of SimAgent is:

* `List[_Item] self._items`

    A list of items which are observable on the board. The information of `_Item()` is:

    * `_Pos self.pos` The position of an item
    * `_ItemType self.type` The type of an item

* `List[_Bomb] self._bombs`

    A list of bombs which are observable on the board. The information of `_Bomb()` is:

    * `_Pos self.pos` The position of a bomb
    * `_Other self.bomber` The bomber of a bomb
    * `_BlastStrengthType self.blast_strength` The blast strength of a bomb
    * `bool self.has_been_moved` The moving state of a bomb (True *once the bomb has been moved before*)
    * `_BombLifeType self.life` The life of a bomb **(This may be INACCURATE when the bomb `has_been_moved`)**

* `List[_Other] self._others`

    A list of other agents in the game. The information of `_Other()` is:

    * `_Pos self.pos`: The position of another agent
    * `_AgentIdType self.id`: The agent id of another agent
    * `_AmmoType self.ammo` The number of ammo of another agent **(This may be INACCURATE)**
    * `_BombLifeType self.can_kick`: The aiblity to kick bombs of another agent **(This may be INACCURATE)**
    * `_BlastStrengthType self.blast_strength`: The blast strength of another anget **(This may be INACCURATE)**

## Test

For the correctness of the simulation, tests are necessary.

### Normal Test

This will test `add_ability()` of `_Other`, games of one `SimAgent` with three `RandomAgent`, and games of one `SimAgent` with three `SimpleAgent`.

```
python test_sim_agent.py
```

### Test with PlayerAgent

This will initialize games with one `PlayerAgent`, one `SimAgent` and two `_IdleAgent` (which does nothing but stop), where you can test manually by playing.

```
python test_sim_agent.py TestSimAgent._test_simulation_by_player_agent
```

## Explation for Inaccuracy

**The simulation is impossible to be the perfect of the real states of others due to these reasons:**

1.  **The items of another agent gets are partially observable.** It is possible for an agent to get an item while no others see: if at some step, these three things happen at the same time: *a box is destroyed by flame of bombs*, *an agent move to the position of this box* and *there is an item below this box*.

    Thus, when this kind of situations happens, these information of agent simulation cannot be accurate:

    1. ammo
    1. blast strength
    1. the ability to kick a bomb

    However, the information of 2 and 3 can be observed as soon as these events happen:

    1. The agent lays a new bomb.
    1. The agent kicks a bomb.

    while the information of 1 can be more accurate as the agent lays more bombs. So the tests should be based on these events or cases.

2.  **The moving states of bombs are partially observable.** Just with the observations of the game, it is impossible to perfectly simulate the move of a bomb, because it has lots of things to do with the internal forward model and other internal inaccessible states.

    However, it is necessary for `SimAgent` to simulate the number of ammo of another agent.

    To simulate the number of ammo, besides keeping track of Extra Bomb items an agent has got, you must also record states of bombs the agent has laid. When an agent lays a bomb, its number of ammo reduces one. When an agent's bomb explodes, its number of ammo increases one.

    The ammo reduction can be accurately simulated, while the ammo increment cannot. Because the ammo increment is detected by checking whether there is a zero `bomb_life` on the same position as the bomb on the board, while we cannot know the accurate next position of a moved bomb. Thus, the `SimAgent` takes these two strategies:

    1. If a bomb *has not been moved before*, when there is a zero `bomb_life` on the same position as the bomb on the board, do addtion to the corresponding agent.
    1. If a bomb *has been moved before*, when its `life` becomes zero, do addtion to the corresponding agent.

    So the sim_agent uses `life` of a bomb to test whether a moved bomb *has exploded*, despite it is inaccurate either (because the bomb can be exploded in a chain).

## Citation

For using codes in the repo, please cite it as follows:
```
@misc{tianyu2019simagent,
  author = {Tianyu Zhao},
  title = {Sim Agent},
  year = {2019},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/guikarist/sim-agent}}
}
```

## Reference

[Pommerman Environment](https://www.pommerman.com/)
