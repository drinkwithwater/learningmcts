
from coin_toss import CoinToss
import random
import enum


class StrategyState(object):
    def __init__(self, info_list, action_list):
        self.info_list = info_list
        self.action_list = action_list
        self.pi = {info:{action:1/len(action_list) for action in action_list} for info in info_list}
        self.regret = {info:{action:0 for action in action_list} for info in info_list}
        self.info_turn = {info:0 for info in info_list}
        self.pi_sum = {info:{action:0 for action in action_list} for info in info_list}

    def get_pi(self, info, action):
        return self.pi[info][action]

    def update_pi(self, info):
        move_to_regret = self.regret[info]
        all_regret = 0
        positive_regret = {}
        for move, regret in move_to_regret.items():
            if regret > 0:
                all_regret += regret
                positive_regret[move] = regret
            else:
                positive_regret[move] = 0
        if all_regret <= 0:
            self.pi[info] = {action:1/len(self.action_list) for action in self.action_list}
        else:
            self.pi[info] = {action:positive_regret[action] / all_regret for action in self.action_list}
        for action in self.action_list:
            self.pi_sum[info][action] += self.pi[info][action]

    def update_regret(self, cfr_node, opponent_p):
        player = cfr_node.state.get_player_next_moved()
        info = cfr_node.state.get_information(player)
        u_old = cfr_node.utility[player]
        t = self.info_turn[info]
        for move, sub_node in cfr_node.sub_nodes.items():
            regret = self.regret[info][move]
            u_next = sub_node.utility[player]
            self.regret[info][move] = (regret * t + opponent_p * (u_next - u_old))/(t+1)
            #if self.info_list[0] == "nothing":
                #print(move, opponent_p, u_old, u_next)
        self.info_turn[info] = t + 1

    def __repr__(self):
        return str(dict(pi=self.pi, regret=self.regret, info_turn=self.info_turn))


pi = {1:StrategyState(["head", "tail"], ["sell", "play"]), 2:StrategyState(["nothing"], ["head", "tail"])}

#pi[2].pi = {"nothing":{"head":0.25, "tail":0.75}}

class CFRNode(object):
    def __init__(self, move=None, parent=None, state=None):
        # the move that got us to this node - 'None' for the root node
        self.move = move
        # 'None' for the root node
        self.parent_node = parent
        self.utility = None
        self.sub_nodes = {}
        # the only part of the state that the Node needs later
        self.player_just_moved = state.player_just_moved
        self.state = state

    def walktree(self, p1, p2, sequence):
        player = self.state.get_player_next_moved()
        if player is None:
            self.utility = {
                    1:self.state.get_result(1),
                    2:self.state.get_result(2),
                    }
            return
        if player == 0:
            next_state = self.state.clone()
            move = sequence[0]
            next_state.do_move(move)
            next_node = CFRNode(move, self, next_state)
            next_node.walktree(p1, p2, sequence[1:])
            self.sub_nodes[move] = next_node
            self.utility = next_node.utility.copy()
        else:
            info = self.state.get_information(player)
            pi[player].update_pi(info)
            utility = {1:0, 2:0}
            for move in self.state.get_moves():
                next_state = self.state.clone()
                next_state.do_move(move)
                pi_action = pi[player].get_pi(info, move)
                next_node = CFRNode(move, self, next_state)
                if player == 1:
                    next_node.walktree(p1*pi_action, p2, sequence)
                elif player == 2:
                    next_node.walktree(p1, p2*pi_action, sequence)
                self.sub_nodes[move] = next_node
                for k in [1,2]:
                    utility[k] += pi_action*next_node.utility[k]
            self.utility = utility
            if player == 1:
                pi[player].update_regret(self, p2)
            else:
                pi[player].update_regret(self, p1)
    def __repr__(self):
        if len(self.sub_nodes) == 0:
            return str(self.utility)
        else:
            #return str([self.sub_nodes, self.utility])
            #return str(self.sub_nodes)
            return str(self.utility)



if __name__=="__main__":
    for i in range(100):
        root_node = CFRNode(state=CoinToss())
        #sequence0 = "head" if i % 2 == 0 else "tail"
        sequence0 = random.choice(["head", "tail"])
        root_node.walktree(1,1, [sequence0])
        print(sequence0, root_node)
        print(pi[1].pi_sum)
        print(pi[2].pi_sum, pi[2].regret)
