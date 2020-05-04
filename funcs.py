import numpy as np
import random
import time
from game import Game, GameState
from agent import Agent, User
import pickle
from settings import run_folder, run_archive_folder
import ctypes
import logging
import threading
import config
from typing import List
import ctypes
import go

_estimator_so = ctypes.cdll.LoadLibrary('./score_estimator.so')

# Color.h
EMPTY = 0
BLACK = 1
WHITE = -1

_estimator_so = ctypes.cdll.LoadLibrary('./score_estimator.so')



def playMatches(EPISODES , goes_first = 0):

    
    BOARD = np.array([[0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, -1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0]])
    board = []
    for r in range(19):
        for c in range(19):
            board.append(BOARD[r,c])
    board.append(0)
    board.append(0)
    board = np.array(board)
    env = Game(board, 1)
    player1 = Agent('best_player', env.state_size, env.action_size, config.MCTS_SIMS, config.CPUCT)
    player2 = Agent('best_player', env.state_size, env.action_size, config.MCTS_SIMS, config.CPUCT)
    scores = {player1.name:0, "drawn": 0, player2.name:0}
    sp_scores = {'sp':0, "drawn": 0, 'nsp':0}
    points = {player1.name:[], player2.name:[]}
    pos = go.Position(board=BOARD)

    for e in range(EPISODES):
        print(str(e+1) + ' ', end='')
        game_start = time.time()
        state = env.reset(board)
        
        done = 0
        turn = 0

        if goes_first == 0:
            player1Starts = random.randint(0,1) * 2 - 1
        else:
            player1Starts = goes_first

        if player1Starts == 1:
            players = {1:{"agent": player1, "name":player1.name}
                    , -1: {"agent": player2, "name":player2.name}
                    }
        else:
            players = {1:{"agent": player2, "name":player2.name}
                    , -1: {"agent": player1, "name":player1.name}
                    }
        env.gameState.render()
        perv_turn = time.time()
        while done == 0:
            turn = turn + 1  
            #### Run the MCTS algo and return an action

            action, pos = players[state.playerTurn]['agent'].act(pos, state, turn)

            print(pos.score())

            this_turn = time.time()
            print()
            print()
            print()
            print("************************* TURN: ", turn," *************************")
            print("This turn took ", (this_turn-perv_turn)/60, " mins")
            print("It has been ", (this_turn-game_start)/60, " mins from the start of the game")    

            perv_turn = time.time()
            ### Do the action
            state, value, done, _ = env.step(action) #the value of the newState from the POV of the new playerTurn i.e. -1 if the previous player played a winning move
            value = pos.score()
            env.gameState.render() #Send state to GUI lib

            state.arr = ((19 * 19) * ctypes.c_int)()
            data = np.copy(state.board[0:361])
            estimated_board_score = 0
            for i, v in enumerate(data):
                state.arr[i] = v
            score = _estimator_so.estimate(19, 19, state.arr, state.playerTurn, 1000,ctypes.c_float(0.4))
            data[:] = state.arr
            current_player_score = state.playerTurn*score
            other_player_score = -state.playerTurn*score
            estimated_board_score = (current_player_score,current_player_score,other_player_score)
            print("Estimated board score: ", estimated_board_score)

            if done == 1:
                print("Done")
             
                if value > 0:
                    print('%s WINS!', players[state.playerTurn]['name'])
                    # logger.info('Player %d Wins!', state.playerTurn)
                    # logger.info(str(value))
                    scores[players[state.playerTurn]['name']] = scores[players[state.playerTurn]['name']] + 1
                    if state.playerTurn == 1: 
                        sp_scores['sp'] = sp_scores['sp'] + 1
                    else:
                        sp_scores['nsp'] = sp_scores['nsp'] + 1

                elif value < 0:
                    print('%s WINS!', players[-state.playerTurn]['name'])
                    # logger.info('Player %d Wins!', -state.playerTurn)
                    # logger.info(str(value))
                    scores[players[-state.playerTurn]['name']] = scores[players[-state.playerTurn]['name']] + 1
               
                    if state.playerTurn == 1: 
                        sp_scores['nsp'] = sp_scores['nsp'] + 1
                    else:
                        sp_scores['sp'] = sp_scores['sp'] + 1

                else:
                    print('DRAW...')
                    scores['drawn'] = scores['drawn'] + 1
                    sp_scores['drawn'] = sp_scores['drawn'] + 1

                pts = state.score
                points[players[state.playerTurn]['name']].append(pts[0])
                points[players[-state.playerTurn]['name']].append(pts[1])
                

    return (scores, points, sp_scores)
