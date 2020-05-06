# %matplotlib inline

import numpy as np
import random
import MCTS as mc
from game import GameState
import config
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython import display
import pylab as pl
import numpy as np
import os
import random
import re
import sys
import go
from policy import PolicyNetwork
from strategies import MCTSPlayerMixin
read_file = config.TRAINED_MODEL_PATH
WHITE, EMPTY, BLACK, FILL, KO, UNKNOWN = range(-1, 5)


class User():
	def __init__(self, name, state_size, action_size):
		self.name = name
		self.state_size = state_size
		self.action_size = action_size

	def act(self, state, tau):
		action = int(input('Enter your chosen action: '))
		pi = np.zeros(self.action_size)
		pi[action] = 1
		value = None
		NN_value = None
		return (action, pi, value, NN_value)



class Agent():
	def __init__(self, name, state_size, action_size, mcts_simulations, cpuct):
		self.name = name
		self.state_size = state_size
		self.action_size = action_size
		self.cpuct = cpuct
		self.MCTSsimulations = mcts_simulations
		self.filepath = config.TRAINED_MODEL_PATH
		self.model = PolicyNetwork(use_cpu=config.USE_CPU)
		self.model.initialize_variables(read_file)
		self.mcts = MCTSPlayerMixin(self.model)
		self.pcount=0
		self.train_overall_loss = []
		self.train_value_loss = []
		self.train_policy_loss = []
		self.val_overall_loss = []
		self.val_value_loss = []
		self.val_policy_loss = []


	def act(self, state, bstate, turn):
		rstate = state
		self.mcts.seconds_per_move = config.SECS_PER_TURN
		baction = self.mcts.suggest_move(state)
		if baction is None:
			if bstate.playerTurn == 1:
				action = 361
			else:
				action = 362
		else:
			action = baction[0]*19+baction[1]
		print(baction)
		
		return baction, action, rstate


	def replay(self, ltmemory):
		for i in range(config.TRAINING_LOOPS):
			minibatch = random.sample(ltmemory, min(config.BATCH_SIZE, len(ltmemory)))
			training_states = np.array([self.model.convertToModelInput(row['state']) for row in minibatch])
			training_targets = {'value_head': np.array([row['value'] for row in minibatch])
								, 'policy_head': np.array([row['AV'] for row in minibatch])} 
			fit = self.model.fit(training_states, training_targets, epochs=config.EPOCHS, verbose=1, validation_split=0, batch_size = 32)
			self.train_overall_loss.append(round(fit.history['loss'][config.EPOCHS - 1],4))
			self.train_value_loss.append(round(fit.history['value_head_loss'][config.EPOCHS - 1],4)) 
			self.train_policy_loss.append(round(fit.history['policy_head_loss'][config.EPOCHS - 1],4)) 
		plt.plot(self.train_overall_loss, 'k')
		plt.plot(self.train_value_loss, 'k:')
		plt.plot(self.train_policy_loss, 'k--')
		plt.legend(['train_overall_loss', 'train_value_loss', 'train_policy_loss'], loc='lower left')
		display.clear_output(wait=True)
		display.display(pl.gcf())
		pl.gcf().clear()
		time.sleep(1.0)
		print('\n')
		self.model.printWeightAverages()

	def predict(self, inputToModel):
		preds = self.model.predict(inputToModel)
		return preds
