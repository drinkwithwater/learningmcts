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


class GameState(object):
    """
    A state of the game, i.e. the game board. These are the only functions
    which are absolutely necessary to implement UCT in any 2-player complete
    information deterministic zero-sum game, although they can be enhanced and
    made quicker, for example by using a GetRandomMove() function to generate
    a random move during rollout.
    By convention the players are numbered 1 and 2.
    """

    def __init__(self):
        # At the root pretend the player just moved is player 2
        # so player 1 has the first move
        self.player_just_moved = 2

    def clone(self):
        """
        Create a deep clone of this game state.
        """
        st = GameState()
        st.player_just_moved = self.player_just_moved
        return st

    def do_move(self, move):
        """
        Update a state by carrying out the given move.
        Must update player_just_moved.
        """
        self.player_just_moved = 3 - self.player_just_moved

    def get_moves(self):
        """
        Get all possible moves from this state.
        """
        pass

    def get_result(self, playerjm):
        """
        Get the game result from the viewpoint of playerjm.
        """
        pass

    def __repr__(self):
        """
        Don't need this - but good style.
        """
        pass


class NimState(GameState):
    """
    A state of the game Nim. In Nim, players alternately take 1,2 or 3 chips
    with the winner being the player to take the last chip.
    In Nim any initial state of the form 4n+k for k = 1,2,3 is a win
    for player 1 (by choosing k) chips.
    Any initial state of the form 4n is a win for player 2.
    """

    def __init__(self, ch):
        super(NimState, self).__init__()
        self.chips = ch

    def clone(self):
        st = NimState(self.chips)
        st.player_just_moved = self.player_just_moved
        return st

    def do_move(self, move):
        assert 1 <= move <= 3 and move == int(move)
        self.chips -= move
        self.player_just_moved = 3 - self.player_just_moved

    def get_moves(self):
        return list(range(1, min([4, self.chips + 1])))

    def get_result(self, playerjm):
        assert self.chips == 0
        if self.player_just_moved == playerjm:
            # playerjm took the last chip and has won
            return 1.0
        else:
            # playerjm's opponent took the last chip and has won
            return 0.0

    def __repr__(self):
        s = 'Chips:' + str(self.chips) + \
            ' JustPlayed:' + str(self.player_just_moved)
        return s


