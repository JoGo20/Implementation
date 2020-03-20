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
   

class Game:
    def __init__(self):
        # BLACK GOES FIRST
        self.currentPlayer = 1
        # 19*19 PLACES EQUALS 361 BOARD STATE SPACE.
        # 2 STATE SPACES FOR BOTH PLAYER TO PASS THEIR TURN.
        # 363 STATE SPACE. 0 TO 362
        self.gameState=GameState(np.array(np.zeros(363),dtype=np.int),1)
        self.actionSpace = np.array(np.zeros(363), dtype = np.int)
        # Positive Numbers reperesent the black number of liberties where 1 has no liberties and 5 has 4 liberties.
        # Negative numbers reperesent the white number of liberties where -1 has no liberties and -5 has 4 liberties.
        # 0 means an empty interesection in the GO board.
        self.pieces = {'1':'B', '2':'B', '3':'B', '4':'B', '5':'B', '0':'-', '-1':'W', '-2':'W', '-3':'W', '-4':'W', '-5':'W'}
        self.grid_shape = (19, 19)
        # # 19*19 Board State binary bits times 2 for each to be used by agents to their neural network.
        self.input_shape = (2, 19, 19)
        self.name = 'go'
        self.state_size = len(self.gameState.binary)
        self.action_size = len(self.actionSpace)

    def reset(self):
        self.gameState = GameState(np.array(np.zeros(363), dtype = np.int), 1)
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
                
        av.append(currentAV[361])
        currentAV = np.array(av)
        
        identities.append((GameState(currentBoard, state.playerTurn), currentAV))
        
        return identities
    
    
