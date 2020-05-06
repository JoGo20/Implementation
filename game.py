'''
Developer: Ahmed Mokhtar
MI: Implementation Team
JoGo
14 March 2020
'''
import numpy as np
from typing import List
import ctypes
import logging
import threading
import config
from gui import *


_estimator_so = ctypes.cdll.LoadLibrary('./score_estimator.so')

# Color.h
EMPTY = 0
BLACK = 1
WHITE = -1

#   Estimate the score and area using the OGS score estimator.
#   The `data` argument must be a `height` * `width` iterable indicating
#   where player stones are.
#   Return value is the difference between black score and white score
#   (positive means back has more on the board).
#   The `data` argument is modified in-place and will indicate the player
#   that the position.

class ActionThread (threading.Thread):
   def __init__(self, threadID, stact, fnact, state):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.stact = stact
      self.fnact = fnact
      self.state = state
   def run(self):
       self.state._threadAction(self.stact,self.fnact)



class Game:
    def __init__(self, board, turn):
        # BLACK GOES FIRST
        self.currentPlayer = turn
        # 19*19 PLACES EQUALS 361 BOARD STATE SPACE.
        # 2 STATE SPACES FOR BOTH PLAYER TO PASS THEIR TURN.
        # 363 STATE SPACE. 0 TO 362
        self.board_history = []
        self.game_score = [0,0,0]
        self.gameState=GameState(np.array(board),self.currentPlayer,self.board_history,  self.game_score)
        self.board_history.append(board)
        self.actionSpace = np.array(np.zeros(363), dtype = np.int)
        # Positive Numbers reperesent the black number of liberties where 1 has no liberties and 5 has 4 liberties.
        # Negative numbers reperesent the white number of liberties where -1 has no liberties and -5 has 4 liberties.
        # 0 means an empty interesection in the GO board.
        self.pieces = {'1':'B', '0':'-', '-1':'W'}
        self.grid_shape = (19, 19)
        # # 19*19 Board State binary bits times 2 for each to be used by agents to their neural network.
        self.input_shape = (2, 19, 19)
        self.name = 'go'
        self.state_size = len(self.gameState.binary)
        self.action_size = len(self.actionSpace)

    def reset(self, board):
        del self.board_history[:]
        self.game_score = [0,0,0]
        self.gameState = GameState(board, 1,self.board_history,  self.game_score)
        self.currentPlayer = 1
        return self.gameState
    

    def step(self, action):
        next_state, value, done = self.gameState.takeAction(action)
        self.gameState = next_state
        self.currentPlayer = -self.currentPlayer
        info = None
        return ((next_state, value, done, info))


    def identities(self, state, actionValues):
        identities = [(state, actionValues)]
        currentBoard = state.board
        currentAV = actionValues

        # The structure of the board state in memory
        cb = []
        for i in range(19):
           for j in range(18, -1, -1):
              cb.append(currentBoard[i+j])
        cb.append(currentBoard[362])
        cb.append(currentBoard[361])
        currentBoard = np.array(cb)
        # The structure of the action values in memory
        
        av = []
        for i in range(19):
            for j in range(18, -1, -1):
                av.append(currentAV[i+j])
                
        av.append(currentAV[362])
        av.append(currentAV[361])
        currentAV = np.array(av)
        
        identities.append((GameState(currentBoard, state.playerTurn, self.board_history,  self.game_score), currentAV))
        
        return identities
    
    
