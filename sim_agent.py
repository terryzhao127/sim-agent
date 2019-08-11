from __future__ import annotations
from typing import Dict, Tuple, List, NewType
from ast import literal_eval
from env_related import *
from enum import Enum

import pommerman
import random
import json


class SimAgent(pommerman.agents.BaseAgent):
    def __init__(self, create_sim_env: bool = False):
        super(SimAgent, self).__init__()

        self._items: List[_Item] = []
        self._agents: List[_Agent] = []
        self._dead_agents: List[_Agent] = []
        self._bombs: List[_Bomb] = []
        self._id_to_agent: Dict[AgentIdType, _Agent] = {}

        self._is_first_action: bool = True
        self._create_sim_env: bool = create_sim_env

        # Initialized in init_agent()
        self._sim_env = None

        # Initialized in act()
        self._last_board = None
        self._board = None
        self._bomb_life = None
        self._bomb_blast_strength = None
        self._alive_agents = None
        self._step_count = None

    def act(self, obs, action_space):
        # Before taking an action
        self._init_obs(obs)

        if self._is_first_action:
            self._is_first_action = False
            self._init_agents()
        else:
            missing_items = self._update_items()
            exploded_bombs, new_bombs, new_moving_bombs = self._update_bombs()
            self._update_agents(missing_items, exploded_bombs, new_bombs, new_moving_bombs)

        if self._create_sim_env:
            # Update the simulated environment
            self._update_sim_env(obs)

        # Take an action
        action = self._act(obs, action_space)

        # After taking an action
        self._last_board = self._board.copy()

        return action

    def init_agent(self, id_, game_type):
        super(SimAgent, self).init_agent(id_, game_type)

        self._sim_env = pommerman.make(pommerman.REGISTRY[game_type.value], self._generate_agents())
        self._sim_env.reset()

    def reset(self, *args, **kwargs):
        self._character.reset(*args, **kwargs)

        self._items.clear()
        self._agents.clear()
        self._dead_agents.clear()
        self._bombs.clear()
        self._id_to_agent.clear()

        self._is_first_action = True

        self._last_board = None
        self._board = None
        self._bomb_life = None
        self._bomb_blast_strength = None
        self._alive_agents = None
        self._step_count = None

    def _act(self, obs, action_space):
        """The subclass should implement this class"""
        raise NotImplementedError

    def _update_sim_env(self, obs):
        sim_state = self._create_sim_state(obs)
        self._sim_env._init_game_state = sim_state
        self._sim_env.set_json_info()
        self._sim_env._intended_actions = [i for i in literal_eval(sim_state[intended_actions_obs])]

    def _create_sim_state(self, obs):
        def append_agent(_agents, _is_alive):
            if agent.id != self._character.agent_id:
                _agents.append({
                    'agent_id': agent.id,
                    'is_alive': _is_alive,
                    'position': agent.pos,
                    'ammo': agent.ammo,
                    'blast_strength': agent.blast_strength,
                    'can_kick': agent.can_kick
                })
            else:
                _agents.append({
                    'agent_id': agent.id,
                    'is_alive': _is_alive,
                    'position': agent.pos,
                    'ammo': obs[ammo_obs],
                    'blast_strength': obs[blast_strength_obs],
                    'can_kick': obs[can_kick_obs]
                })

        board = self._board.tolist()
        bomb_life = self._bomb_life.tolist()
        bomb_blast_strength = self._bomb_blast_strength.tolist()
        bombs_on_board, flames_ob_board = SimAgent._find_items(board, bomb_life, bomb_blast_strength)
        agents = []
        bombs = []
        flames = []

        # Agents
        for agent in self._agents:
            append_agent(agents, True)
        for agent in self._dead_agents:
            append_agent(agents, False)

        # Bombs
        for bomb_on_board in bombs_on_board:
            position = bomb_on_board[0]

            recorded_bomb = None
            for bomb in self._bombs:
                if bomb.pos == position and not bomb.has_been_moved:
                    recorded_bomb = bomb

            if recorded_bomb is None:
                bomber_id = random.choice(agents)[agent_id_obs]
            else:
                bomber_id = recorded_bomb.bomber.id

            bombs.append({
                'position': [position[0], position[1]],
                'bomber_id': bomber_id,
                'life': bomb_on_board[1],
                'blast_strength': bomb_on_board[2],
                'moving_direction': None
            })

        # Flames
        for flame_obs in flames_ob_board:
            position = flame_obs
            flames.append({
                'position': [position[0], position[1]],
                'life': 2
            })

        # Items
        items = [
            [list(item.pos), item.type.value]
            for item in self._items
        ]

        state = {
            'board_size': self._board.shape[0],
            'step_count': self._step_count,
            'board': board,
            'agents': agents,
            'bombs': bombs,
            'flames': flames,
            'items': items,
            'intended_actions': []  # This is not considered in env.set_json_info(), so it can be ignored.
        }

        for key, value in state.items():
            state[key] = json.dumps(value, cls=pommerman.utility.PommermanJSONEncoder)
        return state

    def _generate_agents(self) -> List[_DummyAgent]:
        num_other_agents = len(self._character.enemies)
        if self._character.teammate != agent_dummy:
            num_other_agents += 1
        agents = [_DummyAgent() for _ in range(num_other_agents + 1)]
        return agents

    def _init_obs(self, obs):
        self._board = obs[board_obs]
        self._bomb_life = obs[bomb_life_obs]
        self._alive_agents = obs[alive_agents_obs]
        self._bomb_blast_strength = obs[bomb_blast_strength_obs]
        self._step_count = obs[step_count_obs]

    def _update_items(self) -> List[_Item]:
        """
        Update the observable items on the board
        :return: A list of missing items which are present at the last step
        """
        # Get missing items
        missing_items = []
        for item in self._items:
            row = item.pos[0]
            col = item.pos[1]
            if self._board[row][col] != item.type.value:
                missing_items.append(item)
        for item in missing_items:
            self._items.remove(item)

        # Update items on the board
        for row in range(len(self._board)):
            for col in range(len(self._board[0])):
                if _ItemType.contains(self._board[row][col]):
                    item_type = _ItemType.get_type(self._board[row][col])
                    new_item = _Item(item_type, _Pos((row, col)))

                    if new_item not in self._items:
                        # Find new items
                        self._items.append(new_item)

        return missing_items

    def _update_bombs(self) -> Tuple[List[_Bomb], List[_Bomb], List[_Bomb]]:
        """
        Update the observable bombs on the board
        :return: A list of exploded bombs, a list of new laid bombs and a list of new moving bombs
        """
        # Update life of bombs
        for bomb in self._bombs:
            bomb.update_life()

        # Update the moving state of bombs
        new_moving_bombs = []
        for bomb in self._bombs:
            if not bomb.has_been_moved:
                for agent in self._agents:
                    if agent.pos != bomb.pos and \
                            self._board[bomb.pos[0]][bomb.pos[1]] == agent.value:
                        # A bomb is kicked
                        bomb.has_been_moved = True
                        bomb.first_moving_direction = self._get_moving_direction(agent)
                        new_moving_bombs.append(bomb)

        # Get exploded bombs
        exploded_bomb = []
        for bomb in self._bombs:
            if bomb.has_been_moved:
                # Use bomb life to predict whether a bomb is exploded
                if bomb.life == end_bomb_life:
                    exploded_bomb.append(bomb)
            else:
                # The position of stopped bomb is accurate.
                if self._bomb_life[bomb.pos[0]][bomb.pos[1]] == end_bomb_life:
                    exploded_bomb.append(bomb)
        for bomb in exploded_bomb:
            self._bombs.remove(bomb)

        # Get new laid bombs
        new_bombs = []
        for agent in self._agents:
            if self._bomb_life[agent.pos[0]][agent.pos[1]] == initial_bomb_life:
                new_bomb = _Bomb(agent, agent.pos, self._bomb_blast_strength[agent.pos[0]][agent.pos[1]],
                                 initial_bomb_life)
                self._bombs.append(new_bomb)
                new_bombs.append(new_bomb)

        return exploded_bomb, new_bombs, new_moving_bombs

    def _init_agents(self):
        """Initialize simulation of agents"""
        for agent_value in self._alive_agents:
            agent_pos = SimAgent._get_agent_pos(self._board, agent_value)
            if agent_pos is not None:
                agent = _Agent(agent_value_to_id(agent_value), agent_value, agent_pos, initial_ammo,
                               initial_blast_strength, initial_kick_ability)
                self._id_to_agent[agent.id] = agent
                self._agents.append(agent)

    def _update_agents(self,
                       missing_items: List[_Item],
                       exploded_bombs: List[_Bomb],
                       new_bombs: List[_Bomb],
                       new_moving_bombs: List[_Bomb]) -> None:
        """
        Update simulation of agents
        :param missing_items: A list of items missing in the current step but present in the last step
        :param exploded_bombs: A list of bombs explode in the current step
        :param new_bombs: A list of bombs newly laid in the current step
        :param new_moving_bombs: A list of bombs able to move in the current step but unable in the last step
        """
        # Remove dead agents
        self._dead_agents = list(agent for agent in self._agents if agent.value not in self._alive_agents)
        self._agents = list(set(self._agents) - set(self._dead_agents))

        # Update position
        for agent in self._agents:
            agent.pos = SimAgent._get_agent_pos(self._board, agent.value)

        # Update ability
        for item in missing_items:
            for agent in self._agents:
                if agent.pos == item.pos:
                    agent.add_ability(item.type)
        for bomb in new_bombs:
            agent = self._id_to_agent[bomb.bomber.id]
            if agent.blast_strength < bomb.blast_strength:
                agent.blast_strength = bomb.blast_strength
        for bomb in new_moving_bombs:
            self._id_to_agent[bomb.bomber.id].can_kick = True

        # Update ammo
        for bomb in exploded_bombs:
            for agent in self._agents:
                if agent == bomb.bomber:
                    agent.ammo += 1
        for bomb in new_bombs:
            for agent in self._agents:
                if agent == bomb.bomber:
                    agent.ammo -= 1

    def _get_moving_direction(self, agent: _Agent) -> ActionType:
        new_x, new_y = SimAgent._get_agent_pos(self._board, agent.value)
        old_x, old_y = agent.pos

        if new_x == old_x and new_y == old_y + 1:
            return action_right
        elif new_x == old_x and new_y == old_y - 1:
            return action_left
        elif new_x == old_x + 1 and new_y == old_y:
            return action_down
        else:
            return action_up

    @staticmethod
    def _find_items(board, bomb_life, bomb_blast_strength):
        bombs = []
        flames = []

        for row in range(len(board)):
            for col in range(len(board[0])):
                if bomb_life[row][col] != 0:
                    bombs.append(((row, col), bomb_life[row][col], bomb_blast_strength[row][col]))
                if board[row][col] == flame_value:
                    flames.append((row, col))

        return bombs, flames

    @staticmethod
    def _get_agent_pos(board, agent_value: AgentValueType) -> _Pos:
        """
        Return position of agent by its agent_id. If the agent_id does not exist, None is returned.
        :param board: Game board
        :param agent_value: Agent value on board
        :return: Position of agent
        """
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] == agent_value:
                    return _Pos((row, col))