class GameState():
    def __init__(self, board, playerTurn):
        self.board = board
        self.pieces = {'1':'B', '2':'B', '3':'B', '4':'B', '5':'B', '0':'-', '-1':'W', '-2':'W', '-3':'W', '-4':'W', '-5':'W'}
        self.playerTurn = playerTurn
        self.binary = self._binary()
        self.id = self._convertStateToId()
        self.allowedActions = self._allowedActions()
        self.isEndGame = self._checkForEndGame()
        if(self.isEndGame):
            self.arr = ((19 * 19) * ctypes.c_int)()
            data = np.copy(self.board[0:361])
            for i, v in enumerate(data):
                self.arr[i] = v
                score = _estimator_so.estimate(19, 19, self.arr, self.playerTurn, 1000,ctypes.c_float(0.4))
                data[:] = self.arr
                current_player_score = self.playerTurn*score
                other_player_score = -self.playerTurn*score
                self.value = (current_player_score,current_player_score,other_player_score)
        else:
            self.value = (0,0,0)
        self.score = self._getScore()
        #self.estimate.__annotations__ = { 'width': int, 'height': int, 'data': List[int], 'player_to_move': int, 'trials': int, 'tolerance': float, 'return': int,} 
        
    def _checkZeroLiberty(self, action):
        place = (action + 1) % 19
        isUpper = (action >= 341)
        isLower = (action <= 18)
        
        #Upper Left Corner with 2 Liberties
        if isUpper and place ==1:
            if self.playerTurn == 1:
                if self.board[action+1] < 0 and self.board[action-19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action+1] > 0 and self.board[action-19] > 0:
                    return False
                
        #Upper Right Corner with 2 Liberties
        elif isUpper and place ==0:
            if self.playerTurn == 1:
                if self.board[action-1] < 0 and self.board[action-19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action-1] > 0 and self.board[action-19] > 0:
                    return False

        #Lower Left Corner with 2 Liberties
        elif isUpper and place ==0:
            if self.playerTurn == 1:
                if self.board[action+1] < 0 and self.board[action+19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action+1] > 0 and self.board[action+19] > 0:
                    return False
                
        #Lower Right Corner with 2 Liberties
        elif isUpper and place ==0:
            if self.playerTurn == 1:
                if self.board[action-1] < 0 and self.board[action+19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action-1] > 0 and self.board[action+19] > 0:
                    return False
        
        #Upper Edge with 3 Liberties
        elif isUpper:
            if self.playerTurn == 1:
                if self.board[action-1] < 0 and self.board[action-19] < 0 and self.board[action+1] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action-1] > 0 and self.board[action-19] > 0 and self.board[action+1] > 0:
                    return False
                
        #Lower Edge with 3 Liberties
        elif isLower:
            if self.playerTurn == 1:
                if self.board[action+1] < 0 and self.board[action-1] < 0 and self.board[action+19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action+1] > 0 and self.board[action-1] > 0 and self.board[action+19] > 0:
                    return False
        
        #Right Edge with 3 Liberties
        elif place == 0:
            if self.playerTurn == 1:
                if self.board[action-1] < 0 and self.board[action-19] < 0 and self.board[action+19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action-1] > 0 and self.board[action-19] > 0 and self.board[action+19] > 0:
                    return False
                
        #Left Edge with 3 Liberties
        elif place == 1:
            if self.playerTurn == 1:
                if self.board[action+1] < 0 and self.board[action-19] < 0 and self.board[action+19] < 0:
                    return False
            elif self.playerTurn == -1:
                if self.board[action+1] > 0 and self.board[action-19] > 0 and self.board[action+19] > 0:
                    return False
                
        
        #Otherwise on the board with 4 Liberties
        elif self.playerTurn == 1:
            if self.board[action+1] < 0 and self.board[action-1] < 0 and self.board[action-19] < 0 and self.board[action+19] < 0:
                return False
        elif self.playerTurn == -1:
            if self.board[action+1] > 0 and self.board[action-1] < 0 and self.board[action-19] > 0 and self.board[action+19] > 0:
                return False
        
        return True
    
    
    # def _reduceNeighboring(self, action, newBoard):
    #     #print("Current action: ",action)
    #     place = (action + 1) % 19
    #     isUpper = (action >= 341)
    #     isLower = (action <= 18)
    #     #Upper Left Corner with 2 Liberties
    #     if isUpper and place ==1:
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))
    #         if newBoard[action-19] !=0:
    #             newBoard[action-19] -= (int(newBoard[action-19] > 0) - int(newBoard[action-19] < 0))
    #     #Upper Right Corner with 2 Liberties
    #     elif isUpper and place ==0:
    #         if newBoard[action-1] != 0:
    #             newBoard[action-1] -= (int(newBoard[action-1] > 0) - int(newBoard[action-1] < 0))
    #         if newBoard[action-19] !=0:
    #             newBoard[action-19] -= (int(newBoard[action-19] > 0) - int(newBoard[action-19] < 0))
    #     #Lower Left Corner with 2 Liberties
    #     elif isUpper and place ==0:
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))
    #         if newBoard[action+19] !=0:
    #             newBoard[action+19] -= (int(newBoard[action+19] > 0) - int(newBoard[action+19] < 0))      
    #     #Lower Right Corner with 2 Liberties
    #     elif isUpper and place ==0:
    #         if newBoard[action-1] != 0:
    #             newBoard[action-1] -= (int(newBoard[action-1] > 0) - int(newBoard[action-1] < 0))
    #         if newBoard[action+19] !=0:
    #             newBoard[action+19] -= (int(newBoard[action+19] > 0) - int(newBoard[action+19] < 0))
    #     #Upper Edge with 3 Liberties
    #     elif isUpper:
    #         if newBoard[action-1] != 0:
    #             newBoard[action-1] -= (int(newBoard[action-1] > 0) - int(newBoard[action-1] < 0))
    #         if newBoard[action-19] !=0:
    #             newBoard[action-19] -= (int(newBoard[action-19] > 0) - int(newBoard[action-19] < 0))
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))      
    #     #Lower Edge with 3 Liberties
    #     elif isLower:
    #         if newBoard[action-1] != 0:
    #             newBoard[action-1] -= (int(newBoard[action-1] > 0) - int(newBoard[action-1] < 0))
    #         if  newBoard[action+19] !=0:
    #             newBoard[action+19] -= (int(newBoard[action+19] > 0) - int(newBoard[action+19] < 0))
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))
    #     #Right Edge with 3 Liberties
    #     elif place == 0:
    #         if newBoard[action-1] != 0:
    #             newBoard[action-1] -= (int(newBoard[action-1] > 0) - int(newBoard[action-1] < 0))
    #         if  newBoard[action+19] !=0:
    #             newBoard[action+19] -= (int(newBoard[action+19] > 0) - int(newBoard[action+19] < 0))
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))
                
    #     #Left Edge with 3 Liberties
    #     elif place == 1:
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))
    #         if  newBoard[action-19] !=0:
    #             newBoard[action-19] -= (int(newBoard[action-19] > 0) - int(newBoard[action-19] < 0))
    #         if newBoard[action+19] != 0:
    #             newBoard[action+19] -= (int(newBoard[action+19] > 0) - int(newBoard[action+19] < 0))
                        
    #     #Otherwise on the board with 4 Liberties
    #     else:
    #         if newBoard[action+1] != 0:
    #             newBoard[action+1] -= (int(newBoard[action+1] > 0) - int(newBoard[action+1] < 0))
    #         if newBoard[action-19] !=0:
    #             newBoard[action-19] -= (int(newBoard[action-19] > 0) - int(newBoard[action-19] < 0))
    #         if newBoard[action-1] != 0:
    #             newBoard[action-1] -= (int(newBoard[action-1] > 0) - int(newBoard[action-1] < 0))
    #         if newBoard[action+19] !=0:
    #             newBoard[action+19] -= (int(newBoard[action+19] > 0) - int(newBoard[action+19] < 0))
                
    
    # def _findActionLiberty(self, action):
    #     place = (action + 1) % 19
    #     isUpper = (action >= 341)
    #     isLower = (action <= 18)
    #     liberties = 0
    #     #Upper Left Corner with 2 Liberties
    #     if isUpper and place ==1:
    #         if self.board[action+1] == 0:
    #             liberties += 1
    #         if  self.board[action-19] ==0:
    #             liberties += 1
    #     #Upper Right Corner with 2 Liberties
    #     elif isUpper and place ==0:
    #         if self.board[action-1] == 0:
    #             liberties += 1
    #         if  self.board[action-19] ==0:
    #             liberties += 1
    #     #Lower Left Corner with 2 Liberties
    #     elif isUpper and place ==0:
    #         if self.board[action+1] == 0:
    #             liberties += 1
    #         if  self.board[action+19] ==0:
    #             liberties += 1         
    #     #Lower Right Corner with 2 Liberties
    #     elif isUpper and place ==0:
    #         if self.board[action-1] == 0:
    #             liberties += 1
    #         if  self.board[action+19] ==0:
    #             liberties += 1
    #     #Upper Edge with 3 Liberties
    #     elif isUpper:
    #         if self.board[action-1] == 0:
    #             liberties += 1
    #         if  self.board[action-19] ==0:
    #             liberties += 1
    #         if self.board[action+1] == 0:
    #             liberties += 1
                
    #     #Lower Edge with 3 Liberties
    #     elif isLower:
            
    #         if self.board[action-1] == 0:
    #             liberties += 1
    #         if  self.board[action+19] ==0:
    #             liberties += 1
    #         if self.board[action+1] == 0:
    #             liberties += 1
        
    #     #Right Edge with 3 Liberties
    #     elif place == 0:
    #         if self.board[action-1] == 0:
    #             liberties += 1
    #         if  self.board[action+19] ==0:
    #             liberties += 1
    #         if self.board[action+1] == 0:
    #             liberties += 1
                
    #     #Left Edge with 3 Liberties
    #     elif place == 1:
    #         if self.board[action+1] == 0:
    #             liberties += 1
    #         if  self.board[action-19] ==0:
    #             liberties += 1
    #         if self.board[action+19] == 0:
    #             liberties += 1
                        
    #     #Otherwise on the board with 4 Liberties
    #     else:
    #         if self.board[action+1] == 0:
    #             liberties += 1
    #         if  self.board[action-19] ==0:
    #             liberties += 1
    #         if self.board[action-1] == 0:
    #             liberties += 1
    #         if  self.board[action+19] ==0:
    #             liberties += 1
        
    #     return liberties

    def _allowedActions(self):
        allowed = []
        for i in range(len(self.board)-2): #-2
            if self.board[i]==0 and self._checkZeroLiberty(i):
                allowed.append(i)

        if(len(allowed)==0):
            if self.playerTurn == 1:
                allowed.append(361)
            else:
                allowed.append(362)
    
                             
        #Modify to only allow passes when there is no neutral places
        #Append 361 only
        #Satisfied
        #if(self.board[361]):
        #    print("Black passed:" ,allowPass)
        #if(self.board[362]):
        #    print("White passed: ", allowPass)
                
        return allowed

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
        if(self.board[361]==1 or self.board[362]==-1):
            print("Game Finished")
            return 1
        return 0
    
    
    def _getPrisoners(self,curr_player):
        prisoners_count = 0
        if curr_player:
            for i in range(len(self.board)-2):
                if self._checkZeroLiberty(i):
                    prisoners_count += prisoners_count
            return prisoners_count
        else:
            self.playerTurn = -self.playerTurn
            for i in range(len(self.board)-2):
                if self._checkZeroLiberty(i):
                    prisoners_count += prisoners_count
            self.playerTurn = -self.playerTurn
            return prisoners_count
           
    



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
        
        newState = GameState(newBoard, -self.playerTurn)
        value = 0
        done = 0
        
        if newState.isEndGame:
            value = newState.value[0]
            done = 1
            
        return (newState, value, done) 
    
    
    
    def render(self, logger):
        print()
        print(self.pieces[str(self.playerTurn)] + "'s turn:")
        for r in range(19):
            #logger.info([self.pieces[str(x)] for x in self.board[19*r : (19*r + 19)]])
            print([self.pieces[str(x)]  for x in self.board[19*r : (19*r + 19)]])
        logger.info('--------------')
        print(self.value)
        print("Black Pass: ", self.board[361])
        print("White Pass: ", self.board[362])
        print(self.allowedActions)
        
                

