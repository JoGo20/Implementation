# %matplotlib inline
import numpy as np
import random
import threading
import multiprocessing
import MCTS as mc
from game import GameState
from loss import softmax_cross_entropy_with_logits

import config
import loggers as lg
import time

import matplotlib.pyplot as plt
from IPython import display
import pylab as pl
from model import Residual_CNN


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
	def __init__(self, name, state_size, action_size, mcts_simulations, cpuct, model, env):
		self.name = name
		self.processes_n = 5
		self.state_size = state_size
		self.action_size = action_size

		self.cpuct = cpuct
		self.MCTSsimulations = mcts_simulations
		self.models = [model, None, None, None, None, None]
		self.processes_trees = [None, None, None, None, None, None]
		self.mcts = self.processes_trees[0]
		self.train_overall_loss = []
		self.train_value_loss = []
		self.train_policy_loss = []
		self.val_overall_loss = []
		self.val_value_loss = []
		self.val_policy_loss = []
		self.env = env

	
	def simulate(self, process_id, state):
		sim_n = int(self.MCTSsimulations/self.processes_n)
		self.models[process_id] = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + self.env.grid_shape,   self.env.action_size, config.HIDDEN_CNN_LAYERS)
		if self.processes_trees[process_id] == None or state.id not in self.processes_trees[process_id].tree:
			self.buildMCTS(state, process_id)
		else:
			self.changeRootMCTS(state, process_id) 
		for _ in range(sim_n):
			##### MOVE THE LEAF NODE
			
			leaf, value, done, breadcrumbs = self.processes_trees[process_id].moveToLeaf()
			#leaf.state.render(lg.logger_mcts)
			
			##### EVALUATE THE LEAF NODE
			value, breadcrumbs = self.evaluateLeaf(leaf, value, done, breadcrumbs, process_id)
			

			##### BACKFILL THE VALUE THROUGH THE TREE
			self.processes_trees[process_id].backFill(leaf, value, breadcrumbs)


	def act(self, state, tau):
		
		if self.processes_trees[0] == None or state.id not in self.processes_trees[0].tree:
			self.buildMCTS(state, 0)
		else:
			self.changeRootMCTS(state, 0)
	
		#### run the simulation
		processes = []
		for sim in range(self.processes_n):
			# lg.logger_mcts.info('***************************')
			# lg.logger_mcts.info('****** SIMULATION %d ******', sim + 1)
			# lg.logger_mcts.info('***************************')
			
			processes.append(multiprocessing.Process(target=self.simulate, args=(sim+1, state, )))
			processes[sim].start()

		for sim in range(self.processes_n):
			print("here", sim)
			processes[sim+1].join()

		self.mcts = self.processes_trees[1]
		
		for sim in range(self.processes_n):
			self.mcts.tree.update(self.processes_trees[sim+1].tree)
			self.processes_trees[sim+1].tree.clear()

		#### get action values
		pi, values = self.getAV(1)

		####pick the action
		action, value = self.chooseAction(pi, values, tau)

		nextState, _, _ = state.takeAction(action)
		NN_value = -self.get_preds(nextState, 0)[0]

		# lg.logger_mcts.info('ACTION VALUES...%s', pi)
		# lg.logger_mcts.info('CHOSEN ACTION...%d', action)
		# lg.logger_mcts.info('MCTS PERCEIVED VALUE...%f', value)
		# lg.logger_mcts.info('NN PERCEIVED VALUE...%f', NN_value)

		return (action, pi, value, NN_value)


	def get_preds(self, state, process_id):
		#predict the leaf
		inputToModel = np.array([self.models[process_id].convertToModelInput(state)])
		preds = self.models[process_id].predict(inputToModel)
		
		value_array = preds[0]
		logits_array = preds[1]
		value = value_array[0]

		logits = logits_array[0]

		allowedActions = state.allowedActions
		

		mask = np.ones(logits.shape,dtype=bool)
		mask[allowedActions] = False
		logits[mask] = -100

		#SOFTMAX
		odds = np.exp(logits)
		probs = odds / np.sum(odds) ###put this just before the for?

		return ((value, probs, allowedActions))


	def evaluateLeaf(self, leaf, value, done, breadcrumbs, process_id):

		# lg.logger_mcts.info('------EVALUATING LEAF------')

		if done == 0:
	
			value, probs, allowedActions = self.get_preds(leaf.state, process_id)
			# lg.logger_mcts.info('PREDICTED VALUE FOR %d: %f', leaf.state.playerTurn, value)
			
			probs = probs[allowedActions]

			for idx, action in enumerate(allowedActions):
				newState, _, _ = leaf.state.takeAction(action)
				if newState.id not in self.processes_trees[process_id].tree:
					node = mc.Node(newState)
					self.processes_trees[process_id].addNode(node)
					# lg.logger_mcts.info('added node...%s...p = %f', node.id, probs[idx])
				else:
					node = self.processes_trees[process_id].tree[newState.id]
					# lg.logger_mcts.info('existing node...%s...', node.id)

				newEdge = mc.Edge(leaf, node, probs[idx], action)
				leaf.edges.append((action, newEdge))
				
		else:
			pass
			# lg.logger_mcts.info('GAME VALUE FOR %d: %f', leaf.playerTurn, value)

		
		return ((value, breadcrumbs))


		
	def getAV(self, tau):
		edges = self.mcts.root.edges
		pi = np.zeros(self.action_size, dtype=np.integer)
		values = np.zeros(self.action_size, dtype=np.float32)
		
		for action, edge in edges:
			pi[action] = pow(edge.stats['N'], 1/tau)
			values[action] = edge.stats['Q']

		pi = pi / (np.sum(pi) * 1.0)
		return pi, values

	def chooseAction(self, pi, values, tau):
		if tau == 0:
			actions = np.argwhere(pi == max(pi))
			action = random.choice(actions)[0]
		else:
			action_idx = np.random.multinomial(1, pi)
			action = np.where(action_idx==1)[0][0]

		value = values[action]

		return action, value

	def replay(self, ltmemory):
		# lg.logger_mcts.info('******RETRAINING MODEL******')


		for i in range(config.TRAINING_LOOPS):
			minibatch = random.sample(ltmemory, min(config.BATCH_SIZE, len(ltmemory)))

			training_states = np.array([self.models[0].convertToModelInput(row['state']) for row in minibatch])
			training_targets = {'value_head': np.array([row['value'] for row in minibatch])
								, 'policy_head': np.array([row['AV'] for row in minibatch])} 

			fit = self.models[0].fit(training_states, training_targets, epochs=config.EPOCHS, verbose=1, validation_split=0, batch_size = 32)
			# lg.logger_mcts.info('NEW LOSS %s', fit.history)

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
		self.models[0].printWeightAverages()

	def predict(self, inputToModel, process_id):
		preds = self.models[process_id].predict(inputToModel)
		return preds

	def buildMCTS(self, state, process_id):
		# lg.logger_mcts.info('****** BUILDING NEW MCTS TREE FOR AGENT %s ******', self.name)
		root = mc.Node(state)
		self.processes_trees[process_id] = mc.MCTS(root, self.cpuct)

	def changeRootMCTS(self, state, process_id):
		# lg.logger_mcts.info('****** CHANGING ROOT OF MCTS TREE TO %s FOR AGENT %s ******', state.id, self.name)
		self.processes_trees[process_id].root = self.processes_trees[process_id].tree[state.id]