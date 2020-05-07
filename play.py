# Imports
import numpy as np
np.set_printoptions(suppress=True)
from shutil import copyfile
import random
import time
from importlib import reload
from game import Game, GameState
from agent import Agent
from funcs import playMatches
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
import pygame
from sys import exit
from gui import *
BACKGROUND = 'images/go.jpg'
STARTBG='images/dest.jpg'
STARTBGP='images/destp.jpg'
AIBG='images/ai.jpg'
AIBGP='images/aip.jpg'
BRAIN='images/brain.png'
BRAINP='images/brainp.jpg'
PASS='images/pass.jpg'
BLACKBG='images/black.png'
WHITEBG='images/white.jpg'
JOGO = 'images/rpp.jpg'
HOME ='images/home.jpg'
BOARD_SIZE = (820, 820)
SCREEN_SIZE = (1200,820)
WHITE = (220, 220, 220)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0) 
BLUE = (0, 0, 128)
RED=(255,0,0)
#BGC=(246,232,174)
BGC=(255,255,255)



GameInfo = GameServer()
def initialboard():
    board=[]
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

def initialboarduser():
    board=[]
    for i in range(363):
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



def theend(gboard):
    score=(str(GameInfo.score["W"]),str(GameInfo.score["B"]))
    if GameInfo.pause:
        guiboard.updateMsg("","GAME PAUSE",RED)
    else:
        if str(GameInfo.winner) == 'W':
            guiboard.updateMsg("WHITE WON","GAME ENDED",RED)
        if str(GameInfo.winner) == 'B':
            guiboard.updateMsg("BLACK WON","GAME ENDED",RED)
    gboard.updateScoreMsg(score)
    


