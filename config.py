#### SELF PLAY
EPISODES = 1
MCTS_SIMS = 500
MEMORY_SIZE = 4000
TURNS_UNTIL_TAU0 = 400 # turn on which it starts playing deterministically
CPUCT = 4
EPSILON = 0.75
ALPHA = 0.03
KOMI = 6.5


#### RETRAINING
BATCH_SIZE = 256
EPOCHS = 10
REG_CONST = 0.0001
LEARNING_RATE = 0.0001
MOMENTUM = 0.9
TRAINING_LOOPS = 10

HIDDEN_CNN_LAYERS = [
	{'filters':75, 'kernel_size': (4,4)}
	 , {'filters':75, 'kernel_size': (4,4)}
	 , {'filters':75, 'kernel_size': (4,4)}
	 , {'filters':75, 'kernel_size': (4,4)}
	 , {'filters':75, 'kernel_size': (4,4)}
	 , {'filters':75, 'kernel_size': (4,4)}
	]

#### EVALUATION
EVAL_EPISODES = 1
SCORING_THRESHOLD = 1.3