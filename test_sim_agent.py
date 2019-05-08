import random
import unittest
import pommerman

from pommerman import agents
from typing import List, Dict
from pommerman.constants import Action
from sim_agent import SimAgent, _Other, _ItemType, _Pos, _initial_bomb_life, _AgentIdType


class _IdleAgent(agents.BaseAgent):
    def act(self, obs, action_space):
        return Action.Stop


class _IdleSimAgent(SimAgent):
    def _act(self, obs, action_space):
        return Action.Stop


class TestSimAgent(unittest.TestCase):
    def test_simulation_by_simple_agents(self):
        num_episodes = 100

        agent_list = [
            agents.SimpleAgent(),
            agents.SimpleAgent(),
            agents.SimpleAgent()
        ]
        self._test_simulation(agent_list, num_episodes)

    def test_simulation_by_random_agents(self):
        num_episodes = 100

        agent_list = [
            agents.RandomAgent(),
            agents.RandomAgent(),
            agents.RandomAgent()
        ]
        self._test_simulation(agent_list, num_episodes)

    def _test_simulation_by_player_agent(self):
        num_episodes = 100

        agent_list = [
            _IdleAgent(),
            _IdleAgent(),
            agents.PlayerAgent()
        ]
        self._test_simulation(agent_list, num_episodes, render=True)

    def test_add_ability(self):
        num_tests = 100

        others: List[_Other] = []
        for i in range(3):
            others.append(_Other(i, _Pos((1, i)), 1, 2, False))

        for _ in range(num_tests):
            other = random.sample(others, 1)[0]
            ammo = other.ammo
            blast_strength = other.blast_strength

            # noinspection PyTypeChecker
            item_type = random.choice(list(_ItemType))
            other.add_ability(item_type)

            if item_type == _ItemType.ADD_BOMB:
                self.assertEqual(ammo + 1, other.ammo)
            elif item_type == _ItemType.ENABLE_KICK:
                self.assertEqual(other.can_kick, True)
            elif item_type == _ItemType.INCREASE_RANGE:
                self.assertEqual(blast_strength + 1, other.blast_strength)

    def _test_simulation(self, agent_list, num_episodes, render=False):
        sim_agent_index = 0
        bomb_stop = None

        sim_agent = _IdleSimAgent()
        agent_list.insert(sim_agent_index, sim_agent)

        env = pommerman.make('PommeFFACompetition-v0', agent_list)

        for i_episode in range(num_episodes):
            state = env.reset()
            done = False

            agent_index_to_id = {i: state[i]['board'][state[i]['position'][0]][state[i]['position'][1]]
                                 for i in range(len(state))}
            id_to_other: Dict[_AgentIdType, _Other] = {}
            first_step = True
            while not done:
                if render:
                    env.render()

                actions = env.act(state)
                if first_step:
                    id_to_other = {other.id: other for other in sim_agent._others}
                    first_step = False

                for real_bomb in env._bombs:
                    self.assertNotEqual(id_to_other, {})
                    other = id_to_other[agent_index_to_id[real_bomb.bomber.agent_id]]

                    # Test blast strength of others
                    if real_bomb.life == _initial_bomb_life:
                        self.assertEqual(other.blast_strength, real_bomb.bomber.blast_strength)

                    # Test kick ability of others
                    if real_bomb.moving_direction != bomb_stop:
                        self.assertEqual(other.can_kick, True)

                # Test position and id of others
                real_agents = [state[i] for i in range(len(state)) if i != sim_agent_index
                               and agent_index_to_id[i] in state[i]['alive']]

                self.assertEqual(len(sim_agent._others), len(real_agents))
                for i, (other, agent) in enumerate(zip(
                        sorted(sim_agent._others, key=lambda x: x.id),
                        sorted(real_agents, key=lambda x: x['board'][x['position'][0]][x['position'][1]])
                )):
                    self.assertEqual(other.pos, agent['position'])
                    self.assertEqual(other.id, agent['board'][agent['position'][0]][agent['position'][1]])

                # Take actions in env and get next state
                state, reward, done, info = env.step(actions)
                if reward[sim_agent_index] == -1 and not done:
                    # Stop the episode when the learning agent dies
                    done = True
        env.close()


if __name__ == '__main__':
    unittest.main()
