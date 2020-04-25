from __future__ import absolute_import, division, print_function
from math import sqrt, log
import random
import copy
import time

# Node in the tree. Contains information about state of the board.
# Few functions are copied from randplay.py, some of them with a little modifications.
#
# copied: check_win, get_continuous_count, set_piece, rollout.
# copied + modified: get_options, make_moves
# new: get_control, advanced_heuristics
#
# I only added comment on the part that I changed.
class State:
    def __init__(self, grid, player, parent):
        self.grid = grid
        self.piece = player
        self.in_control = self.get_control(player)
        self.grid_count = 11
        self.maxrc = len(grid)-1
        self.visit_count = 0    # N(s)
        self.reward = 0         # Q(s)
        self.children = []      # childrens
        self.parent = parent    # parent node
        self.r = -1     # row that added on this state
        self.c = -1     # column that added on this state
        self.game_over = False
        self.winner = '.'
        self.used_option = set([])

    # Player whose in control of the state
    def get_control(self, player):
        if player == 'b':
            return 'w'
        else:
            return 'b'

    def check_win(self, r, c):
        n_count = self.get_continuous_count(r, c, -1, 0)
        s_count = self.get_continuous_count(r, c, 1, 0)
        e_count = self.get_continuous_count(r, c, 0, 1)
        w_count = self.get_continuous_count(r, c, 0, -1)
        se_count = self.get_continuous_count(r, c, 1, 1)
        nw_count = self.get_continuous_count(r, c, -1, -1)
        ne_count = self.get_continuous_count(r, c, -1, 1)
        sw_count = self.get_continuous_count(r, c, 1, -1)
        if (n_count + s_count + 1 >= 5) or (e_count + w_count + 1 >= 5) or \
                (se_count + nw_count + 1 >= 5) or (ne_count + sw_count + 1 >= 5):
            self.winner = self.grid[r][c]
            self.game_over = True

    def get_continuous_count(self, r, c, dr, dc):
        piece = self.grid[r][c]
        result = 0
        i = 1
        while True:
            new_r = r + dr * i
            new_c = c + dc * i
            if 0 <= new_r < self.grid_count and 0 <= new_c < self.grid_count:
                if self.grid[new_r][new_c] == piece:
                    result += 1
                else:
                    break
            else:
                break
            i += 1
        return result

    def set_piece(self, r, c):
        if self.grid[r][c] == '.':
            self.grid[r][c] = self.piece
            if self.piece == 'b':
                self.piece = 'w'
            else:
                self.piece = 'b'
            return True
        return False

    def get_options(self, grid):
        current_pcs = []
        for r in range(len(grid)):
            for c in range(len(grid)):
                if not grid[r][c] == '.':
                    current_pcs.append((r,c))

        # When the game grows, execute advanced_heuristic instead
        if len(current_pcs) > 10:
            return self.advanced_heuristic(current_pcs)

        if not current_pcs:
            return [(self.maxrc//2, self.maxrc//2)]

        min_r = max(0, min(current_pcs, key=lambda x: x[0])[0]-1)
        max_r = min(self.maxrc, max(current_pcs, key=lambda x: x[0])[0]+1)
        min_c = max(0, min(current_pcs, key=lambda x: x[1])[1]-1)
        max_c = min(self.maxrc, max(current_pcs, key=lambda x: x[1])[1]+1)

        options = []
        for i in range(min_r, max_r+1):
            for j in range(min_c, max_c+1):
                if not (i, j) in current_pcs:
                    options.append((i,j))

        return options

    # Advanced heuristic function.
    #
    # Since normal heuristic is inefficient when the game goes larger,
    # we are using advanced heuristic in this case.
    #
    # In this heuristic, our primary focus is on where the player's pieces are located.
    # The next movement should be around the average location of the player's pieces.
    #
    # Also, this heuristic function does 4-line checking, which terminates the game when
    # 5-pieces are available.
    def advanced_heuristic(self,curr_pcs):
            avg_r = 0
            avg_c = 0
            player = []         # all players
            opponent = set([])  # all opponents
            op_piece = []

            # Put the player's pieces together and calculate the average location
            for i in curr_pcs:
                (r,c) = i
                if self.grid[r][c] == self.piece:
                    player.append(i)
                    avg_r += r
                    avg_c += c
                else:
                    opponent.add(i)

            avg_r = int(avg_r/len(player))      # average row
            avg_c = int(avg_c/len(player))      # average column
            offset = int(log(len(player),1.8))  # offset - when game grows, offset also grows

            # 4-line checking: check 4-row, 4-column, 4-right-down, 4-left-down.
            # if 4-line and extra space is available, we fill the rest to make 5-lines.
            for rc in player:
                # 4-row checking
                (r,c) = rc
                count = 1
                skip = -1
                while True:
                    if (r+1,c) in player:
                        r = r+1
                        count += 1
                        if count >= 4:
                            break
                    else:
                        if skip == -1:
                            skip = r+1
                            r = r+1
                        else:
                            break
                if count >= 4:
                    if skip != -1 and self.grid[skip][c] == '.':
                        return [(skip,c)]
                    if r+1 <= self.maxrc and self.grid[r+1][c] == '.':
                        return [(r+1,c)]
                    if r-4 >= 0 and self.grid[r-4][c] == '.':
                        return [(r-4,c)]

                # 4-column checking
                (r,c) = rc
                count = 1
                skip = -1
                while True:
                    if (r,c+1) in player:
                        c = c+1
                        count += 1
                        if count >= 4:
                            break
                    else:
                        if skip == -1:
                            skip = c+1
                            c = c+1
                        else:
                            break
                if count >= 4:
                    if skip != -1 and self.grid[r][skip] == '.':
                        return [(r,skip)]
                    if c+1 <= self.maxrc and self.grid[r][c+1] == '.':
                        return [(r,c+1)]
                    if c-4 >= 0 and self.grid[r][c-4] == '.':
                        return [(r,c-4)]

                # 4-right-down checking
                (r,c) = rc
                count = 1
                skipp = (-1,-1)
                while True:
                    if (r+1,c+1) in player:
                        c = c+1
                        r = r+1
                        count += 1
                        if count >= 4:
                            break
                    else:
                        if skipp == (-1,-1):
                            skipp = (r+1,c+1)
                            r = r+1
                            c = c+1
                        else:
                            break
                if count >= 4:
                    if skipp != (-1,-1) and self.grid[skipp[0]][skipp[1]] == '.':
                        return [skipp]
                    if r+1 <= self.maxrc and c+1 <= self.maxrc and self.grid[r+1][c+1] == '.':
                        return [(r+1,c+1)]
                    if r-4 >= 0 and c-4 >= 0 and self.grid[r-4][c-4] == '.':
                        return [(r-4, c-4)]

                # 4-left-down checking
                (r,c) = rc
                count = 1
                skipp = (-1,-1)
                while True:
                    if (r+1,c-1) in player:
                        c = c-1
                        r = r+1
                        count += 1
                        if count >= 4:
                            break
                    else:
                        if skipp == (-1,-1):
                            skipp = (r+1,c-1)
                            r = r+1
                            c = c-1
                        else:
                            break
                if count >= 4:
                    if skipp != (-1,-1) and self.grid[skipp[0]][skipp[1]] == '.':
                        return [skipp]
                    if r+1 <= self.maxrc and c-1 >= 0 and self.grid[r+1][c-1] == '.':
                        return [(r+1,c-1)]
                    if r-4 >= 0 and c+4 <= self.maxrc and self.grid[r-4][c+4] == '.':
                        return [(r-4, c+4)]


            # 3-line defense

            # 3-line attack
            for rc in player:
                # 3-row checking
                (r,c) = rc
                count = 1
                for _ in range(0,3):
                    if (r+1,c) in player:
                        r = r+1
                        count += 1
                        if count >= 3:
                            break
  
                if count >= 3:
                    if r+1 <= self.maxrc and self.grid[r+1][c] == '.':
                        return [(r+1,c)]
                    if r-3 >= 0 and self.grid[r-3][c] == '.':
                        return [(r-3,c)]

                # 3-column checking
                (r,c) = rc
                count = 1
                for _ in range(0,3):
                    if (r,c+1) in player:
                        c = c+1
                        count += 1
                        if count >= 3:
                            break

                if count >= 3:
                    if c+1 <= self.maxrc and self.grid[r][c+1] == '.':
                        return [(r,c+1)]
                    if c-3 >= 0 and self.grid[r][c-3] == '.':
                        return [(r,c-3)]

                # 3-right-down checking
                (r,c) = rc
                count = 1
                for _ in range(0,3):
                    if (r+1,c+1) in player:
                        c = c+1
                        r = r+1
                        count += 1
                        if count >= 3:
                            break
                if count >= 3:
                    if r+1 <= self.maxrc and c+1 <= self.maxrc and self.grid[r+1][c+1] == '.':
                        return [(r+1,c+1)]
                    if r-3 >= 0 and c-3 >= 0 and self.grid[r-3][c-3] == '.':
                        return [(r-3, c-3)]

                # 3-left-down checking
                (r,c) = rc
                count = 1
                for _ in range(0,3):
                    if (r+1,c-1) in player:
                        c = c-1
                        r = r+1
                        count += 1
                        if count >= 3:
                            break

                if count >= 3:
                    if r+1 <= self.maxrc and c-1 >= 0 and self.grid[r+1][c-1] == '.':
                        return [(r+1,c-1)]
                    if r-3 >= 0 and c+3 <= self.maxrc and self.grid[r-3][c+3] == '.':
                        return [(r-3, c+3)]


 
            # minimum/maximum row/column
            min_r = max(0, avg_r - offset) 
            max_r = min(self.maxrc, avg_r + offset)
            min_c = max(0, avg_c - offset)
            max_c = min(self.maxrc, avg_c + offset)

            # Options of reasonable next step moves
            options = set([])
            for i in range(min_r, max_r+1):
                for j in range(min_c, max_c+1):
                    if not (i, j) in curr_pcs:
                        options.add((i,j))

            # return all possible options.
            to_choose = []

            if not options - self.used_option - opponent:
                # used_option is useful to increase chance of winning in mid-early stage.
                to_choose = list(options - self.used_option - opponent)
            else:
                to_choose = list(options - opponent)
            return to_choose

    def make_move(self):
        options = self.get_options(self.grid)
        if len(options) == 0:
            self.game_over = True
            self.winner = self.in_control
            return (-1,-1)
        return random.choice(options)

    def rollout(self):
        simReward = {}
        while not self.game_over:
            r,c = self.make_move();
            self.set_piece(r,c)
            self.check_win(r,c)
        #assign rewards
        if self.winner == 'b':
            simReward['b'] = 1
            simReward['w'] = 0
        elif self.winner == 'w':
            simReward['b'] = 0
            simReward['w'] = 1
        return simReward

# Implementation of Monte-Carlo Tree Search.
# Contains methods -- tree policy, default policy, etc --
# to build a tree and make a reasonable decision for the next movement.
class MCTS:
    def __init__(self, grid, player):
        self.grid = grid
        self.piece = player
        self.root_node = State(grid, player, None)
        self.grid_size = 52
        self.grid_count = 11
        self.game_over = False
        self.winner = None
        self.maxrc = len(grid)-1

    # UCT Search - perform within computational budget. (5 seconds)
    # Use Tree Policy (selection) and Default Policy (simulation) and backpropagation
    def uct_search(self):
        startTime = time.clock()
        while time.clock() < startTime + 10:
            s = self.selection(self.root_node)
            winner = self.simulation(s)
            self.backpropagation(s, winner)
        return self.action()

    # Tree Policy - (call expansion & best_child)
    def selection(self, state):
        while state.game_over == False:
            # call state.get_options() to get possible next movement
            to_choose = state.get_options(state.grid)
            # if the state if not further expandable
            if to_choose == []:
                # find the best child and repeat
                child_state = self.best_child(state)
                if child_state != None:
                    state = child_state
                else:
                    # This case will never happen unless board is mostly filled.
                    # When it happens, I made it to throw exception.
                    raise Exception('Board is filled')
            else:
                # expand the tree
                (r,c) = random.choice(to_choose)
                return self.expansion(state,r,c)
        return state

    # Expand the tree
    def expansion(self, state, r, c):
        # update the grid
        new_grid = copy.deepcopy(state.grid)
        new_grid[r][c] = self.piece
        # determine the next piece
        next_piece = None
        if self.piece == 'w':
            next_piece ='b'
        else:
            next_piece = 'w'
        # declare the child and update the tree
        child = State(new_grid, next_piece, state)  
        child.r = r
        child.c = c
        state.children.append(child)
        state.used_option.add((r,c))
        return child

    # Return child that maximizes quantity
    def best_child(self, state):
        maximum = -999999
        bestchild = None
        for child in state.children:
            # Using the formula
            temp = 0
            temp += (child.reward / child.visit_count)
            temp += sqrt(log(state.visit_count) / child.visit_count)
            if temp > maximum:
                maximum = temp
                bestchild = child
        return bestchild

    # Default Policy -- do the simulation and decide the winner
    def simulation(self, state):
        sim_state = copy.deepcopy(state)
        if sim_state.game_over == False:
            sim_state.rollout()
        return sim_state.winner

    # Back propagation -- update the visit and winning count based on who's in control of state
    def backpropagation(self, state, winner):
        while state != None:
            state.visit_count += 1  # update N(s)
            if winner == state.in_control:
                state.reward += 1   # update Q(s)
            state = state.parent

    # Return the root's child who has the biggest winning proportion 
    def action(self):
        maximum = -999999
        bestchild = None
        for child in self.root_node.children:
            temp = (child.reward / child.visit_count)
            if temp > maximum:
                maximum = temp
                bestchild = child
        return (bestchild.r, bestchild.c)

    # A function called from and returns to board.py
    def make_move(self):
        return self.uct_search()


