import logging
import numpy as np

from player import Player
from agent import Agent
from game import Game

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'util'))

import constants
from util import Util
from plotting import Plotting

# create directory if it doesn't exists
Util.create_directory_for_plots(0, 0)

# instances
player = Player()
agent = Agent()
game = Game()

# define environment 
ENV_ROWS = 37
ENV_COL = 3

# define robot's action
actions = ['none', 'suggest_row_or_column', 'suggest_card']

# define states: {user_state X robot_last_action X game_state}
states = [
    'INIT_STATE',

    'FIRST_FLIPPING_NONE_BEGIN_CORRECT',
    'FIRST_FLIPPING_NONE_BEGIN_WRONG',
    'FIRST_FLIPPING_NONE_MIDDLE_CORRECT',
    'FIRST_FLIPPING_NONE_MIDDLE_WRONG',
    'FIRST_FLIPPING_NONE_END_CORRECT',
    'FIRST_FLIPPING_NONE_END_WRONG',

    'FIRST_FLIPPING_SUGGEST_RC_BEGIN_CORRECT',
    'FIRST_FLIPPING_SUGGEST_RC_BEGIN_WRONG',
    'FIRST_FLIPPING_SUGGEST_RC_MIDDLE_CORRECT',
    'FIRST_FLIPPING_SUGGEST_RC_MIDDLE_WRONG',
    'FIRST_FLIPPING_SUGGEST_RC_END_CORRECT',
    'FIRST_FLIPPING_SUGGEST_RC_END_WRONG',

    'FIRST_FLIPPING_SUGGEST_CARD_BEGIN_CORRECT',
    'FIRST_FLIPPING_SUGGEST_CARD_BEGIN_WRONG',
    'FIRST_FLIPPING_SUGGEST_CARD_MIDDLE_CORRECT',
    'FIRST_FLIPPING_SUGGEST_CARD_MIDDLE_WRONG',
    'FIRST_FLIPPING_SUGGEST_CARD_END_CORRECT',
    'FIRST_FLIPPING_SUGGEST_CARD_END_WRONG',

    'SECOND_FLIPPING_NONE_BEGIN_CORRECT',
    'SECOND_FLIPPING_NONE_BEGIN_WRONG',
    'SECOND_FLIPPING_NONE_MIDDLE_CORRECT',
    'SECOND_FLIPPING_NONE_MIDDLE_WRONG',
    'SECOND_FLIPPING_NONE_END_CORRECT',
    'SECOND_FLIPPING_NONE_END_WRONG',

    'SECOND_FLIPPING_SUGGEST_RC_BEGIN_CORRECT',
    'SECOND_FLIPPING_SUGGEST_RC_BEGIN_WRONG',
    'SECOND_FLIPPING_SUGGEST_RC_MIDDLE_CORRECT',
    'SECOND_FLIPPING_SUGGEST_RC_MIDDLE_WRONG',
    'SECOND_FLIPPING_SUGGEST_RC_END_CORRECT',
    'SECOND_FLIPPING_SUGGEST_RC_END_WRONG',

    'SECOND_FLIPPING_SUGGEST_CARD_BEGIN_CORRECT',
    'SECOND_FLIPPING_SUGGEST_CARD_BEGIN_WRONG',
    'SECOND_FLIPPING_SUGGEST_CARD_MIDDLE_CORRECT',
    'SECOND_FLIPPING_SUGGEST_CARD_MIDDLE_WRONG',
    'SECOND_FLIPPING_SUGGEST_CARD_END_CORRECT',
    'SECOND_FLIPPING_SUGGEST_CARD_END_WRONG'
]

PAIRS = 12
EPISODES = constants.EPISODES_WITH_AGENT

# Keeps track of useful statistics
stats = Plotting.EpisodeStats(
    episode_lengths = np.zeros(EPISODES),
    episode_rewards = np.zeros(EPISODES),
    episode_click_until_match = np.zeros(PAIRS),
    avg_of_moves_until_match = np.zeros(PAIRS),
    avg_of_suggests_in_specific_episode = np.zeros(PAIRS),
    avg_of_suggests_after_some_episode = np.zeros(PAIRS)
)