class OXOState(GameState):
    """
    A state of the game, i.e. the game board.
    Squares in the board are in this arrangement
    012
    345
    678
    where 0 = empty, 1 = player 1 (X), 2 = player 2 (O)
    """

    def __init__(self):
        super(OXOState, self).__init__()
        # 0 = empty, 1 = player 1, 2 = player 2
        self.board = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    def clone(self):
        st = OXOState()
        st.player_just_moved = self.player_just_moved
        st.board = self.board[:]
        return st

    def do_move(self, move):
        assert 0 <= move <= 8 and move == int(move) and self.board[move] == 0
        self.player_just_moved = 3 - self.player_just_moved
        self.board[move] = self.player_just_moved

    def get_moves(self):
        return [i for i in range(9) if self.board[i] == 0]

    def get_result(self, playerjm):
        for (x, y, z) in [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
                          (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]:
            if self.board[x] == self.board[y] == self.board[z]:
                if self.board[x] == playerjm:
                    return 1.0
                else:
                    return 0.0
        if not self.get_moves():
            # draw
            return 0.5
        # Should not be possible to get here
        assert False

    def __repr__(self):
        s = ''
        for i in range(9):
            s += '.XO'[self.board[i]]
            if i % 3 == 2:
                s += '\n'
        return s


class OthelloState(GameState):
    """
    A state of the game of Othello, i.e. the game board.
    The board is a 2D array
    where 0 = empty (.), 1 = player 1 (X), 2 = player 2 (O).
    In Othello players alternately place pieces on
    a square board - each piece played has to sandwich opponent pieces
    between the piece played and pieces already on the board.
    Sandwiched pieces are flipped. This implementation modifies the rules
    to allow variable sized square boards and terminates the game as soon as
    the player about to move cannot make a move
    (whereas the standard game allows for a pass move).
    """

    def __init__(self, sz=8):
        super(OthelloState, self).__init__()
        # 0 = empty, 1 = player 1, 2 = player 2
        self.board = []
        self.size = sz
        # size must be integral and even
        assert sz == int(sz) and sz % 2 == 0
        for y in range(sz):
            self.board.append([0] * sz)
        self.board[sz // 2][sz // 2] = self.board[sz // 2 - 1][sz // 2 - 1] = 1
        self.board[sz // 2][sz // 2 - 1] = self.board[sz // 2 - 1][sz // 2] = 2

    def clone(self):
        st = OthelloState()
        st.player_just_moved = self.player_just_moved
        st.board = [self.board[i][:] for i in range(self.size)]
        st.size = self.size
        return st

    def do_move(self, move):
        (x, y) = (move[0], move[1])
        assert x == int(x) and y == int(y) and \
               self.is_on_board(x, y) and self.board[x][y] == 0
        m = self.get_all_sandwiched_counters(x, y)
        self.player_just_moved = 3 - self.player_just_moved
        self.board[x][y] = self.player_just_moved
        for (a, b) in m:
            self.board[a][b] = self.player_just_moved

    def get_moves(self):
        return [(x, y) for x in range(self.size)
                for y in range(self.size)
                if self.board[x][y] == 0 and
                self.exists_sandwiched_counter(x, y)]

    def adjacent_to_enemy(self, x, y):
        """
        Speeds up get_moves by only considering squares
        which are adjacent to an enemy-occupied square.
        """
        for (dx, dy) in [(0, +1), (+1, +1), (+1, 0), (+1, -1), (0, -1),
                         (-1, -1), (-1, 0), (-1, +1)]:
            if self.is_on_board(x + dx, y + dy) and \
                    self.board[x + dx][y + dy] == self.player_just_moved:
                return True
        return False

    def adjacent_enemy_directions(self, x, y):
        """
        Speeds up get_moves by only considering squares
        which are adjacent to an enemy-occupied square.
        """
        es = []
        for (dx, dy) in [(0, +1), (+1, +1), (+1, 0), (+1, -1),
                         (0, -1), (-1, -1), (-1, 0), (-1, +1)]:
            if self.is_on_board(x + dx, y + dy) and \
                    self.board[x + dx][y + dy] == self.player_just_moved:
                es.append((dx, dy))
        return es

    def exists_sandwiched_counter(self, x, y):
        """
        Does there exist at least one counter which would be flipped
        if my counter was placed at (x,y)?
        """
        for (dx, dy) in self.adjacent_enemy_directions(x, y):
            if len(self.sandwiched_counters(x, y, dx, dy)) > 0:
                return True
        return False

    def get_all_sandwiched_counters(self, x, y):
        """
        Is (x,y) a possible move (i.e. opponent counters are sandwiched
        between (x,y) and my counter in some direction)?
        """
        sandwiched = []
        for (dx, dy) in self.adjacent_enemy_directions(x, y):
            sandwiched.extend(self.sandwiched_counters(x, y, dx, dy))
        return sandwiched

    def sandwiched_counters(self, x, y, dx, dy):
        """
        Return the coordinates of all opponent counters sandwiched
        between (x,y) and my counter.
        """
        x += dx
        y += dy
        sandwiched = []
        while self.is_on_board(x, y) and \
                self.board[x][y] == self.player_just_moved:
            sandwiched.append((x, y))
            x += dx
            y += dy
        if self.is_on_board(x, y) and \
                self.board[x][y] == 3 - self.player_just_moved:
            return sandwiched
        else:
            # nothing sandwiched
            return []

    def is_on_board(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def get_result(self, playerjm):
        jmcount = len([(x, y) for x in range(self.size)
                       for y in range(self.size)
                       if self.board[x][y] == playerjm])
        notjmcount = len([(x, y) for x in range(self.size)
                          for y in range(self.size)
                          if self.board[x][y] == 3 - playerjm])
        if jmcount > notjmcount:
            return 1.0
        elif notjmcount > jmcount:
            return 0.0
        else:
            # draw
            return 0.5

    def __repr__(self):
        s = ''
        for y in range(self.size - 1, -1, -1):
            for x in range(self.size):
                s += '.XO'[self.board[x][y]]
            s += '\n'
        return s


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
    state = NimState(15)
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
