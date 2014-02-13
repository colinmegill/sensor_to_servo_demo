#!/usr/bin/python

import math
import sys
import qlib
import argparse
import numpy as np

parser = argparse.ArgumentParser()

parser.add_argument("--nStateDims",
                    metavar = '<int>',
                    type = int,
                    default = 4,
                    help = 'How many elements in the state vector.')

parser.add_argument("--actions",
                    metavar = "a1 a2 ... ak",
                    nargs = '+',
                    type = str,
                    default = [],
                    help = 'A list of actions.')

parser.add_argument("--epsilon",
                    metavar = '[0..1]',
                    type = float,
                    default = 0.1,
                    help = 'Randomization parameter in the epsilon-greedy exploration.')

parser.add_argument("--epsilonDecayRate",
                    metavar = '[0..1]',
                    type = float,
                    default = 0.00001,
                    help = 'How much the epsilon term decays over time.')

parser.add_argument("--learnRate",
                    metavar = '[0..1]',
                    type = float,
                    default = 0.3,
                    help = 'How much weight is given to the reward obtained by the new training sequence.')

parser.add_argument("--discountRate",
                    metavar = '[0..1]',
                    type = float,
                    default = 0.1,
                    help = 'How much future values are discounted during update by delayed reward.')

parser.add_argument("--replayMemorySize",
                    metavar = '[1,2,3,...]',
                    type = int,
                    default = 100,
                    help = 'How long training sequences can we hold at most.')

parser.add_argument("--loadModel",
                    metavar = '<file>',
                    type = str,
                    default = None,
                    help = 'Load model from file.')

parser.add_argument("--saveModel",
                    metavar = '<file>',
                    type = str,
                    default = None,
                    help = 'Save model to file.')


# Parse arguments
args = parser.parse_args()

# Stream for reading from
inStream  = sys.stdin

# Stream for writing to.
# NOTE: stream flushes everything it gets
outStream = sys.stdout 

# Define a value function
value = qlib.ValueFunctionMLP( nStateDims   = args.nStateDims,
                               nActions     = len(args.actions),
                               epsilon      = args.epsilon,
                               learnRate    = args.learnRate,
                               discountRate = args.discountRate )


if len(args.actions) == 0:
    raise Exception("No actions provided!")
    
# Open log for writing, unbuffered
log = open('log','w', 0)

# Stores a sampled sequence of state-action pairs 
replayMemory = []

idx = 0

while True:
    
    # We need to read lines like this, otherwise the lines get buffered
    try:
        line = inStream.readline().rstrip()
    except:
        break

    if line is None:
        break

    # log.write(line + '\n')
      
    value.epsilon = args.epsilon * math.exp( - args.epsilonDecayRate * idx)
  
    idx += 1

    ID = line.split(' ')[0]

    if ID == 'STATE':

        currState = np.array(map(float,line.split(' ')[1:]))

        if len(currState) != args.nStateDims:
            raise Exception("Input state '" +
                            str(currState) + "' does not have " +
                            str(args.nStateDims) + " elements!")
        
        # If we are not yet close enough to the goal, sample new action
        action = value.getEpsilonGreedyAction(currState)
        
        # Update replay memory
        replayMemory.append( (currState,action) )
        
        # Send the delta action to the controller
        msg = ' '.join(map(str,['DELTA_ACTION',args.actions[action]]))
        outStream.write(msg + '\n')
        outStream.flush()
            
    elif ID == 'REWARD':

        reward = float(line.split(' ')[1])

        n = len(replayMemory)
        
        # We can update the value function based on the replay memory
        # if it exists
        #if n > 10:
        #    thinnedReplayMemory = [replayMemory[i] for i in xrange(n-1)
        #                           if np.max(np.abs([replayMemory[i][0][k]-replayMemory[i+1][0][k] for k in xrange(args.nStateDims)])) > 0.1] + [replayMemory[-1]]
        #else:
        thinnedReplayMemory = replayMemory

            #thinnedReplayMemory = [replayMemory[i] for i in xrange(n-1)
        #                       if np.max(np.abs(replayMemory[i]-replayMemory[i+1])) > 0.1] + [replayMemory[-1]]
            
        #if n >= 10:
        #    thinnedReplayMemory = [replayMemory[i] for i in sorted(np.random.choice(n,size=10,replace=False))] + [replayMemory[-1]]
        #else:
        #    thinnedReplayMemory = replayMemory

        nThin = len(thinnedReplayMemory)
            
        if log:
            log.write('Thinned replay memory from ' + str(n) +
                      ' elements to ' + str(nThin) +
                      ' elements where reward is ' + str(reward) + '\n')

        if nThin > 0:
            value.updateValueByDelayedReward(thinnedReplayMemory,
                                             reward,
                                             log = log)
        #elif n >= 1 and reward < 0:
        #    value.updateValueByDelayedReward([replayMemory[-1]], reward)
        #    replayMemory.pop()

    elif ID == 'NEW_EPISODE':

        replayMemory = []

    else:
        break

















