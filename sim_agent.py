from pommerman.agents import BaseAgent
from pommerman.constants import DEFAULT_BOMB_LIFE, DEFAULT_BLAST_STRENGTH, Item
from enum import Enum
from typing import Dict, Tuple, List, NewType

# Environmental settings
_blast_strength_type = float
_agent_id_type = int
_ammo_type = int
_bomb_life_type = float

_initial_ammo = 1
_initial_kick_ability = False
_initial_bomb_life = DEFAULT_BOMB_LIFE
_initial_blast_strength = DEFAULT_BLAST_STRENGTH
_bomb_life_reduction = 1
_end_bomb_life = _bomb_life_type(0)
_bomb_value = Item.Bomb.value
_passage_value = Item.Passage.value
_enable_kick_value = Item.Kick.value
_add_bomb_value = Item.ExtraBomb.value
_increase_range_value = Item.IncrRange.value

_board_obs = 'board'
_enemies_obs = 'enemies'
_teammates_obs = 'teammate'
_alive_agents_obs = 'alive'
_bomb_life_obs = 'bomb_life'
_bomb_blast_strength_obs = 'bomb_blast_strength'

_Pos = NewType('_Pos', Tuple[int, int])


class _ItemType(Enum):
    ADD_BOMB = _add_bomb_value
    INCREASE_RANGE = _increase_range_value
    ENABLE_KICK = _enable_kick_value

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


class _Other(object):
    __slots__ = ['id', 'pos', 'ammo', 'blast_strength', 'can_kick']

    def __init__(self,
                 other_id: _agent_id_type,
                 pos: _Pos,
                 ammo: _ammo_type,
                 blast_strength: _blast_strength_type,
                 can_kick: bool):
        self.id = other_id
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
    __slots__ = ['bomber', 'pos', 'is_moving', 'blast_strength', 'life']

    def __init__(self, bomber: _Other, pos: _Pos, is_moving: bool, blast_strength: _blast_strength_type,
                 life: _bomb_life_type):
        self.bomber = bomber
        self.pos = pos
        self.is_moving = is_moving
        self.blast_strength = blast_strength
        self.life = life

    def __hash__(self):
        return hash(str(self.bomber.id) + str(self.pos))

    def __eq__(self, other):
        return self.bomber.id == other.bomber.id and \
               self.pos[0] == other.pos[0] and \
               self.pos[1] == other.pos[1]

    def update_life(self):
        self.life -= _bomb_life_reduction


