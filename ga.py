# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 21:05:15 2016

@author: nick
"""
from __future__ import print_function, division, absolute_import
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
        self.genMax = genMax
        self.numElite = numElite
        self.numRecomb = numRecomb
        self.numMut = numMut
        self.numRand = numRand
        self.numParents = popSize//5

    def addSystem(self,system):
        if not any(hasattr())
        self.system = system
    
    def initPop(self):
        