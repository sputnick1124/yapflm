#!/usr/bin/env python
from __future__ import division, print_function
from yapflm import FIS, FuzzyVar, FuzzyRule, MF, ParamError
from operator import mul

from itertools import product
from random import random, randint, sample
from copy import deepcopy

def valid_tri(params):
    """
    Helper function to test inclusion of x in interval
    """
    return params[0] <= params[1] <= params[2]

class GFS(FIS):
    """
    A genetic representation of a Fuzzy system. Contains methods to reproduce,
    mutate, and randomize its own parameters.
    """
    def __init__(self,in_mfs,out_mfs,name='',in_ranges=None,out_ranges=None):
        super(GFS,self).__init__(name=name)
        if not hasattr(in_mfs,'__iter__'):
            self.in_mfs = [in_mfs]
        else:
            self.in_mfs = in_mfs
        if not hasattr(out_mfs,'__iter__'):
            self.out_mfs = [out_mfs]
        else:
            self.out_mfs = out_mfs
        self.in_ranges = in_ranges
        self.out_ranges = out_ranges
        self.num_in = len(self.in_mfs)
        self.num_out = len(self.out_mfs)
        self.num_rule = reduce(mul,self.in_mfs)
        
        self.init_vars()
        self.init_rules()

    def init_vars(self):
        if self.in_ranges is None:
            in_ranges = [(0,1) for _ in range(len(self.in_mfs))]
        else:
            in_ranges = self.in_ranges
        if self.out_ranges is None:
            out_ranges = [(0,1) for _ in range(len(self.out_mfs))]
        else:
            out_ranges = self.out_ranges
        for inp,input_mfs in enumerate(self.in_mfs):
            self.addvar(input_mfs,'input','',in_ranges[inp])
        for outp,output_mfs in enumerate(self.out_mfs):
            self.addvar(output_mfs,'output','',out_ranges[outp])

    def init_rules(self):
        self.rule = GenFuzzyRuleBase(in_mfs=self.in_mfs,out_mfs=self.out_mfs)

    def randomize(self):
        self.randomize_vars()
        self.randomize_rule_base()

    def randomize_vars(self):
        for inp in self.input:
            inp.randomize()
        for outp in self.output:
            outp.randomize()

    def randomize_rule_base(self):
        self.rule.randomize()

    def crossover(self,other):
        c1 = deepcopy(self)
        c2 = deepcopy(self)
        for i in range(len(self.input)):
            s1,s2 = self.input[i].crossover(other.input[i])
            c1.input[i].update(s1)
            c2.input[i].update(s2)
        for o in range(len(self.output)):
            s1,s2 = self.output[o].crossover(other.output[o])
            c1.output[o].update(s1)
            c2.output[o].update(s2)
        c1.rule,c2.rule = self.rule.crossover(other.rule)
        return c1,c2

    def mutate(self,percent=0):
        variables = sample(self.input + self.output,1)
        for var in variables:
            var.mutate(randint(0,var.num_mfs-1),randint(0,2),percent)
        self.rule.mutate()

    def addvar(self,num_mfs,vartype,varname,varrange):
        if vartype in 'input':
            self.input.append(GenFuzzyVar(num_mfs,1,varrange))
        elif vartype in 'output':
            self.output.append(GenFuzzyVar(num_mfs,0,varrange))
        else:
            #Throw an invalid variable type exception
            pass

