# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 10:23:04 2016

@author: nick
"""

import sys
sys.path.append('..')
from ga import GFS, GA
from matplotlib import pyplot as plt

class fitness_fn(object):
    def __init__(self,fn):
        dx = 0.01
        self.x = [dx*i for i in range(100)]
        self.ya = list(map(fn, self.x))
    def __call__(self,fis):
        yf = map(fis.evalfis,self.x)
        mean_yf = sum(yf)/len(yf)
        SS1,SS2 = zip(*(((f-mean_yf)**2,(f-a)**2) for f,a in zip(yf,self.ya)))
#        SSres = sum((f-a)**2 for f,a in zip(yf,self.ya))
        SStot = sum(SS1)
        SSres = sum(SS2)
        return abs(SSres/SStot) if SStot else 1000
        

#def fitness(fis):
#    x = [dx*i for i in range(100)]
#    ya = list(map(lambda x: x**(0.45), x))
#    yf = map(fis.evalfis,x)
#    mean_yf = sum(yf)/len(yf)
#    SStot = sum((f-mean_yf)**2 for f in yf)
#    SSres = sum((f-a)**2 for f,a in zip(yf,ya))
#    return abs(SSres/SStot) if SStot else 1000

fn = lambda x: x**(0.45)
fitness1 = fitness_fn(fn)

myfis = GFS(init=[3,0,2,0],inRange=[-0.5,1.5],outRange=[-0.5,1.5],
            rules = ((0,0,1,0),(1,1,1,0),(2,1,1,0)))
myfis.keep_rules = False
myga = GA(popSize=25)
myga.addSystem(myfis)
myga.addFitness(fitness1)
best = myga.evalGA()

dx = 0.01
x = [dx*i for i in range(100)]
ya = list(map(lambda x: x**(0.45), x))
yf = map(best.evalfis,x)
#yf = [myfis.evalfis(xx) for xx in x]



plt.plot(x,ya,'b',x,yf,'g--')
plt.legend(['x^.45',"Fuzzy Approx"],loc='best')
plt.show()