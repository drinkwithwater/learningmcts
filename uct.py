# This is a very simple implementation of the UCT Monte Carlo Tree Search
# algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards
# the bottom of the code.
# It aims to have the clearest and simplest possible code,
# and for the sake of clarity, the code is orders of magnitude
# less efficient than it could be made, particularly by using a
# state.GetRandomMove() or state.DoRandomRollout() function.
#
# Example GameState classes for Nim, OXO and Othello are included to
# give some idea of how you can write your own GameState use UCT
# in your 2-player game. Change the game to be played
# in the UCTPlayGame() function at the bottom of the code.
#
# Written by Peter Cowling, Ed Powley,
# Daniel Whitehouse (University of York, UK) September 2012.
# Updated by SErAphLi to support python 3. Switch to Google python style.
#
# Licence is granted to freely use and distribute
# for any sensible/legal purpose so long as this comment
# remains in any distributed code.
#
# For more information about Monte Carlo Tree Search
# check out our web site at www.mcts.ai

from math import *
import random


class CoinToss(object):
    """
    A state of the game, i.e. the game board. These are the only functions
    which are absolutely necessary to implement UCT in any 2-player complete
    information deterministic zero-sum game, although they can be enhanced and
    made quicker, for example by using a GetRandomMove() function to generate
    a random move during rollout.
    By convention the players are numbered 1 and 2.
    """

    def __init__(self):
        # chance with 0
        # player 1, 2
        self.player_just_moved = None
        self.coin_toss = None
        self.player1_sold = None
        self.player2_choice = None

    def clone(self):
        """
        Create a deep clone of this game state.
        """
        st = CoinToss()
        st.player_just_moved = self.player_just_moved
        st.coin_toss = self.coin_toss
        st.player1_sold = self.player1_sold
        st.player2_choice = self.player2_choice
        return st

    def do_move(self, move):
        """
        Update a state by carrying out the given move.
        Must update player_just_moved.
        """
        print("before", self)
        if self.player_just_moved is None:
            self.player_just_moved = 0
            self.coin_toss = move
        if self.player_just_moved == 0:
            self.player_just_moved = 1
            self.player1_sold = move
        if self.player_just_moved == 1:
            self.player_just_moved = 2
            self.player2_choice = move
        print("after", self)

    def get_moves(self):
        """
        Get all possible moves from this state.
        """
        if self.player_just_moved is None:
            return [0, 1]
        if self.player_just_moved == 0:
            return [False, True]
        if self.player_just_moved == 1:
            return [0, 1]
        if self.player_just_moved == 2:
            return None

    def get_result(self, playerjm):
        """
        Get the game result from the viewpoint of playerjm.
        """
        # player 1 sold
        if self.player_just_moved == 1 and self.player1_sold == True:
            # player 1 sold yes
            if self.coin_toss == 1:
                if playerjm == 1:
                    return 0.5
                elif playerjm == 2:
                    return -0.5
                elif playerjm == 0:
                    return 0
            # player 1 sold no
            elif self.coin_toss == 0:
                if playerjm == 1:
                    return -0.5
                elif playerjm == 2:
                    return 0.5
                elif playerjm == 0:
                    return 0
        # player 2 guess
        elif self.player_just_moved == 2 and self.player1_sold == False:
            # player 2 guess right
            if self.coin_toss == self.player2_choice:
                if playerjm == 1:
                    return -1
                elif playerjm == 2:
                    return 1
                elif playerjm == 0:
                    return 0
            # player 2 guess wrong
            elif self.coin_toss != self.player2_choice:
                if playerjm == 1:
                    return -1
                elif playerjm == 2:
                    return 1
                elif playerjm == 0:
                    return 0
        else:
            print(self)
            raise Exception("wrong state...")


    def __repr__(self):
        """
        Don't need this - but good style.
        """
        return str(self.__dict__)

