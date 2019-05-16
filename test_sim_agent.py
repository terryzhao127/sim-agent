from pommerman.agents import BaseAgent, SimpleAgent, PlayerAgent, RandomAgent
from typing import List, Dict
from pommerman.constants import Action
from sim_agent import SimAgent, _Agent, _ItemType, _Pos
from env_related import AgentIdType, initial_bomb_life, agent_value_to_id, agent_id_to_value, bomb_stop_value

import random
import unittest
import pommerman


class _IdleAgent(BaseAgent):
    def act(self, obs, action_space):
        return Action.Stop


class _IdleSimAgent(SimAgent):
    def _act(self, obs, action_space):
        return Action.Stop


class TestSimAgent(unittest.TestCase):
    def test_simulation_by_simple_agents(self):
        num_episodes = 10000

        agent_list = [
            SimpleAgent(),
            SimpleAgent(),
            SimpleAgent()
        ]
        self._test_simulation(agent_list, num_episodes)

    def test_simulation_by_random_agents(self):
        num_episodes = 10000

        agent_list = [
            RandomAgent(),
            RandomAgent(),
            RandomAgent()
        ]
        self._test_simulation(agent_list, num_episodes)

    def _test_simulation_by_player_agent(self):
        num_episodes = 10000

        agent_list = [
            _IdleAgent(),
            _IdleAgent(),
            PlayerAgent()
        ]
        self._test_simulation(agent_list, num_episodes, render=True)

    def test_add_ability(self):
        num_tests = 100

        agents: List[_Agent] = []
        for i in range(3):
            agents.append(_Agent(i, agent_id_to_value(i), _Pos((1, i)), 1, 2, False))

        for _ in range(num_tests):
            agent = random.sample(agents, 1)[0]
            ammo = agent.ammo
            blast_strength = agent.blast_strength

            # noinspection PyTypeChecker
            item_type = random.choice(list(_ItemType))
            agent.add_ability(item_type)

            if item_type == _ItemType.ADD_BOMB:
                self.assertEqual(ammo + 1, agent.ammo)
            elif item_type == _ItemType.ENABLE_KICK:
                self.assertEqual(agent.can_kick, True)
            elif item_type == _ItemType.INCREASE_RANGE:
                self.assertEqual(blast_strength + 1, agent.blast_strength)

    def _test_simulation(self, agent_list, num_episodes, render=False):
        sim_agent_index = 0

        sim_agent = _IdleSimAgent()
        agent_list.insert(sim_agent_index, sim_agent)

        env = pommerman.make('PommeFFACompetition-v0', agent_list)

        for i_episode in range(num_episodes):
            state = env.reset()
            done = False

            real_agent_index_to_id = {
                i: agent_value_to_id(state[i]['board'][state[i]['position'][0]][state[i]['position'][1]])
                for i in range(len(state))
            }
            id_to_agent: Dict[AgentIdType, _Agent] = {}
            moved_bombs = set()
            first_step = True
            while not done:
                if render:
                    env.render()

                actions = env.act(state)
                if first_step:
                    id_to_agent = {agent.id: agent for agent in sim_agent._agents}
                    first_step = False

                # Test bombs and some related abilities of agents
                for real_bomb in env._bombs:
                    self.assertNotEqual(id_to_agent, {})
                    agent = id_to_agent[real_agent_index_to_id[real_bomb.bomber.agent_id]]

                    # Test blast strength of agents
                    if real_bomb.life == initial_bomb_life:
                        if agent.blast_strength != real_bomb.bomber.blast_strength:
                            print(env.get_json_info())
                            print(real_bomb.to_json())
                            print(real_bomb.bomber.blast_strength)
                            print(agent.id)
                            print(agent.pos)
                            print(agent.can_kick)
                            print(agent.blast_strength)
                            print(agent.ammo)
                        self.assertEqual(agent.blast_strength, real_bomb.bomber.blast_strength)

                    if real_bomb.moving_direction != bomb_stop_value:
                        if real_bomb not in moved_bombs:
                            moved_bombs.add(real_bomb)

                        # Test kick ability of agents
                        self.assertEqual(agent.can_kick, True)

                    if real_bomb not in moved_bombs:
                        # Tests on bombs which has not been moved
                        find_bomb = False
                        for bomb in sim_agent._bombs:
                            if bomb.pos == real_bomb.position and not bomb.has_been_moved:
                                if real_bomb.blast_strength != bomb.blast_strength:
                                    print('Strength!!!!')
                                    print(real_bomb.to_json())
                                    print(str(bomb))
                                self.assertEqual(real_bomb.blast_strength, bomb.blast_strength)
                                if real_bomb.life != bomb.life:
                                    print('Life!!!!')
                                    print(real_bomb.to_json())
                                    print(bomb.blast_strength)
                                    print(bomb.pos)
                                    print(bomb.life)
                                    print(bomb.bomber.id)
                                    print(bomb.bomber.pos)
                                    print(bomb.first_moving_direction)
                                    print(bomb.has_been_moved)
                                self.assertEqual(real_bomb.life, bomb.life)
                                find_bomb = True
                        self.assertEqual(find_bomb, True)

                # Test position and id of agents
                real_agents = [
                    state[i] for i in range(len(state))
                    if agent_id_to_value(real_agent_index_to_id[i]) in state[i]['alive']
                ]

                self.assertEqual(len(sim_agent._agents), len(real_agents))
                for i, (agent, real_agent) in enumerate(zip(
                        sorted(sim_agent._agents, key=lambda x: x.id),
                        sorted(
                            real_agents,
                            key=lambda x: agent_value_to_id(x['board'][x['position'][0]][x['position'][1]])
                        )
                )):
                    self.assertEqual(agent.pos, real_agent['position'])
                    self.assertEqual(
                        agent.id,
                        agent_value_to_id(real_agent['board'][real_agent['position'][0]][real_agent['position'][1]])
                    )

                # Take actions in env and get next state
                state, reward, done, info = env.step(actions)
                if reward[sim_agent_index] == -1 and not done:
                    # Stop the episode when the learning agent dies
                    done = True
        env.close()


if __name__ == '__main__':
    unittest.main()
