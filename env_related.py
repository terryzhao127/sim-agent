from pommerman.constants import DEFAULT_BOMB_LIFE, DEFAULT_BLAST_STRENGTH, Item, Action

AmmoType = int
AgentIdType = int
ActionType = Action
BombLifeType = float
AgentValueType = int
BlastStrengthType = float

action_up = ActionType.Up
action_down = ActionType.Down
action_left = ActionType.Left
action_stop = ActionType.Stop
action_right = ActionType.Right

initial_ammo = 1
bomb_stop_value = None
bomb_life_reduction = 1
initial_kick_ability = False
agent_dummy = Item.AgentDummy
end_bomb_life = BombLifeType(0)
initial_bomb_life = DEFAULT_BOMB_LIFE
initial_blast_strength = DEFAULT_BLAST_STRENGTH

bomb_value = Item.Bomb.value
flame_value = Item.Flames.value
passage_value = Item.Passage.value
enable_kick_value = Item.Kick.value
add_bomb_value = Item.ExtraBomb.value
increase_range_value = Item.IncrRange.value

ammo_obs = 'ammo'
board_obs = 'board'
agent_id_obs = 'agent_id'
can_kick_obs = 'can_kick'
alive_agents_obs = 'alive'
bomb_life_obs = 'bomb_life'
step_count_obs = 'step_count'
blast_strength_obs = 'blast_strength'
intended_actions_obs = 'intended_actions'
bomb_blast_strength_obs = 'bomb_blast_strength'


def agent_id_to_value(agent_id):
    return agent_id + 10


def agent_value_to_id(agent_value):
    return agent_value - 10
