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
        self.player1_choice = None
        self.player2_choice = None

    def get_player_next_moved(self):
        # terminal state
        if self.player1_choice == "sell":
            return None
        if self.player_just_moved == 2:
            return None
        # non-terminal state
        if self.player_just_moved == None:
            return 0
        if self.player_just_moved == 0:
            return 1
        if self.player_just_moved == 1:
            return 2

    def get_information(self, player):
        if player == 1:
            return self.coin_toss
        elif player == 2:
            return "nothing"

    def clone(self):
        """
        Create a deep clone of this game state.
        """
        st = CoinToss()
        st.player_just_moved = self.player_just_moved
        st.coin_toss = self.coin_toss
        st.player1_choice = self.player1_choice
        st.player2_choice = self.player2_choice
        return st

    def do_move(self, move):
        """
        Update a state by carrying out the given move.
        Must update player_just_moved.
        """
        if self.player_just_moved is None:
            self.player_just_moved = 0
            self.coin_toss = move
        elif self.player_just_moved == 0:
            self.player_just_moved = 1
            self.player1_choice = move
        elif self.player_just_moved == 1:
            self.player_just_moved = 2
            self.player2_choice = move

    def get_moves(self):
        """
        Get all possible moves from this state.
        """
        if self.player_just_moved is None:
            return ["head", "tail"]
        if self.player_just_moved == 0:
            return ["sell", "play"]
        if self.player_just_moved == 1:
            if self.player1_choice == "play":
                return ["head", "tail"]
            elif self.player1_choice == "sell":
                return None
        if self.player_just_moved == 2:
            return None

    def get_result(self, playerjm):
        """
        Get the game result from the viewpoint of playerjm.
        """
        # player 1 sell
        if self.player_just_moved == 1 and self.player1_choice == "sell":
            # player 1 sell yes
            if self.coin_toss == "head":
                if playerjm == 1:
                    return 0.5
                elif playerjm == 2:
                    return -0.5
                else:
                    return 0
            # player 1 sell no
            elif self.coin_toss == "tail":
                if playerjm == 1:
                    return -0.5
                elif playerjm == 2:
                    return 0.5
                else:
                    return 0
        # player 2 guess
        elif self.player_just_moved == 2 and self.player1_choice == "play":
            # player 2 guess right
            if self.coin_toss == self.player2_choice:
                if playerjm == 1:
                    return -1
                elif playerjm == 2:
                    return 1
                else:
                    return 0
            # player 2 guess wrong
            elif self.coin_toss != self.player2_choice:
                if playerjm == 1:
                    return 1
                elif playerjm == 2:
                    return -1
                else:
                    return 0
        else:
            print(self)
            raise Exception("wrong state...")


    def __repr__(self):
        """
        Don't need this - but good style.
        """
        return str(self.__dict__)



