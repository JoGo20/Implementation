# %matplotlib inline
import os
import time
import signal 
import multiprocessing as mp
#os.environ['CUDA_VISIBLE_DEVICES'] = ''
from concurrent.futures import ProcessPoolExecutor, as_completed

#CPU_COUNT = mp.cpu_count() # how many cpus on the machine? 
#print("how many cpus: {}".format(CPU_COUNT))
CPU_COUNT = 8
#m = mp.Manager()
#q = m.() # define an output queue
import numpy as np
import random

import MCTS as mc
from game import GameState
from loss import softmax_cross_entropy_with_logits
import memory_profiler
import config
import loggers as lg
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import initialise
from IPython import display
import pylab as pl
from timeit import default_timer as timer
queue = mp.JoinableQueue() # define an output queue 


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
		self.pool = ProcessPoolExecutor(max_workers=CPU_COUNT) # create a pool of workers 
		self.state_size = state_size
		self.action_size = action_size
		self.cpuct = cpuct
		self.MCTSsimulations = mcts_simulations
		self.weights = self.pool.submit(self.get_weights_resnet).result()
		self.mcts = None
		self.train_overall_loss = []
		self.train_value_loss = []
		self.train_policy_loss = []
		self.val_overall_loss = []
		self.val_value_loss = []
		self.val_policy_loss = []
	
	def __getstate__(self):
		state = self.__dict__.copy()
		del state['pool']
		return state
		
	def __setstate__(self, state):
		self.__dict__.update(state)

	def get_weights_resnet(self):
		print("Building and compiling the model in the 'mother' process")
		from model import Residual_CNN
		resmodel = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + (19, 19),   363, config.HIDDEN_CNN_LAYERS)
		if initialise.INITIAL_MODEL_VERSION != None:
			m_tmp = resmodel.read(initialise.INITIAL_RUN_NUMBER, initialise.INITIAL_MODEL_VERSION)
			resmodel.model.set_weights(m_tmp.get_weights())
		#print("Model summary:")
		#resmodel.model.summary()
		return resmodel.model.get_weights() # returns a list of all weight tensors in the model, as Numpy arrays



	
	def simulate(self, state, p):

		root = mc.Node(state)
		mcts = mc.MCTS(root, self.cpuct)
		if self.mcts == None or state.id not in self.mcts.tree:
			pass
		else:
			mcts.tree.update(self.mcts.tree)
			mcts.root = mcts.tree[state.id]
	
		import model
		from model import Residual_CNN
		resmodel = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + (19, 19),   363, config.HIDDEN_CNN_LAYERS)
		resmodel.model.set_weights(self.weights)
		##### MOVE THE LEAF NODE
		sim_n = int(self.MCTSsimulations/CPU_COUNT)
		
		for sim in range(sim_n):
			leaf, value, done, breadcrumbs = mcts.moveToLeaf(p)
			#print("Process: ",p," ==> ")
			#leaf.state.render(lg.logger_mcts)

			##### EVALUATE THE LEAF NODE
			
			value, breadcrumbs = self.evaluateLeaf(leaf, value, done, breadcrumbs, mcts, resmodel, p)


			##### BACKFILL THE VALUE THROUGH THE TREE
			mcts.backFill(leaf, value, breadcrumbs)
			#print("Process: ", p,". Current tree length: ",len(self.mcts.tree))
			#queue.task_done()
			#queue.join()
			
		return mcts
		

		

	
	def write(self, game, version):
		from model import Residual_CNN
		resmodel = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + (19, 19),   363, config.HIDDEN_CNN_LAYERS)
		resmodel.model.set_weights(self.weights)
		resmodel.write(game, version)

	def act(self, state, tau):
		if self.mcts == None or state.id not in self.mcts.tree:
			self.buildMCTS(state)
		else:
			self.changeRootMCTS(state)

		#### run the simulation
		start = timer()
		futures = [self.pool.submit(self.simulate, state, p) for p in range(CPU_COUNT)]
		for future in as_completed(futures):
			umcts = future.result()
			end = timer()
			print("Evaluation time = ", (end-start))
			self.mcts.tree.update(umcts.tree)
			self.mcts.root = umcts.root
			umcts.tree.clear()
		#### get action values
		pi, values = self.getAV(1)

		####pick the action
		action, value = self.chooseAction(pi, values, tau)

		nextState, _, _ = state.takeAction(action)
		NN_value = 0#-self.get_preds(nextState)[0]

		# lg.logger_mcts.info('ACTION VALUES...%s', pi)
		# lg.logger_mcts.info('CHOSEN ACTION...%d', action)
		# lg.logger_mcts.info('MCTS PERCEIVED VALUE...%f', value)
		# lg.logger_mcts.info('NN PERCEIVED VALUE...%f', NN_value)
		print("Action selected: ", action)
		return (action, pi, value, NN_value)


	def get_preds(self, state, resmodel):
		#predict the leaf
		#start = timer()
		#import model
		#from model import Residual_CNN
		#resmodel = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + (19, 19),   363, config.HIDDEN_CNN_LAYERS)
		#end = timer()
		#print("Model building time = ", (end-start))
		resmodel.model.set_weights(self.weights)
		inputToModel = np.array([resmodel.convertToModelInput(state)])
		
		preds = resmodel.model.predict(inputToModel)
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


	def evaluateLeaf(self, leaf, value, done, breadcrumbs, mcts, resmodel, p):

		# lg.logger_mcts.info('------EVALUATING LEAF------')

		if done == 0:
		
			value, probs, allowedActions = self.get_preds(leaf.state, resmodel)
			# lg.logger_mcts.info('PREDICTED VALUE FOR %d: %f', leaf.state.playerTurn, value)
			probs = probs[allowedActions]
			actions_start = int(p*len(allowedActions)/CPU_COUNT)
			actions_end = int((1+p)*len(allowedActions)/CPU_COUNT)+1
			for idx, action in enumerate(allowedActions):
				newState, _, _ = leaf.state.takeAction(action)
				if newState.id not in mcts.tree:
					node = mc.Node(newState)
					mcts.addNode(node)
					# lg.logger_mcts.info('added node...%s...p = %f', node.id, probs[idx])
				else:
					node = mcts.tree[newState.id]
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
		from model import Residual_CNN
		resmodel = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + (19, 19),   363, config.HIDDEN_CNN_LAYERS)
		resmodel.model.set_weights(self.weights)

		for i in range(config.TRAINING_LOOPS):
			minibatch = random.sample(ltmemory, min(config.BATCH_SIZE, len(ltmemory)))

			training_states = np.array([resmodel.convertToModelInput(row['state']) for row in minibatch])
			training_targets = {'value_head': np.array([row['value'] for row in minibatch])
								, 'policy_head': np.array([row['AV'] for row in minibatch])} 

			fit = resmodel.model.fit(training_states, training_targets, epochs=config.EPOCHS, verbose=1, validation_split=0, batch_size = 32)
			# lg.logger_mcts.info('NEW LOSS %s', fit.history)

			self.train_overall_loss.append(round(fit.history['loss'][config.EPOCHS - 1],4))
			self.train_value_loss.append(round(fit.history['value_head_loss'][config.EPOCHS - 1],4)) 
			self.train_policy_loss.append(round(fit.history['policy_head_loss'][config.EPOCHS - 1],4)) 

		plt.plot(self.train_overall_loss, 'k')
		plt.plot(self.train_value_loss, 'k:')
		plt.plot(self.train_policy_loss, 'k--')
		plt.show()
		plt.legend(['train_overall_loss', 'train_value_loss', 'train_policy_loss'], loc='lower left')
		
		display.clear_output(wait=True)
		display.display(pl.gcf())
		pl.gcf().clear()
		time.sleep(1.0)

		print('\n')
		resmodel.printWeightAverages()

	# def predict(self, inputToModel):
	# 	preds = self.model.predict(inputToModel)
	# 	return preds

	def buildMCTS(self, state):
		# lg.logger_mcts.info('****** BUILDING NEW MCTS TREE FOR AGENT %s ******', self.name)
		self.root = mc.Node(state)
		self.mcts = mc.MCTS(self.root, self.cpuct)

	def changeRootMCTS(self, state):
		# lg.logger_mcts.info('****** CHANGING ROOT OF MCTS TREE TO %s FOR AGENT %s ******', state.id, self.name)
		self.mcts.root = self.mcts.tree[state.id]