class Node(object):
    """
    A node in the game tree.
    Note wins is always from the viewpoint of playerJustMoved.
    Crashes if state not specified.
    """

    def __init__(self, move=None, parent=None, state=None):
        # the move that got us to this node - 'None' for the root node
        self.move = move
        # 'None' for the root node
        self.parent_node = parent
        self.child_nodes = []
        self.wins = 0
        self.visits = 0
        # future child nodes
        self.untried_moves = state.get_moves()
        # the only part of the state that the Node needs later
        self.player_just_moved = state.player_just_moved

    def uct_select_child(self):
        """
        Use the UCB1 formula to select a child node.
        Often a constant UCTK is applied so we have
        lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits
        to vary the amount of exploration versus exploitation.
        """
        s = sorted(self.child_nodes, key=lambda c: c.wins / c.visits + sqrt(
            2 * log(self.visits) / c.visits))[-1]
        return s

    def add_child(self, m, s):
        """
        Remove m from untried_moves and add a new child node for this move.
        Return the added child node.
        """
        n = Node(move=m, parent=self, state=s)
        self.untried_moves.remove(m)
        self.child_nodes.append(n)
        return n

    def update(self, result):
        """
        Update this node - one additional visit and result additional wins.
        Result must be from the viewpoint of player_just_moved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return '[M:' + str(self.move) + ' W/V:' + str(self.wins) + '/' + \
               str(self.visits) + ' U:' + str(self.untried_moves) + ']'

    def tree_to_string(self, indent):
        s = self.indent_string(indent) + str(self)
        for c in self.child_nodes:
            s += c.tree_to_string(indent + 1)
        return s

    @staticmethod
    def indent_string(indent):
        s = '\n'
        for i in range(1, indent + 1):
            s += '| '
        return s

    def children_to_string(self):
        s = ''
        for c in self.child_nodes:
            s += str(c) + '\n'
        return s


def uct(root_state, iter_max, verbose=False):
    """
    Conduct a UCT search for iter_max iterations starting from root_state.
    Return the best move from the root_state.
    Assumes 2 alternating players (player 1 starts),
    with game results in the range [0.0, 1.0].
    """

    root_node = Node(state=root_state)

    for i in range(iter_max):
        node = root_node
        state = root_state.clone()

        # Select
        # node is fully expanded and non-terminal
        while not node.untried_moves and node.child_nodes:
            node = node.uct_select_child()
            state.do_move(node.move)

        # Expand
        # if we can expand (i.e. state/node is non-terminal)
        if node.untried_moves:
            m = random.choice(node.untried_moves)
            state.do_move(m)
            # add child and descend tree
            node = node.add_child(m, state)

        # Rollout - this can often be made orders of magnitude quicker
        # using a state.get_random_move() function
        # while state is non-terminal
        while state.get_moves():
            state.do_move(random.choice(state.get_moves()))
        print("after get_moves", state)

        # Backpropagate
        # backpropagate from the expanded node and work back to the root node
        while node is not None:
            # state is terminal. Update node with result
            # from POV of node.playerJustMoved
            node.update(state.get_result(node.player_just_moved))
            node = node.parent_node

    # Output some information about the tree - can be omitted
    if verbose:
        print(root_node.tree_to_string(0))
    else:
        print(root_node.children_to_string())

    # return the move that was most visited
    return sorted(root_node.child_nodes, key=lambda c: c.visits)[-1].move


def uct_play_game():
    """
    Play a sample game between two UCT players
    where each player gets a different number
    of UCT iterations (= simulations = tree nodes).
    """
    # uncomment to play Othello on a square board of the given size
    # state = OthelloState(4)
    # uncomment to play OXO
    # state = OXOState()
    # uncomment to play Nim with the given number of starting chips
    state = CoinToss()
    #state = NimState(10)
    while state.get_moves():
        print(str(state))
        if state.player_just_moved == 1:
            # play with values for iter_max and verbose = True
            # Player 2
            m = uct(root_state=state, iter_max=1000, verbose=False)
        else:
            # Player 1
            m = uct(root_state=state, iter_max=100, verbose=False)
        print('Best Move: ' + str(m) + '\n')
        state.do_move(m)
    return
    if state.get_result(state.player_just_moved) == 1.0:
        print('Player ' + str(state.player_just_moved) + ' wins!')
    elif state.get_result(state.player_just_moved) == 0.0:
        print('Player ' + str(3 - state.player_just_moved) + ' wins!')
    else:
        print('Nobody wins!')


if __name__ == "__main__":
    """
    Play a single game to the end using UCT for both players.
    """
    uct_play_game()