async def main():
    #initialize game
    global GameInfo
    ai = Agent('current_player', (19, 19), 363, config.MCTS_SIMS, config.CPUCT)
        
    while True:
        env = None
        gamepos = None
        mode=-1
        playerColor=""
        oppcolor=""
        playerName="JoGo"
        playerTurn=0
        action=0
        sc=[0,0,0]
        chosen=-1
        guiboard.startmenu(startbg,aibg,brain)  
         
        while mode==-1:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        x = event.pos[0]
                        y = event.pos[1]
                        if x>865 and x<965 and y>50 and y<150:
                            if chosen==-1 or chosen==1:
                                chosen=0
                                guiboard.startmenu(startbg,aibgp,brain)
                            else:
                                chosen=-1
                                guiboard.startmenu(startbg,aibg,brain)
                        if x>1048 and x<1148 and y>50 and y<150:
                            if chosen==-1 or chosen==0:
                                chosen=1
                                guiboard.startmenu(startbg,aibg,brainp)
                            else:
                                chosen=-1
                                guiboard.startmenu(startbg,aibg,brain)
                        
                        if x>910 and x<1096 and y>500 and y<700:
                            if chosen==-1:
                                guiboard.updateMsg("","CHOOSE GAME MOOD",BLACK)
                            else:
                                guiboard.startmenu(startbgp,aibg,brain)
                                mode=chosen
                        
                                
        if mode==0:
            print("AI vs AI")
            turn = 0
            game_start = time.time()
            perv_turn = time.time()
            GameInfo.State = States.INIT
            guiboard.updateMsg("","Connecting to server..",BLACK)
            bpass = 0
            wpass = 0
            while(1):
                try:
                    if GameInfo.endgame==True:
                        theend(guiboard)
                    if GameInfo.State == States.INIT:
                        if(not await InitState(GameInfo, playerName)):
                            guiboard.updateMsg("","Connection Failed",BLACK)
                            GameInfo.State = States.INIT
                        else:
                            guiboard.updateMsg("Waiting for game start", "Connected.",BLACK) 
                    elif GameInfo.State == States.READY:
                        await ReadyState(GameInfo)
                        playerColor=str(GameInfo.PlayerColor)
                        print("Player Color is"+playerColor)
                        guiboard.updateMsg("","Game is ready!",BLACK)
                        if GameInfo.endgame==False:
                                board = initialboard()
                                if playerColor=="b" or playerColor=="B" or playerColor=="black" or playerColor=="BLACK":
                                    oppcolor="W"
                                    playerTurn=1
                                    
                                else:
                                    oppcolor="B"
                                    playerTurn=-1
                                
                                if env is None:
                                    env = Game(board, 1)
                                    env.gameState.render()
                                    gamepos = go.Position(board=initialdboard(board))
                                else:
                                    print("Environment Turn ",env.gameState.playerTurn)
                        else:
                            theend(guiboard)
                    
                        

                        
                    elif  GameInfo.State == States.IDLE:
                        await IdleState(GameInfo)
                        if GameInfo.State!= States.READY:

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
                            if action == 361 or action == 362:
                                if -1*env.gameState.playerTurn == 1:
                                    bpass += 1
                                else:
                                    wpass += 1  
                            env.gameState.renderThinkUser(guiboard, gamepos, bpass, wpass)
                            guiboard.screen.blit(jogo, (910, 300))
                            pygame.display.update()


                    elif  GameInfo.State == States.THINK:
                        action = -1
                        baction = -1
                        while action not in env.gameState.allowedActions:
                            baction, action, gamepos=ai.act(gamepos, env.gameState, turn)
                            if action not in env.gameState.allowedActions:
                                print("Invalid action")
                        typ=0
                        if action==361:
                            typ=1
                        elif action==362:
                            typ = 1
                        else:
                            typ=0
                            y =  action % 19
                            x =  math.floor(action / 19)
                        

                        await ThinkState(GameInfo, x,y,typ)
                        if GameInfo.validmove==True and GameInfo.State!=States.READY:
                            gamepos = gamepos.play_move(baction, env.gameState.playerTurn, mutate=True)
                            env.step(action)
                            if action == 361 or action == 362:
                                if -1*env.gameState.playerTurn == 1:
                                    bpass += 1
                                else:
                                    wpass += 1 
                            turn = turn + 1  
                        this_turn = time.time()
                        env.gameState.renderWaitUser(guiboard, gamepos, bpass, wpass)
                        guiboard.screen.blit(jogo, (910, 300))
                        pygame.display.update()
                except:
                    mode = -1
                    guiboard.clearboard()
            
                    break



        if mode==1:
            pygame.draw.rect(guiboard.screen, BGC,(820,0,1200,500))
            pygame.draw.rect(guiboard.screen, BGC,(820,500,1200,820))
            guiboard.screen.blit(blackbg, (865, 50))
            guiboard.screen.blit(whitebg, (1048, 50))
            guiboard.updateMsg("","CHOOSE YOUR COLOR",BLACK)
            pygame.display.update()
            usercolor=""
            while usercolor=="":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            x = event.pos[0]
                            y = event.pos[1]
                            if x>865 and x<965 and y>50 and y<150:
                                usercolor="BLACK"
                            if x>1048 and x<1148 and y>50 and y<150:
                                usercolor="WHITE"
            pygame.draw.rect(guiboard.screen, BGC,(820,0,1200,820))
            board = initialboarduser()
            env = Game(board,1)
            env.gameState.render()
            print("Here")
            
 
            gamepos = go.Position(board=initialdboard(board))
            turn = 0
            biaction = None
            aiaction = None
            bpass=0
            wpass=0
            while(True):
                turn =turn+1
                if (turn == 1 and usercolor == "BLACK") or turn != 1:
                    useraction = -2
                    if turn == 1:
                        env.gameState.renderWaitUser(guiboard, gamepos, bpass, wpass)
                    while useraction not in env.gameState.allowedActions and useraction != -1:
                        useraction=guiboard.getUserAction(passbg,usercolor, home)
                        if useraction not in env.gameState.allowedActions and useraction != -1:
                            env.gameState.renderWaitUser(guiboard, gamepos, bpass, wpass)
                            guiboard.updateMsg("TRY AGAIN","INVALID ACTION",BLACK)
                    if useraction == -1:
                        mode = -1
                        break
                    env.step(useraction)
                    if useraction == 361 or useraction ==362:
                        baction = None
                    else:
                        baction = (math.floor(useraction / 19), useraction % 19)
                    gamepos = gamepos.play_move(baction, -1*env.gameState.playerTurn, mutate=True)           
                    if useraction == 361 or useraction ==362:
                        if -1*env.gameState.playerTurn == 1:
                            bpass += 1
                        else:
                            wpass += 1
                    env.gameState.renderThinkUser(guiboard, gamepos, bpass, wpass)
                    if useraction != aiaction and aiaction is not None:
                        print("ua: ",useraction)
                        print("ai: ",aiaction)
                        print("bi: ",biaction)
                        guiboard.updateMsg(str(biaction),"BEST ACTION WAS",BLACK)
                        (x, y) = biaction
                        added_stone = Stone((y+1,x+1), RED,guiboard.screen,guiboard.background)
                        added_stone.draw()
                    elif aiaction is not None:
                        guiboard.updateMsg("SELECTED "+str(biaction),"GOOD JOB",BLACK)
                    
                else:                       
                    env.gameState.renderThinkUser(guiboard, gamepos, bpass, wpass)


                env.gameState.render()
                guiboard.screen.blit(jogo, (910, 300))
                pygame.display.update()
                aiaction = -1
                while aiaction not in env.gameState.allowedActions:
                    biaction, aiaction, gamepos=ai.act(gamepos, env.gameState, turn)
                    if aiaction not in env.gameState.allowedActions:
                        print("Invalid action")
        
                env.step(aiaction)
                gamepos = gamepos.play_move(biaction, -1*env.gameState.playerTurn, mutate=True)
                baction = None
                aiaction = None
                while aiaction not in env.gameState.allowedActions:
                    biaction, aiaction, gamepos=ai.act(gamepos, env.gameState, turn)
                    if aiaction not in env.gameState.allowedActions:
                        print("Invalid action")
                if aiaction == 361 or aiaction ==362:
                    if -1*env.gameState.playerTurn == 1:
                        bpass += 1
                    else:
                        wpass += 1
                env.gameState.renderWaitUser(guiboard, gamepos, bpass, wpass)


                #guiboard.updateMsg(str(useraction),usercolor,RED)


            
  
    
if __name__== "__main__":
    pygame.init()
    programIcon = pygame.image.load('icon.jpg')
    pygame.display.set_icon(programIcon)
    pygame.display.list_modes()
    pygame.display.set_caption('JoGo')
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    background = pygame.image.load(BACKGROUND).convert()
    guiboard = Board(screen,background)
    startbg=pygame.image.load(STARTBG).convert()
    startbgp=pygame.image.load(STARTBGP).convert()
    pygame.draw.rect(guiboard.screen, BGC,(820,0,1200,820))
    jogo=pygame.image.load(JOGO).convert()
    aibg=pygame.image.load(AIBG).convert()
    brain=pygame.image.load(BRAIN).convert()
    aibgp=pygame.image.load(AIBGP).convert()
    brainp=pygame.image.load(BRAINP).convert()
    passbg=pygame.image.load(PASS).convert()
    blackbg=pygame.image.load(BLACKBG).convert()
    whitebg=pygame.image.load(WHITEBG).convert()
    home=pygame.image.load(HOME).convert()
    guiboard.startmenu(startbg,aibg,brain)
    asyncio.get_event_loop().run_until_complete(main())

