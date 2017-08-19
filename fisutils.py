#!/usr/bin/env python
from matplotlib import pyplot as plt
plt.ion()

def plot_fis(fis):
    axes = []
    for i in fis.input:
        plt.figure()
        ax = plt.axes()
        axes .append(ax)
        names = []
        for m in i.mf:
            ax.plot(m.params,[0] + [1]*(len(m.params)>>1) + [0])
            names.append(m.name)
        plt.legend(names)
        plt.title(i.name)
    
    for o in fis.output:
        plt.figure()
        ax = plt.axes()
        axes.append(ax)
        names = []
        for m in o.mf:
            ax.plot(m.params,[0] + [1]*(len(m.params)>>1) + [0])
            names.append(m.name)
        plt.legend(names)
        plt.title(i.name)
    return axes

class FisPlot(object):
    def __init__(self,fis):
        self.fis = fis
        self.axes = plot_fis(self.fis)
    
    def eval_input(self,x):
        return self.fis.evalfis(x)