class SimAgent(BaseAgent):
    def __init__(self):
        super(SimAgent, self).__init__()

        self._items: List[_Item] = []
        self._others: List[_Other] = []
        self._bombs: List[_Bomb] = []
        self._id_to_other: Dict[_agent_id_type, _Other] = {}
        self._is_first_action = True

        # Initialized in act()
        self._last_board = None
        self._board = None
        self._bomb_life = None
        self._bomb_blast_strength = None
        self._enemies = None
        self._teammates = None
        self._alive_agents = None

    def act(self, obs, action_space):
        # Before taking an action
        self._init_obs(obs)

        if self._is_first_action:
            self._is_first_action = False
            self._init_others()
        else:
            missing_items = self._update_items()
            exploded_bombs, new_bombs, new_moving_bombs = self._update_bombs()
            self._update_others(missing_items, exploded_bombs, new_bombs, new_moving_bombs)

        # Take an action
        action = self._act(obs, action_space)

        # After taking an action
        self._last_board = self._board.copy()

        return action

    def reset(self, *args, **kwargs):
        self._character.reset(*args, **kwargs)

        self._items.clear()
        self._others.clear()
        self._bombs.clear()
        self._id_to_other.clear()
        self._is_first_action = True

        self._last_board = None
        self._board = None
        self._bomb_life = None
        self._bomb_blast_strength = None
        self._enemies = None
        self._teammates = None
        self._alive_agents = None

    def _act(self, obs, action_space):
        """The subclass should implement this class"""
        raise NotImplementedError

    def _init_obs(self, obs):
        self._board = obs[_board_obs]
        self._enemies = obs[_enemies_obs]
        self._bomb_life = obs[_bomb_life_obs]
        self._teammates = obs[_teammates_obs]
        self._alive_agents = obs[_alive_agents_obs]
        self._bomb_blast_strength = obs[_bomb_blast_strength_obs]

    def _update_items(self) -> List[_Item]:
        """
        Update the observable items on the board
        :return: A list of missing items which are present after last update
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
            if not bomb.is_moving:
                for other in self._others:
                    if other.pos != bomb.pos and \
                            self._board[bomb.pos[0]][bomb.pos[1]] == other.id:
                        # A bomb is kicked
                        bomb.is_moving = True
                        new_moving_bombs.append(bomb)

        # Get exploded bombs
        exploded_bomb = []
        for bomb in self._bombs:
            if bomb.is_moving:
                # Use bomb life to predict whether a bomb is exploded
                if bomb.life == _end_bomb_life:
                    exploded_bomb.append(bomb)
            else:
                # The position of stopped bomb is accurate.
                if self._bomb_life[bomb.pos[0]][bomb.pos[1]] == _end_bomb_life:
                    exploded_bomb.append(bomb)
        for bomb in exploded_bomb:
            self._bombs.remove(bomb)

        # Get new laid bombs
        new_bombs = []
        for other in self._others:
            if self._bomb_life[other.pos[0]][other.pos[1]] == _initial_bomb_life:
                new_bomb = _Bomb(other, other.pos, False,
                                 self._bomb_blast_strength[other.pos[0]][other.pos[1]], _initial_bomb_life)
                self._bombs.append(new_bomb)
                new_bombs.append(new_bomb)

        return exploded_bomb, new_bombs, new_moving_bombs

    def _init_others(self):
        """Initialize simulation of others"""
        for other_agent in self._enemies + [self._teammates]:
            agent_pos = SimAgent._get_agent_pos(self._board, other_agent.value)
            if agent_pos is not None:
                other = _Other(other_agent.value, agent_pos, _initial_ammo, _initial_blast_strength,
                               _initial_kick_ability)
                self._id_to_other[other_agent.value] = other
                self._others.append(other)

    def _update_others(self,
                       missing_items: List[_Item],
                       exploded_bombs: List[_Bomb],
                       new_bombs: List[_Bomb],
                       new_moving_bombs: List[_Bomb]):
        """
        Update simulation of others
        :param missing_items: A list of items missing in the current step but present in the last step
        :param exploded_bombs: A list of bombs explode in the current step
        :param new_bombs: A list of bombs newly laid in the current step
        :param new_moving_bombs: A list of bombs able to move in the current step but unable in the last step
        """
        # Remove dead others
        self._others = list(other for other in self._others if other.id in self._alive_agents)

        # Update position
        for other in self._others:
            other.pos = SimAgent._get_agent_pos(self._board, other.id)

        # Update ability
        for item in missing_items:
            for other in self._others:
                if other.pos == item.pos:
                    other.add_ability(item.type)
        for bomb in new_bombs:
            other = self._id_to_other[bomb.bomber.id]
            if other.blast_strength <= bomb.blast_strength:
                other.blast_strength = bomb.blast_strength
        for bomb in new_moving_bombs:
            self._id_to_other[bomb.bomber.id].can_kick = True

        # Update ammo
        for bomb in exploded_bombs:
            for other in self._others:
                if other == bomb.bomber:
                    other.ammo += 1
        for bomb in new_bombs:
            for other in self._others:
                if other == bomb.bomber:
                    other.ammo -= 1

    @staticmethod
    def _get_agent_pos(board, agent_id: _agent_id_type) -> _Pos:
        """
        Return position of agent by its agent_id. If the agent_id does not exist, None is returned.
        :param board: Game board
        :param agent_id: Agent ID
        :return: Position of agent
        """
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] == agent_id:
                    return _Pos((row, col))
