# -*- coding: utf-8 -*-
# %matplotlib inline

import numpy as np
np.set_printoptions(suppress=True)
from shutil import copyfile
import random
from importlib import reload
from game import Game, GameState
from agent import Agent
from funcs import playMatches
from settings import run_folder, run_archive_folder
import pickle
import config



print('\n')

######## CREATE THE PLAYERS ########


iteration = 0
while 1:
    iteration += 1
    print('ITERATION NUMBER ' + str(iteration))
    _,  _, _ = playMatches(config.EPISODES)
    print('\n')