class _DummyAgent(pommerman.agents.BaseAgent):
    def act(self, obs, action_space):
        pass


_Pos = NewType('_Pos', Tuple[int, int])


class _ItemType(Enum):
    ADD_BOMB = add_bomb_value
    INCREASE_RANGE = increase_range_value
    ENABLE_KICK = enable_kick_value

    @classmethod
    def contains(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def get_type(cls, value):
        # noinspection PyTypeChecker
        for _, item in cls.__members__.items():
            if item.value == value:
                return item
        return None


class _Agent(object):
    __slots__ = ['id', 'value', 'pos', 'ammo', 'blast_strength', 'can_kick']

    def __init__(self,
                 agent_id: AgentIdType,
                 agent_value: AgentValueType,
                 pos: _Pos,
                 ammo: AmmoType,
                 blast_strength: BlastStrengthType,
                 can_kick: bool):
        self.id = agent_id
        self.value = agent_value
        self.pos = pos
        self.ammo = ammo
        self.blast_strength = blast_strength
        self.can_kick = can_kick

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def add_ability(self, item_type: _ItemType):
        if item_type == _ItemType.ADD_BOMB:
            self.ammo += 1
        elif item_type == _ItemType.ENABLE_KICK:
            self.can_kick = True
        elif item_type == _ItemType.INCREASE_RANGE:
            self.blast_strength += 1
        else:
            raise TypeError('Invalid type for item_type in add_ability()')


class _Item(object):
    __slots__ = ['type', 'pos']

    def __init__(self, item_type: _ItemType, pos: _Pos):
        self.type = item_type
        self.pos = pos

    def __hash__(self):
        return hash(str(self.type.value) + str(self.pos))

    def __eq__(self, other):
        return self.type.value == other.type.value and \
               self.pos[0] == other.pos[0] and \
               self.pos[1] == other.pos[1]


class _Bomb(object):
    __slots__ = ['bomber', 'pos', 'has_been_moved', 'blast_strength', 'life', 'first_moving_direction']

    def __init__(self, bomber: _Agent, pos: _Pos, blast_strength: BlastStrengthType,
                 life: BombLifeType, has_been_moved=False, first_moving_direction=None) -> None:
        self.bomber = bomber
        self.pos = pos
        self.has_been_moved = has_been_moved
        self.blast_strength = blast_strength
        self.life = life
        self.first_moving_direction: ActionType = first_moving_direction

    def __hash__(self):
        return hash(str(self.bomber.id) + str(self.pos))

    def __eq__(self, other):
        return self.bomber.id == other.bomber.id and \
               self.pos[0] == other.pos[0] and \
               self.pos[1] == other.pos[1]

    def update_life(self):
        self.life -= bomb_life_reduction