class GenFuzzyVar(FuzzyVar):
    def __init__(self,num_mfs,vartype=None,varrange=None):
        super(GenFuzzyVar,self).__init__(varname='',vartype=vartype)
        self.num_mfs = num_mfs
        self.num_params = num_mfs*3
        if varrange is None:
            self.varrange = (0,1)
        else:
            self.varrange = varrange
        if 1:#vartype:
            interval = (self.varrange[1]-self.varrange[0])/(num_mfs-1)
            bins = []
            # make the 'buckets' in which the params need to reside
            bins.append((self.varrange[0],self.varrange[0]+interval/2))
            for mf in range(1,num_mfs-1):
                lo = self.varrange[0] + interval*mf - interval/2
                if abs(lo) < 1e-10:
                    lo = 0
                hi = self.varrange[0] + interval*mf + interval/2
                if abs(hi) < 1e-10:
                    hi = 0
                bins.append((lo,hi))
            bins.append((self.varrange[1] - interval/2, self.varrange[1]))
            # assign a bucket to each of the params
            buckets = [(self.varrange[0],)*2]*2 + [bins[1]]        
            for p in range(1,len(bins)-1):
                buckets.append(bins[p-1])
                buckets.append(bins[p])
                buckets.append(bins[p+1])
            buckets.append(bins[-2])
            buckets.extend([(self.varrange[1],)*2]*2)
            for b in range(self.num_mfs):
                self.addmf('',buckets[b*3:b*3+3],self)
        else:
            buckets = [None,(self.varrange[0],self.varrange[1])]
            for b in range(self.num_mfs):
                self.addmf('',buckets,self)

    def serialize(self):
        return sum([mf.params for mf in self.mf],[])

    def update(self,params):
        if not len(self.mf):
            for mf in range(self.num_mfs):
                self.addmf(mfname='',mfparams=params[mf*3:mf*3+3])
        else:
            for ind,mf in enumerate(self.mf):
                mf.params = params[ind*3:ind*3+3]

    def addmf(self,mfname,buckets,parent=None):
        try:
            mf = GenFuzzyMF(mfname,buckets,parent)
        except ParamError as e:
            raise(e)
        self.mf.append(mf)
                

    def randomize(self):
        for mf in self.mf:
            mf.randomize()

    def mutate(self,mf,gene,perc=0):
        self.mf[mf].mutate(gene)

    def crossover(self,other):
        c1,c2 = [],[]
        for p1,p2 in zip(self.mf,other.mf):
            c_1,c_2 = p1.crossover(p2)
            c1.extend(c_1)
            c2.extend(c_2)
        return c1,c2

class GenFuzzyMF(MF):
    def __init__(self,mfname='',buckets=None,parent=None):
        if buckets is not None:
            self.buckets = buckets
        else:
            pass #throw error
        if buckets[0] is None: #must be an output, let mfs float
            params = sorted([random()*(buckets[1][1]-buckets[1][0])+buckets[1][0] for _ in range(3)])
        else:
            params = [random()*(b[1]-b[0]) + b[0] for b in self.buckets]
        super(GenFuzzyMF,self).__init__(mfname,params,parent)

    def mutate(self,gene,perc=0):
        r = random()
        cur = self.params[gene]
        tau = randint(0,1)
        b = 0
        if self.buckets[0] is not None:
            if tau:
                delta = (self.buckets[gene][1] - cur) * (1-r*(1-perc**b))
            else:
                delta = -(cur - self.buckets[gene][0]) * (1-r*(1-perc**b))
        else:
            top = self.params[gene+1] if gene != 2 else self.buckets[1][1]
            bot = self.params[gene-1] if gene != 0 else self.buckets[1][0]
            if tau:
                delta = (top - cur) * r*(1 - (1-perc**b))
            else:
                delta = -(cur - bot) * r*(1 - (1-perc**b))
        self.params[gene] += delta
        if not valid_tri(self.params):
            print("Mutation: ",end='')
            print("tau=",tau,"delta=",delta,"cur=",cur,"params=",self.params)
            if self.buckets[0] is not None:
                print("bucket=",self.buckets[gene])
            else:
                print("top=",top,"bot=",bot)

    def randomize(self):
        if self.buckets[0] is None:
            self.params = sorted([random()*(self.buckets[1][1]-self.buckets[1][0])+self.buckets[1][0] for _ in range(3)])
            if not valid_tri(self.params):
                print('INPUT:')
                print(self.params)
        else:
            self.params = [random()*(b[1]-b[0]) + b[0] for b in self.buckets]
            if not valid_tri(self.params):
                print('OUTPUT:')
                print(self.params)

    def crossover(self,other):
        blended = random #function alias
        uniform = lambda:randint(0,1) #function alias
        selection = uniform #method selector
        if self.buckets[0] is not None:
            c1,c2 = [],[]
            for p1,p2,b in zip(self.params,other.params,self.buckets):
                bmin,bmax = b[:]
                R = bmax - bmin
                if not R:
                    c1.append(p1)
                    c2.append(p2)
                else:
                    xmin,xmax = min(p1,p2),max(p1,p2)
                    I = 0#xmax - xmin
                    lamb = selection()
                    new_xmin = xmin - (I/R)*(xmin - bmin)
                    new_xmax = xmax + (I/R)*(bmax - xmax)
                    c1.append(lamb*new_xmin + (1-lamb)*new_xmax)
                    c2.append((1-lamb)*new_xmin + lamb*new_xmax)
            if not valid_tri(c1) or not valid_tri(c2):
                print('INPUT:')
                print(self.buckets)
                print(self.params,other.params)
                print(c1,c2)
        else:
            c1,c2 = [None]*3,[None]*3