def learning():
    # define training parameters
    DISCOUNT_FACTOR = 0.8
    epsilon = 1.0
    learning_rate = 0.1

    # initialize Q-values to 0
    Q = np.zeros((ENV_ROWS, ENV_COL))

    for episode in range(EPISODES):
        game.init_game(player)

        # init S
        state = constants.INIT_STATE

        # for each step of episode
        while state_is_not_terminal():
            # Choose A from S using policy derived from Q (e.g., "epsilon-greedy")
            action = select_action(Q, state, epsilon)

            # Take action A, observe R, S'
            next_state, reward = step(state, action)

            # update statistics
            Plotting.update_stats(stats, episode, reward, action, player, game, Plotting.ROBOT_PLAYER)

            # update Q
            Q[state, action] = Q[state, action] \
                               + learning_rate \
                               * (reward + DISCOUNT_FACTOR * np.max(Q[next_state, :]) - Q[state, action])

            # S <- S'
            state = next_state

        # epsilon decay
        epsilon = get_new_epsilon(episode)
        # learning rate increase
        learning_rate = get_new_learning_rate(learning_rate, episode)

        # save plot
        print_stats(episode)

        # for debug; print q-table with pandas every 500 times
        Util.print_Q_table(Q, states, actions, 500)

    print(Q)

    # save matrix into a file in order to use that with human player
    Util.save_Q_table_into_file(Q)
    # save epsilon for the same reason
    Util.save_epsilon_into_file(epsilon)


def select_action(Q, state, epsilon):
    is_pairs_zero = player.get_pairs < 1

    if is_pairs_zero:
        return constants.SUGGEST_NONE
    else:
        if np.random.random() < epsilon:
            return np.random.randint(3)
        else:
            return np.argmax(Q[state, :])

def step(state, action):
    """
    For each step get the robot action, make a move by following the suggestion, 
    then move to next state, get the reward and set player's info if second card was clicked.
    """
    
    suggest, card, position = agent.take_action(action, player, game)

    # click a card and follow the suggest
    clicked_card, pos, match = player.play(suggest, card, position, game)
    
    next_state = agent.get_next_state(action, game.get_face_up_cards, 
                                      player.get_pairs, player.get_last_pair_was_correct)

    reward = agent.get_reward(state, action, player, game)
    
    logging.debug("Current turn:", game.get_turn - 1)
    logging.debug("Current state:", states[state])
    logging.debug("Action", action)
    logging.debug("Suggest:", suggest, card, position)
    logging.debug("Clicked:", clicked_card, pos, match, player.get_number_of_clicks_for_current_pair)
    logging.debug("Reward", reward, "\n")

    return next_state, reward

def state_is_not_terminal():
    return player.get_pairs != 12

def get_new_learning_rate(current_learning_rate, episode, start_lr = 0.1, taper_lr = 0.001):
    if current_learning_rate < 0.96:
        return start_lr * (1.0 + episode * taper_lr)
    
    return current_learning_rate

def get_new_epsilon(episode):
    START_EPSILON = 1.0   # Probability of random action
    EPSILON_TAPER = 0.01  # How much epsilon is adjusted each step
    
    return START_EPSILON / (1.0 + episode * EPSILON_TAPER)

##################################################################################################################
#                                                   PLOT                                                         #
##################################################################################################################

def print_stats(episode):
    if (episode != 0 and episode % 1000 == 0) or episode == 99999:
        # total moves for each episode
        avg_moves = Util.get_cumulative_avg(stats.episode_lengths, episode)
        Plotting.save_stats(avg_moves, Plotting.AVERAGE_EPISODE_LENGTH, episode, Plotting.ROBOT_PLAYER, 0)

        # average suggest for each pair of specific episode
        Plotting.save_stats(stats.avg_of_suggests_in_specific_episode, Plotting.ACTION_TAKEN_IN_SPECIFIC_EPISODE, 
                            episode, Plotting.ROBOT_PLAYER, 0)

        # average suggest for each pair considering n episodes
        avg_suggest_after_episode = Util.get_avarage(stats.avg_of_suggests_after_some_episode, PAIRS, episode)
        Plotting.save_stats(avg_suggest_after_episode, Plotting.AVERAGE_OF_ACTIONS_TAKEN, episode, Plotting.ROBOT_PLAYER, 0)

        # number of click until pair is founded
        Plotting.save_stats(stats.episode_click_until_match, Plotting.NUMBER_OF_CLICK_UNTIL_MATCH, episode, 
                            Plotting.ROBOT_PLAYER, 0)

        # average of moves until pair is founded considering n episodes
        avg_moves_after_episode = Util.get_avarage(stats.avg_of_moves_until_match, PAIRS, episode)
        Plotting.save_stats(avg_moves_after_episode, Plotting.AVERAGE_OF_TURNS_FOR_MATCH, episode, 
                            Plotting.ROBOT_PLAYER, 0)

        # total reward for each episode
        avg_rewards = Util.get_cumulative_avg(stats.episode_rewards, episode)
        Plotting.save_stats(avg_rewards, Plotting.AVERAGE_EPISODE_REWARDS, episode, Plotting.ROBOT_PLAYER, 0)


if __name__ == "__main__":
    learning()
