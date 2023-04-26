##  RESCUER AGENT
### @Author: Tacla (UTFPR)
### Demo of use of VictimSim

import heapq
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod
import math


## Classe que define o Agente Rescuer com um plano fixo
class Rescuer(AbstractAgent):
    def __init__(self, env, config_file):
        """ 
        @param env: a reference to an instance of the environment class
        @param config_file: the absolute path to the agent's config file"""

        super().__init__(env, config_file)

        # Specific initialization for the rescuer
        self.plan = []              # a list of planned actions
        self.rtime = self.TLIM      # for controlling the remaining time
        
        # Starts in IDLE state.
        # It changes to ACTIVE when the map arrives
        self.body.set_state(PhysAgent.IDLE)
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1)]
        self.walls = []
        self.victims = {}
        self.currentPos = (0,0)
        # planning



    def find_next_victim(self, next_victim):   
        lastMove = (0,0) 
        plan = []
        dir = []
        while self.currentPos != (next_victim[0]):
            nextLayer = False
            distances = []
            dir = self.directions.copy()

            for move in dir:
                newPos = tuple(map(lambda i, j: i + j, self.currentPos, move))
                if newPos in self.walls:
                    distances.append(1000)
                else:
                    x, y = next(iter(next_victim))
                    distance = math.sqrt((newPos[0]-x) ** 2 + (newPos[1]-y) ** 2)
                    distances.append(distance)
            # Find the move with the shortest distance to the next victim
            lastMoveComplement = (-1*lastMove[0], -1*lastMove[1])
            if(lastMove != (0,0)):
                if lastMoveComplement in dir:
                    index = dir.index(lastMoveComplement)
                    distances.pop(index)
                    dir.remove(lastMoveComplement)
            # If the best move is the opposite of the last move, remove it from the list of possible moves
            while(nextLayer == False):

                # if(lastMove != (0,0) and bestMove[0] == -1*lastMove[0] and bestMove[1] == -1*lastMove[1]):
                #     distances.remove(minDist)
                #     dir.remove(bestMove)

                minDist = min(distances)
                bestMove = dir[distances.index(minDist)]
                # if(bestMove == -1*lastMove):
                #     dir.remove(bestMove)
                #     distances.remove(minDist)
                #     # bestMove = random.choice(dir)
                #     minDist = min(distances)
                #     bestMove = self.directions[distances.index(minDist)]

                    

                # Move the agent
                result = self.body.walk(bestMove[0], bestMove[1])
                # print(self.currentPos, bestMove, result)
                # if bestMove[0] != 0 and bestMove[1] != 0:
                #     self.rtime -= self.COST_DIAG
                # else:
                #     self.rtime -= self.COST_LINE

                self.currentPos = (self.currentPos[0]+bestMove[0], self.currentPos[1]+bestMove[1])
                
                # Test the result of the walk action
                if result == PhysAgent.BUMPED:
                    walls = 1  # build the map- to do
                    # print(self.name() + ": wall or grid limit reached")
                    # self.walls.append(self.currentPos)
                    self.currentPos = (self.currentPos[0]-bestMove[0], self.currentPos[1]-bestMove[1]) 
                if result == PhysAgent.EXECUTED:
                    # print(self.name() + ": victim found")
                    seq = self.body.check_for_victim()
                    if seq >= 0:
                        res = self.body.first_aid(seq)
                        # Remove the victim from the list even if it is not the next victim using the self.currentPos
                        self.victims.index(self.currentPos)
                    lastMove = bestMove
                    plan.append(bestMove)  
                    nextLayer = True           
                
            print(self.currentPos, next_victim[0])
        return plan

    def go_save_victims(self, walls, victims):
        """ The explorer sends the map containing the walls and
        victims' location. The rescuer becomes ACTIVE. From now,
        the deliberate method is called by the environment"""
        self.walls = walls
        self.victims = sorted(victims.items(), key=lambda x: x[1][7], reverse=True)
        #planning
        self.__planner()
        self.body.set_state(PhysAgent.ACTIVE)
        
    
    def __planner(self):
        """ A private method that calculates the walk actions to rescue the
        victims. Further actions may be necessary and should be added in the
        deliberata method"""

        # This is a off-line trajectory plan, each element of the list is
        # a pair dx, dy that do the agent walk in the x-axis and/or y-axis

        for victim in self.victims:
            moveToNextVictim = self.find_next_victim(victim)
            for move in moveToNextVictim:
                self.plan.append(move)
        
    def deliberate(self) -> bool:
        """ This is the choice of the next action. The simulator calls this
        method at each reasonning cycle if the agent is ACTIVE.
        Must be implemented in every agent
        @return True: there's one or more actions to do
        @return False: there's no more action to do """

        # No more actions to do
        if self.plan == []:  # empty list, no more actions to do
           return False

        # Takes the first action of the plan (walk action) and removes it from the plan
        dx, dy = self.plan.pop(0)

        # Walk - just one step per deliberation
        result = self.body.walk(dx, dy)

        # Rescue the victim at the current position
        if result == PhysAgent.EXECUTED:
            # check if there is a victim at the current position
            seq = self.body.check_for_victim()
            if seq >= 0:
                res = self.body.first_aid(seq) # True when rescued             

        return True

