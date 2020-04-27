
import numpy as np
np.set_printoptions(suppress=True)

from shutil import copyfile
import random
from importlib import reload


from keras.utils import plot_model

from game import Game, GameState
from agent import Agent
from memory import Memory
from funcs import playMatches, playMatchesBetweenVersions

import loggers as lg

from settings import run_folder, run_archive_folder
import initialise
import pickle



env = Game()

# If loading an existing neural network, copy the config file to root
if initialise.INITIAL_RUN_NUMBER != None:
    copyfile(run_archive_folder  + env.name + '/run' + str(initialise.INITIAL_RUN_NUMBER).zfill(4) + '/config.py', './config.py')

import config

######## LOAD MEMORIES IF NECESSARY ########

if initialise.INITIAL_MEMORY_VERSION == None:
    memory = Memory(config.MEMORY_SIZE)
else:
    print('LOADING MEMORY VERSION ' + str(initialise.INITIAL_MEMORY_VERSION) + '...')
    memory = pickle.load( open( run_archive_folder + env.name + '/run' + str(initialise.INITIAL_RUN_NUMBER).zfill(4) + "/memory/memory" + str(initialise.INITIAL_MEMORY_VERSION).zfill(4) + ".p",   "rb" ) )


CPU_COUNT = mp.cpu_count() # how many cpus on the machine? 
print("how many cpus: {}".format(CPU_COUNT))
queue = mp.Queue() # define an output queue 



def get_weights_resnet():
    print("Building and compiling the model in the 'mother' process")
	#from keras import layers
	#from keras import models
	#import keras.backend as K  
	#import tensorflow as tf
	#create an untrained neural network objects from the config file
    from modelimport Residual_CNN
    resmodel = Residual_CNN(config.REG_CONST, config.LEARNING_RATE, (2,) + env.grid_shape,   env.action_size, config.HIDDEN_CNN_LAYERS)
    print("Model summary:")
    resmodel.model.summary()
    return resmodel.model.get_weights() # returns a list of all weight tensors in the model, as Numpy arrays



def pool_job_resnet(weights, quit, foundit):
	"""
	This should be the child process, 
	where you load/run within another process.
	It will contain whatever code should be run on 
	multiple processors.
	"""
	print("This is me, your child feeding from you Mum")

	#from keras import layers
	#from keras import models
	#import keras.backend as K
	#import tensorflow as tf
	K.set_session(tf.Session())
	from keras.datasets import mnist 
	from keras.utils import to_categorical

	(train_images, train_labels), (test_images, test_labels) = mnist.load_data()
	train_images = train_images.reshape((60000, 28, 28, 1))
	train_images = train_images.astype('float32') / 255

	test_images = test_images.reshape((10000, 28, 28, 1))
	test_images = test_images.astype('float32') / 255

	train_labels = to_categorical(train_labels)
	test_labels = to_categorical(test_labels)
	
	model = models.Sequential()
	model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)))
	model.add(layers.MaxPooling2D((2, 2)))
	model.add(layers.Conv2D(64, (3, 3), activation='relu'))
	model.add(layers.MaxPooling2D((2, 2)))
	model.add(layers.Conv2D(64, (3, 3), activation='relu'))
	model.add(layers.Flatten())
	model.add(layers.Dense(64, activation='relu'))
	model.add(layers.Dense(10, activation='softmax'))

	model.compile(optimizer='rmsprop', loss='categorical_crossentropy',
		metrics=['accuracy'])
	
	model.set_weights(weights) 
	# sets the values of the weights of the model, from a list of Numpy arrays. 
	# The arrays in the list should have the same shape as those returned by get_weights().
	
	while True:
		model.fit(train_images, train_labels, epochs=5, batch_size=64, verbose=1)
		test_loss, test_acc = model.evaluate(test_images, test_labels)
		print("test accuracy {}".format(test_acc))
		queue.put(os.getpid())
		queue.join()
		#print("process id:", queue.get(os.getpid()))


if __name__ == "__main__":
	pool = ProcessPoolExecutor(max_workers=CPU_COUNT) # create a pool of workers 
	weights = pool.submit(get_weights_resnet).result() # a pool of processes 
		# [pool.submit(pool_job_MNIST, weights) for p in range(CPU_COUNT)]
	[pool.submit(pool_job_resnet, weights)]
	# with ProcessPoolExecutor(max_workers=CPU_COUNT) as pool:
	# 	pool.submit(pool_job_MNIST, weights)

	#while not queue.empty():
	while(True):
		if not queue.empty():
			print("Process Job id:", queue.get(block=True))
		#queue.task_done()

	#pool.close()
	#pool.terminate()
	exit()
