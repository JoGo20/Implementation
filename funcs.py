import numpy as np
import random
import time
import loggers as lg

from game import Game, GameState
#from model import Residual_CNN

from agent import Agent, User


import pickle
from settings import run_folder, run_archive_folder
import ctypes
import logging
import threading
import config
from typing import List
import ctypes

_estimator_so = ctypes.cdll.LoadLibrary('./score_estimator.so')

# Color.h
EMPTY = 0
BLACK = 1
WHITE = -1

_estimator_so = ctypes.cdll.LoadLibrary('./score_estimator.so')



# def playMatchesBetweenVersions(env, run_version, player1version, player2version, EPISODES, logger, turns_until_tau0, goes_first = 0):
    
#     if player1version == -1:
#         player1 = User('player1', env.state_size, env.action_size)
#     else:
#         player1_NN = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, env.input_shape,   env.action_size, config.HIDDEN_CNN_LAYERS)

#         if player1version > 0:
#             player1_network = player1_NN.read(env.name, run_version, player1version)
#             player1_NN.model.set_weights(player1_network.get_weights())   
#         player1 = Agent('player1', env.state_size, env.action_size, config.MCTS_SIMS, config.CPUCT, player1_NN)

#     if player2version == -1:
#         player2 = User('player2', env.state_size, env.action_size)
#     else:
#         player2_NN = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, env.input_shape,   env.action_size, config.HIDDEN_CNN_LAYERS)
        
#         if player2version > 0:
#             player2_network = player2_NN.read(env.name, run_version, player2version)
#             player2_NN.model.set_weights(player2_network.get_weights())
#         player2 = Agent('player2', env.state_size, env.action_size, config.MCTS_SIMS, config.CPUCT, player2_NN)

#     scores, memory, points, sp_scores = playMatches(player1, player2, EPISODES, logger, turns_until_tau0, None, goes_first)

#     return (scores, memory, points, sp_scores)


def playMatches(player1, player2, EPISODES, logger, turns_until_tau0, memory = None, goes_first = 0):

    env = Game()
    scores = {player1.name:0, "drawn": 0, player2.name:0}
    sp_scores = {'sp':0, "drawn": 0, 'nsp':0}
    points = {player1.name:[], player2.name:[]}

    for e in range(EPISODES):

        # logger.info('====================')
        # logger.info('EPISODE %d OF %d', e+1, EPISODES)
        # logger.info('====================')

        print(str(e+1) + ' ', end='')
        game_start = time.time()
        state = env.reset()
        
        done = 0
        turn = 0
        player1.mcts = None
        player2.mcts = None

        if goes_first == 0:
            player1Starts = random.randint(0,1) * 2 - 1
        else:
            player1Starts = goes_first

        if player1Starts == 1:
            players = {1:{"agent": player1, "name":player1.name}
                    , -1: {"agent": player2, "name":player2.name}
                    }
            # logger.info(player1.name + ' plays as B')
        else:
            players = {1:{"agent": player2, "name":player2.name}
                    , -1: {"agent": player1, "name":player1.name}
                    }
            # logger.info(player2.name + ' plays as B')
            # logger.info('--------------')

        env.gameState.render(logger)
        perv_turn = time.time()
        while done == 0:


            turn = turn + 1
            
            
            #### Run the MCTS algo and return an action
            if turn < turns_until_tau0:
                action, pi, MCTS_value, NN_value = players[state.playerTurn]['agent'].act(state, 1)
            else:
                action, pi, MCTS_value, NN_value = players[state.playerTurn]['agent'].act(state, 0)

            this_turn = time.time()
            print()
            print()
            print()
            print("************************* TURN: ", turn," *************************")
            print("This turn took ", (this_turn-perv_turn)/60, " mins")
            print("It has been ", (this_turn-game_start)/60, " mins from the start of the game")    
            if memory != None:
                print("Tree length: ",players[state.playerTurn]['agent'].mcts.__len__())
                print('SHORT TERM MEMORY SIZE: ' + str(len(memory.stmemory)))
                print('LONG TERM MEMORY SIZE: ' + str(len(memory.ltmemory)))
                ####Commit the move to memory
                memory.commit_stmemory(env.identities, state, pi)

                #players[state.playerTurn]['agent'].mcts._delGarbageNodes(players[state.playerTurn]['agent'].mcts.root,action)
                #players[state.playerTurn]['agent'].mcts.tree.clear()
            perv_turn = time.time()
            # logger.info('action: %d', action)
            # for r in range(env.grid_shape[0]):
            #     logger.info(['----' if x == 0 else '{0:.2f}'.format(np.round(x,2)) for x in pi[env.grid_shape[1]*r : (env.grid_shape[1]*r + env.grid_shape[1])]]) 
            # logger.info('MCTS perceived value for %s: %f', state.pieces[str(state.playerTurn)] ,np.round(MCTS_value,2))
            # logger.info('NN perceived value for %s: %f', state.pieces[str(state.playerTurn)] ,np.round(NN_value,2))
            # logger.info('====================')

            ### Do the action
            state, value, done, _ = env.step(action) #the value of the newState from the POV of the new playerTurn i.e. -1 if the previous player played a winning move
            
            env.gameState.render(logger) #Send state to GUI lib

            arr = ((19 * 19) * ctypes.c_int)()
            data = np.copy(state.board[0:361])
            estimated_board_score = 0
            for i, v in enumerate(data):
                arr[i] = v
            score = _estimator_so.estimate(19, 19, arr, state.playerTurn, 1000,ctypes.c_float(0.4))
            data[:] = arr
            current_player_score = state.playerTurn*score
            other_player_score = -state.playerTurn*score
            estimated_board_score = (current_player_score,current_player_score,other_player_score)
            print("Estimated board score: ", estimated_board_score)
            if(turn>22):
                done = 1
                value = estimated_board_score[0]

            if done == 1 or estimated_board_score[0] > 100:
                print("Done")
                if estimated_board_score[0] > 100:
                    print("Player playing with ", state.pieces[str(state.playerTurn)], " won by resignation")
                    value += estimated_board_score[0]
                    done =1
                if memory != None:
                    #### If the game is finished, assign the values correctly to the game moves
                    for move in memory.stmemory:
                        if move['playerTurn'] == state.playerTurn:
                            move['value'] = value
                        else:
                            move['value'] = -value
                         
                    memory.commit_ltmemory()
             
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
                

    return (scores, memory, points, sp_scores)