class GameState():
    def __init__(self, board, playerTurn, board_history, game_score):
        self.board = board
        self.pieces = {'1':'B', '0':'-', '-1':'W'}
        self.initialPlaces = [60,66,72,174,180,186,288,294,300]
        self.visited={}
        self.processed = []
        self.playerTurn = playerTurn
        self.binary = self._binary()
        self.id = self._convertStateToId()
        self.board_history = board_history
        self.allowedActions = []
        self._allowedActions()
        self.game_score = [0,0,0]
        self.perv_score = game_score
        self.isEndGame = self._checkForEndGame()


 
        if(self.isEndGame and self.playerTurn == -1):
            self.arr = ((19 * 19) * ctypes.c_int)()
            data = np.copy(self.board[0:361])
            for i, v in enumerate(data):
                self.arr[i] = v
            score = _estimator_so.estimate(19, 19, self.arr, self.playerTurn, 1000,ctypes.c_float(0.4))
            data[:] = self.arr
            current_player_score = self.playerTurn*score + self.perv_score[0]
            other_player_score = -self.playerTurn*score - self.perv_score[0]
            self.value = (current_player_score,current_player_score,other_player_score)
        else:
            self.value = self.perv_score
        self.score = self._getScore()
        #self.estimate.__annotations__ = { 'width': int, 'height': int, 'data': List[int], 'player_to_move': int, 'trials': int, 'tolerance': float, 'return': int,} 
    
    def _checkNeighbours(self, action):
         place = (action) % 19
         isLower = (action >= 342)
         isUpper = (action <= 18)
        
         #Upper Left Corner with 2 Liberties
         if isUpper and place ==0:
             if self.playerTurn == 1:
                 if self.board[action+1] != 0 and self.board[action+19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action+1] != 0 and self.board[action+19] != 0:
                     return False
                
         #Upper Right Corner with 2 Liberties
         elif isUpper and place ==18:
             if self.playerTurn == 1:
                 if self.board[action-1] != 0 and self.board[action+19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action-1] != 0 and self.board[action+19] != 0:
                     return False

         #Lower Left Corner with 2 Liberties
         elif isLower and place ==0:
             if self.playerTurn == 1:
                 if self.board[action+1] != 0 and self.board[action-19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action+1] != 0 and self.board[action-19] != 0:
                     return False
                
         #Lower Right Corner with 2 Liberties
         elif isLower and place ==18:
             if self.playerTurn == 1:
                 if self.board[action-1] != 0 and self.board[action-19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action-1] != 0 and self.board[action-19] != 0:
                     return False
        
    #     #Upper Edge with 3 Liberties
         elif isUpper:
             if self.playerTurn == 1:
                 if self.board[action-1] != 0 and self.board[action+19] != 0 and self.board[action+1] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action-1] != 0 and self.board[action+19] != 0 and self.board[action+1] != 0:
                     return False
                
    #     #Lower Edge with 3 Liberties
         elif isLower:
             if self.playerTurn == 1:
                 if self.board[action+1] != 0 and self.board[action-1] != 0 and self.board[action-19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action+1] != 0 and self.board[action-1] != 0 and self.board[action-19] != 0:
                     return False
        
    #     #Right Edge with 3 Liberties
         elif place == 18:
             if self.playerTurn == 1:
                 if self.board[action-1] != 0 and self.board[action-19] != 0 and self.board[action+19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action-1] != 0 and self.board[action-19] != 0 and self.board[action+19] != 0:
                     return False
                
    #     #Left Edge with 3 Liberties
         elif place == 0:
             if self.playerTurn == 1:
                 if self.board[action+1] != 0 and self.board[action-19] != 0 and self.board[action+19] != 0:
                     return False
             elif self.playerTurn == -1:
                 if self.board[action+1] != 0 and self.board[action-19] != 0 and self.board[action+19] != 0:
                     return False
                
        
    #     #Otherwise on the board with 4 Liberties
         elif self.playerTurn == 1:
             if self.board[action+1] != 0 and self.board[action-1] != 0 and self.board[action-19] != 0 and self.board[action+19] != 0:
                 return False
         elif self.playerTurn == -1:
             if self.board[action+1] != 0 and self.board[action-1] != 0 and self.board[action-19] != 0 and self.board[action+19] != 0:
                 return False
        
         return True
          

    def _getNeighbours(self, action):
         place = (action) % 19
         isLower = (action >= 342)
         isUpper = (action <= 18)
         actionNeigh = []
         if self.board[action] == 0:
             actionNeigh.append(action)
        
         #Upper Left Corner with 2 Liberties
         if isUpper and place ==0:
            if self.board[action+1] == 0:
                actionNeigh.append(action+1)
                
            if self.board[action+19] == 0:
                actionNeigh.append(action+19)
                
                
         #Upper Right Corner with 2 Liberties
         elif isUpper and place ==18:
            if self.board[action-1] == 0:
                actionNeigh.append(action-1)
                
            if self.board[action+19] == 0:
                actionNeigh.append(action+19)

         #Lower Left Corner with 2 Liberties
         elif isLower and place ==0:
            if self.board[action+1] == 0:
                actionNeigh.append(action+1)
                
            if self.board[action-19] == 0:
                actionNeigh.append(action-19)
                
    #     #Lower Right Corner with 2 Liberties
         elif isLower and place ==18:
            if self.board[action-1] == 0:
                actionNeigh.append(action-1)
                
            if self.board[action-19] == 0:
                actionNeigh.append(action-19)
        
    #     #Upper Edge with 3 Liberties
         elif isUpper:
            if self.board[action-1] == 0:
                actionNeigh.append(action-1)
            if self.board[action+1] == 0:
                actionNeigh.append(action+1)
                
            if self.board[action+19] == 0:
                actionNeigh.append(action+19)
                
    #     #Lower Edge with 3 Liberties
         elif isLower:
            if self.board[action-1] == 0:
                actionNeigh.append(action-1)
            if self.board[action+1] == 0:
                actionNeigh.append(action+1)
                
            if self.board[action-19] == 0:
                actionNeigh.append(action-19)
        
    #     #Right Edge with 3 Liberties
         elif place == 18:
            if self.board[action-1] == 0:
                actionNeigh.append(action-1)
            if self.board[action-19] == 0:
                actionNeigh.append(action-19)
                
            if self.board[action+19] == 0:
                actionNeigh.append(action+19)
                
    #     #Left Edge with 3 Liberties
         elif place == 0:
            if self.board[action+1] == 0:
                actionNeigh.append(action+1)
            if self.board[action-19] == 0:
                actionNeigh.append(action-19)
                
            if self.board[action+19] == 0:
                actionNeigh.append(action+19)
                
        
    #     #Otherwise on the board with 4 Liberties
         else:
            if self.board[action-1] == 0:
                actionNeigh.append(action-1)
            if self.board[action+1] == 0:
                actionNeigh.append(action+1)     
            if self.board[action-19] == 0:
                actionNeigh.append(action-19)
                
            if self.board[action+19] == 0:
                actionNeigh.append(action+19)
        
         return actionNeigh

    def _generateLibMap(self, element, turn, action):
        #visited=np.full(361,-1)
        connected = []
        newarr=np.array(np.zeros(361), dtype=np.int)
        def findLiberty(i,typ,taken,vis, action):
            if i in vis:
                return 0
            else:
                vis.append(i)
                if element[i]==0:
                    if i in taken:
                        return 0
                    else:
                        taken.append(i)
                        if element[action] == typ:
                            return 1 
                        else:
                            return 0    
                elif element[i]!=typ: 
                    return 0
                else:
                    action = i
                    connected.append(i)
                    place = (i) % 19
                    isLower = (i >= 342)
                    isUpper = (i <= 18)
                    if i == 0:
                        return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)
                    elif i==18:
                        return findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)
                    elif i==342:
                        return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                    elif i==360:
                        return findLiberty(i-1,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                    elif place == 0:
                        return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                    elif place == 18:
                        return findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                    elif isUpper:
                        return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)
                    elif isLower:
                        return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-1,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
                    else:
                        return findLiberty(i+1,typ,taken,vis,action)+findLiberty(i-1,typ,taken,vis,action)+findLiberty(i+19,typ,taken,vis,action)+findLiberty(i-19,typ,taken,vis,action)
        def calcliberty(action, connected):  
            taken=[]
            vis=[]
            typ = turn
            place = (action) % 19
            isLower = (action >= 342)
            isUpper = (action <= 18)
            if element[action] == typ:
                if action == 0:
                    liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)
                elif action==18:
                    liberty = findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)
                elif action==342:
                    liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
                elif action==360:
                    liberty = findLiberty(action-1,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
                elif place == 0:
                    liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
                elif place == 18:
                    liberty = findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
                elif isUpper:
                    liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)
                elif isLower:
                    liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-1,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
                else:
                    liberty = findLiberty(action+1,typ,taken,vis,action)+findLiberty(action-1,typ,taken,vis,action)+findLiberty(action+19,typ,taken,vis,action)+findLiberty(action-19,typ,taken,vis,action)
                
                newarr[connected] = (liberty+1)
                newarr[action] =  (liberty+1)
            
            else:
                if action == 0:
                    liberty = findLiberty(action+1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action+19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                elif action==18:
                    liberty = findLiberty(action-1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action+19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]

                elif action==342:
                    liberty = findLiberty(action+1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]

                elif action==360:
                    liberty = findLiberty(action-1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                elif place == 0:
                    liberty = findLiberty(action+1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action+19,typ,taken,vis,action)
                    
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                elif place == 18:
                    liberty = findLiberty(action-1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action+19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                elif isUpper:
                    liberty = findLiberty(action+1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action+19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                elif isLower:
                    liberty = findLiberty(action+1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                else:
                    liberty = findLiberty(action+1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-1,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action+19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                    liberty = findLiberty(action-19,typ,taken,vis,action)
                    newarr[connected] = (liberty+1)
                    del connected[:]
                    del vis[:]
                    del taken[:]
                
            del connected[:]
            del vis[:]
            del taken[:]
            return newarr  
        out=calcliberty(action, connected)
        return out
    
    def _checkAllowance(self, action):
        currLib = self._generateLibMap(self.board[0:361],self.playerTurn, action)
        tempBoard =np.copy(self.board[0:361])
        tempBoard[action] = self.playerTurn 
        nextLib = self._generateLibMap(tempBoard,-self.playerTurn, action)
        tempBoard[nextLib == 1] = 0
        nextLib = self._generateLibMap(tempBoard,self.playerTurn, action)
        nextLib[nextLib == 1] =0
        if any(i > 0 for i in (nextLib - currLib)):
            if tempBoard in self.board_history:
                return False
            return True
        return False
            

            
    def _allowedActions(self):        
        for action in range(len(self.board)-2):
            for n in self._getNeighbours(action):
                if n not in self.allowedActions:
                    if self._checkAllowance(n):
                        self.allowedActions.append(n)         

        if self.playerTurn ==1:
            self.allowedActions.append(361)
        else:
            self.allowedActions.append(362)
        
    
                        

    def _binary(self):
        currentplayer_position = np.zeros(len(self.board)-2, dtype=np.int)
        other_position = np.zeros(len(self.board)-2, dtype=np.int)
        if(self.playerTurn == 1):
            currentplayer_position[self.board[0:361]>0] = 1
            other_position[self.board[0:361]<0] = 1
        else:
            currentplayer_position[self.board[0:361]<0] = 1
            other_position[self.board[0:361]>0] = 1
            
        position = np.append(currentplayer_position,other_position)
        return (position)

    def _convertStateToId(self):
        player1_position = np.zeros(len(self.board), dtype=np.int)
        player1_position[self.board>0] = 1
        other_position = np.zeros(len(self.board), dtype=np.int)
        other_position[self.board<0] = 1
        position = np.append(player1_position,other_position)
        id = ''.join(map(str,position))
        
        return id
    
    def _checkForEndGame(self):
        if(self.board[361]==1 and self.board[362]==-1):
            return 1
        return 0
    
    
    # def _getPrisoners(self,curr_player):
    #     prisoners_count = 0
    #     if curr_player:
    #         for i in range(len(self.board)-2):
    #             if self._checkZeroLiberty(i):
    #                 prisoners_count += prisoners_count
    #         return prisoners_count
    #     else:
    #         self.playerTurn = -self.playerTurn
    #         for i in range(len(self.board)-2):
    #             if self._checkZeroLiberty(i):
    #                 prisoners_count += prisoners_count
    #         self.playerTurn = -self.playerTurn
    #         return prisoners_count
           
    



    # def _getValue(self):
    #     print("_getValue")
    #     current_player_score = self.playerTurn*self.estimate(19,19,self.board[0:361],self.playerTurn,1000,0.2)
    #     other_player_score = -self.playerTurn*self.estimate(19,19,self.board[0:361],self.playerTurn,1000,0.2)

    #     # current_player_liberties = 0
    #     # other_player_liberties = 0
    #     # if self.playerTurn == 1:
    #     #     for i in range(len(self.board)-2):
    #     #         if self.board[i] > 0:
    #     #             current_player_liberties+=(self.board[i]-1)
    #     #         elif self.board[i] < 0:
    #     #             other_player_liberties+=((-self.board[i])-1)      
    #     # elif self.playerTurn == -1:
    #     #     for i in range(len(self.board)-2):
    #     #         if self.board[i] > 0:
    #     #             other_player_liberties+=(self.board[i]-1)
    #     #         elif self.board[i] < 0:
    #     #             current_player_liberties+=((-self.board[i])-1)           
    #     # current_player_prisoners = self._getPrisoners(1)
    #     # other_player_prisoners = self._getPrisoners(0)        
    #     # current_player_score = current_player_liberties + 4*other_player_prisoners - 4*current_player_prisoners
    #     # other_player_score = other_player_liberties + 4*current_player_prisoners - 4*other_player_prisoners
    #     return (current_player_score,current_player_score,other_player_score)
    
    
    def _getScore(self):
        tmp = self.value
        return (tmp[1], tmp[2])
    
    
    def takeAction(self, action):
        newBoard = np.array(self.board)
        newBoard[action]=self.playerTurn
        if action == 361:
            self.game_score[2] = self.perv_score[2] + 1
            self.game_score[1] = self.perv_score[1]
        elif action == 362:
            self.game_score[1] = self.perv_score[1] + 1
            self.game_score[2] = self.perv_score[2]
        else:
            newBoard[361] = 0
            newBoard[362] = 0
            LibMap = self._generateLibMap(newBoard[0:361], -self.playerTurn, action)
            deadPieces = (LibMap == 1)
            deadCount = sum(deadPieces)
            newBoard[0:361][deadPieces] = 0
            if self.playerTurn == 1:
                self.game_score[1] = self.perv_score[1] + deadCount
                self.game_score[2] = self.perv_score[2]
            else:
                self.game_score[1] = self.perv_score[1] 
                self.game_score[2] = self.perv_score[2] + deadCount

        if self.playerTurn == 1:
            self.game_score[0] = (self.game_score[1] - self.game_score[2]) 
        else:
            self.game_score[0] = self.game_score[2] - self.game_score[1]

        
            
        # elif action == 361:
        #     self.game_score -= 1
        # else:
        #     self.game_score +=1
            
        if len(self.board_history) > 3:
            del self.board_history[:]
        
        nextStateScore = [0,0,0]
        nextStateScore[0] = -self.game_score[0]
        nextStateScore[1] = self.game_score[1]
        nextStateScore[2] = self.game_score[2]

        self.board_history.append(newBoard)
        newState = GameState(newBoard, -self.playerTurn, self.board_history,  nextStateScore)
        value = self.game_score[0]
        done = 0
        
        if newState.isEndGame and newState.playerTurn == -1:
            value = 0
            done = 1

            
        return (newState, value, done) 
    
    
    
    def render(self):
        print()
        print(self.pieces[str(self.playerTurn)] + "'s turn:")
        for r in range(19):
            #logger.info([self.pieces[str(x)] for x in self.board[19*r : (19*r + 19)]])
            print([self.pieces[str(x)]  for x in self.board[19*r : (19*r + 19)]])
        # logger.info('--------------')
        print("Prisoners: ", self.perv_score)
        print("Black Pass: ", self.board[361])
        print("White Pass: ", self.board[362])
        print("Attention places", self.allowedActions)


    
    
    def renderThink(self,guiboard):
        guiboard.updateScoreMsg((self.perv_score[2],self.perv_score[1]))
        if self.board[361]==1:
            guiboard.updateMsg("Thinking...","Black Pass",(0,0,0))
        elif self.board[362]==-1:
            guiboard.updateMsg("Thinking...","White Pass",(220,220,220))
        else:
            guiboard.clearboard()
            b=np.array(self.board)
            guiboard.drawboard(b)
            if self.playerTurn==1:
                color="Black"
                guiboard.updateMsg("Thinking...",color + "'s turn",(0,0,0))
            else:
                color="White"
                guiboard.updateMsg("Thinking...",color + "'s turn",(220,220,220))
            


    def renderWait(self,guiboard):
        guiboard.updateScoreMsg((self.perv_score[2],self.perv_score[1]))
        if self.board[361]==1:
            guiboard.updateMsg("Waiting...","Black Pass",(0,0,0))
        elif self.board[362]==-1:
            guiboard.updateMsg("Waiting...","White Pass",(220,220,220))
        else:
            guiboard.clearboard()
            b=np.array(self.board)
            guiboard.drawboard(b)
            if self.playerTurn==1:
                color="Black"
                guiboard.updateMsg("Waiting...",color + "'s turn",(0,0,0))
                
            else:
                color="White"
                guiboard.updateMsg("Waiting...",color + "'s turn",(220,220,220))


    def renderThinkUser(self,guiboard, gamepos, bpass, wpass):
        print(bpass, wpass)
        (x,y) = gamepos.fullscore()
        y =y+bpass
        x=x+wpass
        guiboard.updateFullScoreMsg((y+self.perv_score[2],x+self.perv_score[1]),(self.perv_score[2],self.perv_score[1]))
        if self.board[361]==1:
            guiboard.updateMsg("Thinking...","Black Pass",(0,0,0))
        elif self.board[362]==-1:
            guiboard.updateMsg("Thinking...","White Pass",(220,220,220))
        else:
            guiboard.clearboard()
            b=np.array(self.board)
            guiboard.drawboard(b)
            if self.playerTurn==1:
                color="Black"
                guiboard.updateMsg("Thinking...",color + "'s turn",(0,0,0))
            else:
                color="White"
                guiboard.updateMsg("Thinking...",color + "'s turn",(220,220,220))
            


    def renderWaitUser(self,guiboard, gamepos, bpass, wpass):
        (x,y) = gamepos.fullscore()
        y =y+bpass
        x=x+wpass
        guiboard.updateFullScoreMsg((y+self.perv_score[2],x+self.perv_score[1]),(self.perv_score[2],self.perv_score[1]))
        if self.board[361]==1:
            guiboard.updateMsg("Waiting...","Black Pass",(0,0,0))
        elif self.board[362]==-1:
            guiboard.updateMsg("Waiting...","White Pass",(220,220,220))
        else:
            guiboard.clearboard()
            b=np.array(self.board)
            guiboard.drawboard(b)
            if self.playerTurn==1:
                color="Black"
                guiboard.updateMsg("Waiting...",color + "'s turn",(0,0,0))
                
            else:
                color="White"
                guiboard.updateMsg("Waiting...",color + "'s turn",(220,220,220))
            

                


        
                

