# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 21:05:15 2016

@author: nick
"""
from __future__ import print_function, division, absolute_import
import random

class GA(object):
    def __init__(self,popSize=100,genMax=200,numElite=15,numRecomb=50,
                 numMut=25,numRand=10):
        popTrial = sum(numElite,numRecomb,numMut,numRand)
        if popTrial != popSize:
            popPer = popSize/popTrial
            numElite = numElite*popPer
            numRecomb = numRecomb*popPer
            numMut = numMut*popPer
            numRand = numRand*popPer
            print('Incorrect population slicing. Numbers have been scaled to'
                  'fit popSize')
        self.popSize = popSize
        self.genMax = genMax
        self.numElite = numElite
        self.numRecomb = numRecomb
        self.numMut = numMut
        self.numRand = numRand
        self.numParents = popSize//5

    def addSystem(self,system):
        if not all(hasattr(system,x) for x in ('randomize')):
            print("This system is not valid for GA optimization")
            return
        self.system = system
        self.ranges = system.getranges()
    
    def initPop(self,popSize=None):
        if popSize is None:
            popSize = self.popSize
        return [self.system.randomize() for i in xrange(popSize)]
    
    def evalPop(self):
        pass
    
    def setFitnessFn(self,function):
        self.fitness_fn = function
    
    def crossover(self,ind1,ind2):
        x1 = ind1.encode()
        x2 = ind2.encode()
        for x1x2 in zip(x1,x2):
            xMin,xMax = min(x1x2),max(x1x2)
            
        try:
            child = parent[0].replicate(encoded)
        except ParamError as e:
            return
        
        