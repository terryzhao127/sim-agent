**The simulation is impossible to be the perfect of the real states of others due to these reasons:**

1. It is possible for an agent get an item while no others see: if at some step, a box is destroyed by flame of bombs
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

2. Just with the observations of the game, it is impossible to perfectly to simulate the move of a bomb, because it
 has lots of things to do with the internal rules of agents and bombs moving. But it is needed for the program to denote
 whether a bomb is exploded and then necessary for simulating number of ammo of an agent. So the sim_agent uses life of
 a bomb to test whether a moving is exploded, despite it is inaccurate either (because the bomb can be exploded in a
 chain).
