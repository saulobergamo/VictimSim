## EXPLORER AGENT
### @Author: Tacla, UTFPR
### It walks randomly in the environment looking for victims.

import math
import sys
import os
import random
from abstract_agent import AbstractAgent
from physical_agent import PhysAgent
from abc import ABC, abstractmethod


class Explorer(AbstractAgent):
    def __init__(self, env, config_file, resc):
        """ Construtor do agente random on-line
        @param env referencia o ambiente
        @config_file: the absolute path to the explorer's config file
        @param resc referencia o rescuer para poder acorda-lo
        """

        super().__init__(env, config_file)
        
        # Specific initialization for the rescuer
        self.resc = resc           # reference to the rescuer agent
        self.rtime = self.TLIM     # remaining time to explore   

        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (1, 1), (-1, -1), (1, -1)]
        self.currentPos = (0,0)
        self.victims = []
        self.walls = []
        self.visited = [self.currentPos]
        self.layer = 0
    
    # Calculates the euclidian distance between two points and returns True if the distance is greater than 15
    def euclidianDistance(self, pos1, pos2):
        if (((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)**0.5) > 15:
            return True

    # This method is called to return the best move for the explorer
    def nextMove(self, currentPos):
        
        # Starting the spiral search from the agent's current position
        while True:
            nodes_to_explore = []
            for i in range(-self.layer, self.layer+1):
                for j in range(-self.layer, self.layer+1):
                    if abs(i) == self.layer or abs(j) == self.layer:
                        node = (currentPos[0]+i, currentPos[1]+j)
                        if node not in self.visited and node not in self.walls:
                            nodes_to_explore.append(node)
            
            # Exploring the nodes in the order defined by the movement options
            random.shuffle(self.directions)
            for direction in self.directions:
                new_pos = (currentPos[0] + direction[0], currentPos[1] + direction[1])
                if new_pos in nodes_to_explore:
                    return direction
            
            # If none of the neighboring nodes can be explored, choose a random direction to break out of the deadlock
            if not nodes_to_explore:
                return random.choice(self.directions)
            
            self.layer += 1

    # Based on the A* algorithm, uses the Euclidean distance from the current position to the desired position (0,0)
    def returnToBase(self):
        
        while self.currentPos != (0,0):
            distances = []
            for move in self.directions:
                newPos = tuple(map(lambda i, j: i + j, self.currentPos, move))
                if newPos in self.walls:
                    distances.append(1000)
                else:
                    distance = math.sqrt(newPos[0] ** 2 + newPos[1] ** 2)
                    distances.append(distance)
            # Find the move with the shortest distance to the base
            minDist = min(distances)
            bestMove = self.directions[distances.index(minDist)]
        
            # Move the agent
            result = self.body.walk(bestMove[0], bestMove[1])
            print(self.currentPos, bestMove, result)
            if bestMove[0] != 0 and bestMove[1] != 0:
                self.rtime -= self.COST_DIAG
            else:
                self.rtime -= self.COST_LINE

            self.currentPos = (self.currentPos[0]+bestMove[0], self.currentPos[1]+bestMove[1])
            
            # Test the result of the walk action
            if result == PhysAgent.BUMPED:
                walls = 1  # build the map- to do
                # print(self.name() + ": wall or grid limit reached")
                self.walls.append(self.currentPos)
                self.currentPos = (self.currentPos[0]-bestMove[0], self.currentPos[1]-bestMove[1]) 
            
            if result == PhysAgent.EXECUTED:
                # check for victim returns -1 if there is no victim or the sequential
                # the sequential number of a found victim
                seq = self.body.check_for_victim()
                if seq >= 0:
                    vs = self.body.read_vital_signals(seq)
                    self.rtime -= self.COST_READ
                    # print("exp: read vital signals of " + str(seq))
                    # print(vs)

    
    def deliberate(self) -> bool:
        """ The agent chooses the next action. The simulator calls this
        method at each cycle. Must be implemented in every agent"""

        # No more actions, time almost ended
        if self.euclidianDistance(self.currentPos, (0,0)) or self.rtime < 15.0: 
            # time to wake up the rescuer
            # pass the walls and the victims (here, they're empty)
            print(f"{self.NAME} I believe I've remaining time of {self.rtime:.1f}")

            # print("Current position="+str(self.currentPos))
            self.returnToBase()
            # print("Final position="+str(self.currentPos))
            
            self.resc.go_save_victims(self.walls,self.victims)
            return False
        
        nextMove = self.nextMove(self.currentPos)

        # Moves the body to another position
        result = self.body.walk(nextMove[0], nextMove[1])

        # Update remaining time
        if nextMove[0] != 0 and nextMove[1] != 0:
            self.rtime -= self.COST_DIAG
        else:
            self.rtime -= self.COST_LINE

        self.currentPos = (self.currentPos[0]+nextMove[0], self.currentPos[1]+nextMove[1])
        
        # Test the result of the walk action
        if result == PhysAgent.BUMPED:
            walls = 1  # build the map- to do
            # print(self.name() + ": wall or grid limit reached")
            self.walls.append(self.currentPos)
            self.currentPos = (self.currentPos[0]-nextMove[0], self.currentPos[1]-nextMove[1])


        if result == PhysAgent.EXECUTED:
            # check for victim returns -1 if there is no victim or the sequential
            # the sequential number of a found victim
            seq = self.body.check_for_victim()
            if seq >= 0:
                vs = self.body.read_vital_signals(seq)
                self.rtime -= self.COST_READ
                # print("exp: read vital signals of " + str(seq))
                # print(vs)
                self.victims.append(self.currentPos)
            
            self.visited.append(self.currentPos)

        return True