#            print("Parents: ",self.params,other.params)
            for i in [1,0,2]:
                p1,p2 = self.params[i],other.params[i]
                if i == 1:
                    xmin,xmax = min(p1,p2),max(p1,p2)
                elif i == 0:
                    xmin = min(p1,p2)
                    xmax = min(self.params[i+1],other.params[i+1])
                elif i == 2:
                    xmin = max(self.params[i-1],other.params[i-1])
                    xmax = max(p1,p2)

                lamb = selection()
                c1[i] = lamb*xmin + (1-lamb)*xmax
                c2[i] = (1-lamb)*xmin + lamb*xmax
#                print(i,": ",c1,c2,self.buckets)
            if not valid_tri(c1) or not valid_tri(c2):
                print('OUTPUT:')
                print(self.params,other.params)
                print(c1,c2)
        return c1,c2

class GenFuzzyRuleBase(object):
    def __init__(self,in_mfs=None,out_mfs=None,antecedents=None,consequents=None):
        self.rules = []
        if antecedents is not None:
            self.antecedents = antecedents
        else:
            self.init_antecedents(in_mfs)
        self.out_mfs = out_mfs
        self.weights = [1]*len(self.antecedents)
        self.connections = [1]*len(self.antecedents)
        if consequents is not None:
            self.consequents = consequents
            self.update()
        else:
            self.consequents = None

    def __iter__(self):
        return (rule for rule in self.rules)

    def __getitem__(self,key):
        return self.rules[key]
    
    def append(self,item):
        self.rules.append(item)

    def init_antecedents(self,in_mfs):
        ranges = map(range,in_mfs)
        self.antecedents = [list(x) for x in product(*ranges)]

    def update(self):
        if not len(self.rules):
            self.rules = [FuzzyRule(ant,con,w,c) for ant,con,w,c in zip(
                                            self.antecedents,
                                            self.consequents,
                                            self.weights,
                                            self.connections)]
        else:
            for rule,con in zip(self.rules,self.consequents):
                rule.consequent = con[:]
    
    def serialize(self):
        return self.consequents

    def randomize(self):
        self.consequents = []
        for ant in self.antecedents:
            self.consequents.append([randint(0,mf-1) for mf in self.out_mfs])
        self.update()

    def mutate(self,num_gen=2):
        up_down = (-1,1)
        for g in range(num_gen):
            tau = randint(0,1)
            m = randint(0,len(self.consequents)-1)
            c = randint(0,len(self.out_mfs)-1)
            if (self.consequents[m][c] == 0) and (self.out_mfs[c] > 0):
                self.consequents[m][c] += 1
            elif (self.consequents[m][c] == self.out_mfs[c]-1):
                self.consequents[m][c] -= 1
            else:
                self.consequents[m][c] += up_down[tau]
        self.update()
            

    def crossover(self,other):
        """
        Two-point crossover
        """
        p1 = self.consequents[:]
        p2 = other.consequents[:]
        i,j  = randint(0,len(self.consequents)), randint(0,len(self.consequents))
        c1 = p1[:i] + p2[i:j] + p1[j:]
        c2 = p2[:i] + p1[i:j] + p2[j:]
        return GenFuzzyRuleBase(antecedents=self.antecedents,consequents=c1,out_mfs=self.out_mfs),\
               GenFuzzyRuleBase(antecedents=self.antecedents,consequents=c2,out_mfs=self.out_mfs)
