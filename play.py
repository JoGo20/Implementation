# Imports
import numpy as np
np.set_printoptions(suppress=True)
from shutil import copyfile
import random
import time
import loggers as lg
from importlib import reload
from keras.utils import plot_model
from game import Game, GameState
from agent import Agent
from funcs import playMatches
import loggers as lg
from settings import run_folder, run_archive_folder
import initialise
import pickle
import config
from client import *
import ctypes
import logging
import threading
from typing import List
import ctypes
import go
import asyncio
import math

GameInfo = GameServer()
def initialboard():
    board=[]
    f=open("gui4.txt", "w")
    f.write("0\r\n" )
    GameInfo.board = np.zeros([19,19])
    for i in range(19):
        for j in range(19):
            if GameInfo.board[i][j]=="B":
                board.append(1)
            elif GameInfo.board[i][j]=="W":
                board.append(-1)
            else:
                board.append(0)
    board.append(0)
    board.append(0)
    return board
    
def initialdboard(iboard):
    board=[]
    for r in range(19):
        row=[]
        for c in range(19):
            row.append(iboard[r*19+c])
        board.append(row)
    return np.array(board)



def theend():
    f=open("gui4.txt", "w")
    f.write("1\r\n" )
    f.write("B %d \r\n" %GameInfo.score["B"])
    f.write("W %d \r\n" %GameInfo.score["W"])


async def main():
    #initialize game
    global GameInfo
    env = None
    gamepos = None
    mode=-1
    playerColor=""
    oppcolor=""
    playerName="JoGo"
    playerTurn=0
    action=0
    sc=[0,0,0]
    
    ai = None
    while mode==-1:
        f=open("gui3.txt", "r")
        f1=f.readlines()
        j=0
        for i in f1:
            if j==0:
                #if mode =0 --> AI Vs AI else mode=1--> AI VS User
                mode=int(i)
            if j==1:
                #PlayerNum=0 --> black(player1) 1--> white(player2)
                playerColor=str(i)
            j=j+1
        
    
    if mode==0:
        print("AI vs AI")
        turn = 0
        game_start = time.time()
        perv_turn = time.time()
        GameInfo.State = States.INIT
        while(1):
            print("Waiting for server")
            # print(type(GameInfo.RemainTime))
            # print(GameInfo.score)
           
            if GameInfo.State == States.INIT:
                print("Initialized")
                await InitState(GameInfo, playerName)
            elif GameInfo.State == States.READY:
                await ReadyState(GameInfo)
                playerColor=GameInfo.PlayerColor
                
                if GameInfo.endgame==False:
                        board = initialboard()
                        if playerColor=="B":
                            oppcolor="W"
                            playerTurn=1
                        else:
                            oppcolor="B"
                            playerTurn=-1
                        if env is None:
                            env = Game(board, 1)
                            env.gameState.render()
                            ai = Agent('current_player', env.state_size, env.action_size, config.MCTS_SIMS, config.CPUCT)
                            gamepos = go.Position(board=initialdboard(board))
                else:
                    theend()
            
                

                
            elif  GameInfo.State == States.IDLE:
                await IdleState(GameInfo)
                action = None
                baction = None
                if GameInfo.getOppMove(0)==-1:
                    if playerColor=="B":
                        action=362
                    else:
                        action=361
                elif GameInfo.getOppMove(0)==-2:
                    pass
                else:
                    baction = (int(GameInfo.getOppMove(0)),int(GameInfo.getOppMove(1)))
                    action=int(GameInfo.getOppMove(0))*19+int(GameInfo.getOppMove(1))
                gamepos = gamepos.play_move(baction, env.gameState.playerTurn, mutate=True)
                env.step(action)
                turn = turn + 1  
                this_turn = time.time()
                print()
                print()
                print()
                print("************************* TURN: ", turn," *************************")
                print("This turn took ", (this_turn-perv_turn)/60, " mins")
                print("It has been ", (this_turn-game_start)/60, " mins from the start of the game") 
                env.gameState.render()
                env.gameState.renderThink()


            elif  GameInfo.State == States.THINK:

                action, gamepos=ai.act(gamepos, env.gameState, turn)
                print(gamepos.score())
                typ=0
                if action==361:
                    typ=1
                elif action==362:
                    typ = 1
                else:
                    typ=0
                    y =  action % 19
                    x =  math.floor(action / 19)
                
                env.step(action)
                await ThinkState(GameInfo, x,y,typ)
                turn = turn + 1  
                this_turn = time.time()
                print()
                print()
                print()
                print("************************* TURN: ", turn," *************************")
                print("This turn took ", (this_turn-perv_turn)/60, " mins")
                print("It has been ", (this_turn-game_start)/60, " mins from the start of the game") 
                env.gameState.render()
                env.gameState.renderWait()



    # if mode==1:
    #     player = User('player', env.state_size, env.action_size)
    #     if playerColor=="B":
    #         playMatches(player, ai, EPISODES=0, lg.logger_main, turns_until_tau0 = config.TURNS_UNTIL_TAU0, memory = None, goes_first = 1)
    #     else:
    #         playMatches(ai, player, EPISODES=0, lg.logger_main, turns_until_tau0 = config.TURNS_UNTIL_TAU0, memory = None, goes_first = 1)

            
  
    
if __name__== "__main__":
   asyncio.get_event_loop().run_until_complete(main())

