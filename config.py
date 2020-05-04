#### PLAYING
SECS_PER_TURN = 1
TRAINED_MODEL_PATH = "saved_models/20170718"
USE_CPU = True

#### SELF PLAY
EPISODES = 1
MCTS_SIMS = 3
MEMORY_SIZE = 300
TURNS_UNTIL_TAU0 = 80 # turn on which it starts playing deterministically
CPUCT = 1
EPSILON = 0.5
ALPHA = 0.5
KOMI = 6.5


#### RETRAINING
BATCH_SIZE = 256
EPOCHS = 1
REG_CONST = 0.0001
LEARNING_RATE = 0.1
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