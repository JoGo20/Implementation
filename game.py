'''
Developer: Ahmed Mokhtar
MI: Impelemntation Team
JoGo
14 March 2020
'''
import numpy as np


class Game:
    def __init__(self):
        # BLACK GOES FIRST
        self.currentPlayer = 1
        # 19*19 PLACES EQUALS 361 BOARD STATE SPACE.
        # 2 STATE SPACES FOR BOTH PLAYER TO PASS THEIR TURN.
        # 363 STATE SPACE. 0 TO 362
        self.gameState=GameState(np.array(np.zeros(363),dtype=np.int),1)
        #  19*19 PLACES EQUALS 361 BOARD ACTION SPACE.
        #  1 ACTION SPACE FOR ANY AGENT TO PASS THEIR TURN TI THE OPPONENT.
        #  362 ACTION SPACE. 0 TO 361
        self.actionSpace = np.array(np.zeros(363), dtype = np.int)
        # Positive Numbers reperesent the black number of liberties where 1 has no liberties and 5 has 4 liberties.
        # Negative numbers reperesent the white number of liberties where -1 has no liberties and -5 has 4 liberties.
        # 0 means an empty interesection in the GO board.
        self.pieces = {'1':'B', '2':'B', '3':'B', '4':'B', '5':'B', '0':'-', '-1':'W', '-1':'W', '-2':'W', '-3':'W', '-4':'W', '-5':'W'}
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
