

# Sim Agent

The observation of agents in Pommerman is not the same as the game state. Not only can the items (such as Extra Bomb item) not be seen, but agents can not know the number of ammo others have with only the current observation. However, we can predict most of them by preceding observations, which the SimAgent in this repo do.

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
    * `bool self.is_moving` The moving state of a bomb
    * `_bomb_life_type self.life` The life of a bomb **(This may be INACCURATE when `is_moving`)**
    * `_blast_strength_type self.blast_strength` The blast strength of a bomb **(This may be INACCURATE when `is_moving`)**

    
* `List[_Other] self._others`

    A list of other agents in the game. The information of `_Other()` is:

    * `_Pos self.pos`: The position of another agent
    * `_agent_id_type self.id`: The agent id of another agent
    * `_ammo_type self.ammo` The number of ammo of another agent **(This may be INACCURATE)**
    * `_bomb_life_type self.can_kick`: The aiblity to kick bombs of another agent **(This may be INACCURATE)**
    * `_blast_strength_type self.blast_strength`: The blast strength of another anget **(This may be INACCURATE)**

## Test

Explain how to run the automated tests for this system

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

1.  It is possible for an agent get an item while no others see: if at some step, a box is destroyed by flame of bombs
, a agent move to the position of this box and get the hidden item below the box.

    Thus, when the situations happens, these information of agent simulation cannot be exact:

    1. ammo
    1. blast strength
    1. the ability to kick a bomb
    
    In other words, the state of what items a agent get is **partially observable**.
    However, after these hidden situations, the information of 2 and 3 can be observed as soon as these events happen:
    
    1. The agent lays a new bomb.
    1. The agent kicks a bomb.
    
    while the information of 1 can be more exact as many bombs a agent laid as possible.
    So the tests should of these information of agent should be based on these events or cases.

2.  Just with the observations of the game, it is impossible to perfectly to simulate the move of a bomb, because it
 has lots of things to do with the internal rules of agents and bombs moving. But it is needed for the program to denote
 whether a bomb is exploded and then necessary for simulating number of ammo of an agent. So the sim_agent uses life of
 a bomb to test whether a moving is exploded, despite it is inaccurate either (because the bomb can be exploded in a
 chain).
 
## Reference

[Pommerman Environment](https://www.pommerman.com/)
