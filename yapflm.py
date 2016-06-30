# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 08:25:34 2016

@author: nick
"""
from __future__ import division , print_function
from math import exp
from collections import deque
from itertools import cycle
from string import ascii_letters as let
import random
  
def prod(x):
    y = 1
    for _ in x:
        y *= _
    return y

def bitmaskarray(n,base=512,length=None):
    retval = []
    i = 1
    while n >= base:
        retval.append(n%base)
        n //= base
        i += 1
    retval.append(n)
    if length is not None:
        retarray = [0]*length
        retarray[:i] = retval
        return retarray[::-1]
    return retval[::-1]

def storebits(a,shift=9):
    retval = 0
    for i,x in enumerate(a[::-1]):
        retval += x * (shift**i)
    return retval

class FIS(object):
    oper =      {'max'      :   max,
                 'min'      :   min,
                 'sum'      :   sum,
                 'prod'     :   prod}
                 
    def __init__(self,name='',fistype='mamdani',andMethod='min',orMethod='max',
                  impMethod='min',aggMethod='max',defuzzMethod='centroid',
                  init=None,inRange=None,outRange=None):
        self.defuzz =    {'centroid' :   self.defuzzCentroid}
        self.input,self.output = [],[]
        self.name = name
        self.type = fistype
        self.andMethod = andMethod
        self.orMethod = orMethod
        self.impMethod = impMethod
        self.aggMethod = aggMethod
        self.defuzzMethod = defuzzMethod
        self.rule = []
        self._mfList = ['trimf','trapmf']
        if init is not None:
            self.init = [None]*4
            if inRange is None or outRange is None:
                r = (-1,1)
                inRange, outRange = cycle([r]),cycle([r])
                print("No range specified. Defaulting to [-1,1]")
            else:
                inRange = cycle(inRange)
                outRange = cycle(outRange)
            numInMFs = bitmaskarray(init[0],10)
            typeInMFs = bitmaskarray(init[1],512,len(numInMFs))
            for i,(inp,m) in enumerate(zip(numInMFs,typeInMFs)):
                self.addvar('input','input%d'%i,inRange.next())
                for j,mf in enumerate(bitmaskarray(m,2,inp)):
                    self.input[-1].addmf('%s%d'%(let[j],i),self._mfList[mf])
            numOutMFs = bitmaskarray(init[2],10)
            typeOutMFs = bitmaskarray(init[3],512,len(numOutMFs))
            for i,(outp,m) in enumerate(zip(numOutMFs,typeOutMFs)):
                self.addvar('output','output%d'%i,outRange.next())
                for j,mf in enumerate(bitmaskarray(m,2,outp)):
                    self.output[-1].addmf('%s%d'%(let[j],i),self._mfList[mf])
        else:
            self.init = [None]*4

    def __str__(self):
        sys_atts = ['name','type','andMethod','orMethod',
                     'defuzzMethod','impMethod','aggMethod']
        s = ''
        for att in sys_atts:
            s += '{0:>13}: {1}\n'.format(att,self.__dict__[att])
        s += '{:>13}:\n'.format('input')
        for inp in self.input:
            s += inp.__str__('\t')
        s += '{:>13}:\n'.format('output')
        for outp in self.output:
            s += outp.__str__('\t')
        s += '{:>13}:\n'.format('rule')
        for rule in self.rule:
            s += rule.__str__('\t\t') + '\n'
        return s
        
    def config(self):
        if len(self.input) == 0 or len(self.output) == 0:
            return None
        self.init = []
        self.init.append(storebits([len(i.mf) for i in self.input],10))
        self.init.append(storebits([storebits([self._mfList.index(mf.type) 
                        for mf in inp.mf],2) for inp in self.input],512))
        self.init.append(storebits([len(outp.mf) for outp in self.output],10))
        self.init.append(storebits([storebits([self._mfList.index(mf.type) 
                        for mf in outp.mf],2) for outp in self.output],512))
        return self.init
        
    def copy(self,encoded=None):
        inRanges = [inp.range for inp in self.input]
        outRanges = [outp.range for outp in self.output]
        retFIS = FIS(init=self.init,inRange=inRanges,outRange=outRanges)
        if encoded is not None:
            retFIS.decode(encoded)
        else:
            retFIS.decode(self.encode())
        rules = [r.encode() for r in self.rule]
        retFIS.addrule(rules)
        return retFIS

    def encode(self):
        var = self.input + self.output
        return deque(sum((sum([mf.params for mf in v.mf],[]) for v in var),[]))

    def decode(self,encoded):
        if not type(encoded) is deque:
            encoded = deque(encoded)
        var = self.input + self.output
        num_mf = [len(v.mf) for v in var]
        for i,num_in in enumerate(num_mf):
            for mf in xrange(num_in):
                params = var[i].mf[mf].params
                var[i].mf[mf].params = [encoded.popleft() for _ in params] 

    def randomize(self,ret=False):
        # This only works for well-order param lists (like tri and trap)
        out = deque()
        for var in self.input + self.output:
            for mf in var.mf:
                [out.append(x) for x in 
                       sorted((random.uniform(*var.range) for p in mf.params))]
        if ret:
            return out
        else:
            return self.copy(out)

    def addvar(self,vartype,varname,varrange):
        if vartype in 'input':
            if self.init[0] is None:
                self.init[:2] = [0,0]
            else:
                self.init[0] *= 10
                self.init[1] *= 512
            self.input.append(FuzzyVar(varname,varrange,self,1))
            if len(self.rule) > 0:
                for rule in self.rule:
                    rule.antecedent += [0]
        elif vartype in 'output':
            if self.init[2] is None:
                self.init[2:] = [0,0]
            else:
                self.init[2] *= 10
                self.init[3] *= 512
            self.output.append(FuzzyVar(varname,varrange,self,0))
            if len(self.rule) > 0:
                for rule in self.rule:
                    rule.consequent += [0]
        else:
            #Throw an invalid variable type exception
            pass

    def rmvar(self,vartype,varindex):
        if vartype in 'input':
            if varindex > len(self.input):
                #throw invalid variable reference exception
                pass
            del self.input[varindex]
            if len(self.input) == 0:
                self.rule = []
                return
            if len(self.rule) > 0:
                for rule in self.rule:
                    del rule.antecedent[varindex]
        elif vartype in 'output':
            if varindex > len(self.output):
                #throw invalid variable reference exception
                pass
            del self.output[varindex]
            if len(self.output) == 0:
                self.rule = []
                return
            if len(self.rule) > 0:
                for rule in self.rule:
                    del rule.consequent[varindex]
        else:
            #Throw an invalid variable type exception
            pass

    def addrule(self,rules):
        numInput = len(self.input)
        numOutput = len(self.output)
        if not any(isinstance(rule,list) for rule in rules):
            rules = [rules]
        for rule in rules:
            if not len(rule) != sum([numInput,numOutput,2]):
                #Throw an incorrect number of in/outputs exception
                pass
            antecedent = rule[:numInput]
            consequent = rule[numInput:numInput+numOutput]
            weight = rule[-2]
            connection = rule[-1]
            self.rule.append(Rule(antecedent,consequent,weight,connection))
    
    def evalfis(self,x):
        if not hasattr(x,'__iter__'):
            x = [x]
        elif len(x) != len(self.input):
            #Throw an incorrect number of inputs exception
            pass
        numout = len(self.output)
        ruleout = []
        outputs = []
#        numrule = len(self.rule)
        andMethod = self.oper[self.andMethod]
        orMethod = self.oper[self.orMethod]
        impMethod = self.oper[self.impMethod]
        aggMethod = self.oper[self.aggMethod]
        defuzzMethod = self.defuzz[self.defuzzMethod]
        comb = [andMethod,orMethod]
        for rule in self.rule:
            ruleout.append([])
            ant = rule.antecedent
            con = rule.consequent
            weight = rule.weight
            conn = rule.connection
            mfout = [self.input[i].mf[a].evalmf(x[i]) 
                                    for i,a in enumerate(ant) if a is not None]
            # Generalize for multiple output systems. Easy
            for out in xrange(numout):
                outset = self.output[out].mf[con[out]].evalset()
                rulestrength = weight*comb[conn](mfout)
                ruleout[-1].append([impMethod([rulestrength,y]) for y in outset])
        for o in xrange(numout):
            ruletemp = [r[o] for r in ruleout]
            agg = [aggMethod([y[i] for y in ruletemp]) 
                                             for i in xrange(len(ruletemp[0]))]
            outputs.append(defuzzMethod(agg,o))
        return outputs if len(outputs)>1 else outputs[0]
        
    def defuzzCentroid(self,agg,out):
        a,b = self.output[out].range
        points = len(agg)
        dx = (b-a)/(points - 1)
        totarea = sum(agg)
        if totarea == 0:
            print('Total area was zero. Using average of the range instead')
            return (a+b)/2
        totmom = 0
        for i,y in enumerate(agg):
            totmom += y*(a + i*dx)
        return totmom/totarea

class FuzzyVar(object):
    def __init__(self,varname,varrange,parent=None,vartype=None):
        self.name = varname
        self.range = varrange
        self.mf = []
        self.parent = parent
        if vartype:
            self.num = len(parent.input)
        elif vartype == 0:
            self.num = len(parent.output)
        self.vartype = vartype

    def __str__(self,indent=''):
        var_atts = ['name','range']
        s = ''
        for att in var_atts:
            s += indent + '{0:>10}: {1}\n'.format(att,self.__dict__[att])
        s += indent + '{:>10}:\n'.format('mf')
        for mf in self.mf:
            s += mf.__str__(indent+'\t') + '\n'
        return s
        
    def addmf(self,mfname,mftype,mfparams=None):
        mf = MF(mfname,mftype,mfparams)
        mf.range = self.range
        mftypes = {'trimf':0, 'trapmf':1}
        self.mf.append(mf)
        if self.vartype is None:
            return
        elif self.vartype:
            numIn = len(self.parent.input)
            self.parent.init[0] += 10**(numIn - self.num - 1)
            
            typeMFs = bitmaskarray(self.parent.init[1])
            if len(typeMFs) <= numIn:
                typeMFs = [0]*(numIn-len(typeMFs)) + typeMFs
            typeMFs[self.num] = (typeMFs[self.num]<<1) + mftypes[mftype]
            self.parent.init[1] = storebits(typeMFs)
        else:
            numOut = len(self.parent.output)
            self.parent.init[2] += 10**(numOut - self.num - 1)
            
            typeMFs = bitmaskarray(self.parent.init[1])
            if len(typeMFs) <= numOut:
                typeMFs = [0]*(numOut-len(typeMFs)) + typeMFs
            typeMFs[self.num] = (typeMFs[self.num]<<1) + mftypes[mftype]
            self.parent.init[3] = storebits(typeMFs)

class MF(object):
    def __init__(self,mfname,mftype,mfparams=None):
        self.name = mfname
        self.type = mftype
        
        mfdict = {'trimf'           :   (self.mfTriangle,3),
                  'trapmf'          :   (self.mfTrapezoid,4),
                  'trunctrilumf'    :   (self.mfTruncTriLeftUpper,4),
                  'trunctrillmf'    :   (self.mfTruncTriLeftLower,4),
                  'trunctrirumf'    :   (self.mfTruncTriRightUpper,4),
                  'trunctrirlmf'    :   (self.mfTruncTriRightLower,4),
                  'gaussmf'         :   (self.mfGaussian,2),
                  'gauss2mf'        :   (self.mfGaussian2,2)}
        
        self.mf = mfdict[self.type][0]
        if mfparams is not None:
            self.params = mfparams
        else:
            self.params = [0]*mfdict[self.type][1]
        if not mfdict[self.type][1] == len(self.params):
            #Throw invalid param number exception
            pass

    def __str__(self,indent=''):
        mf_atts = ['name','type','params']
        s = ''
        for att in mf_atts:
            s += indent + '{0:>10}: {1}\n'.format(att,self.__dict__[att])
        return s

    def evalmf(self,x):
        return self.mf(x)
        
    def evalset(self,points=101):
        if hasattr(self,'range'):
            a,b = self.range
        elif not 'gauss' in self.type:
            a,b = self.params[0],self.params[-1]
        else:
            a = self.params[1] - 6*self.params[0]
            b = -a
        #Fake linspace until I bring in numpy for the time being. Baby steps...
        dx = (b - a)/(points-1)
        xlinspace = [a + i*dx for i in xrange(points-1)] + [b]
        return [self.mf(x) for x in xlinspace]
    
    def mfTriangle(self,x,params=None):
        if params is not None:
            a,b,c = params
        else:
            a,b,c = self.params
        check = [b<a,c<b,a==b,b==c,a<=x<=c]
        if any(check[:2]):
            #Throw an invalid param exception
            pass
        if not check[4]:
#            print('outside of range')
            return 0
        if check[2]:
            return (c-x)/(c-b)
        elif check[3]:
            return (x-a)/(b-a)
        else:
            return min((x-a)/(b-a),(c-x)/(c-b))
            
    def mfTrapezoid(self,x,params=None):
        if params is not None:
            a,b,c,d = params
        else:
            a,b,c,d = self.params
        check = [b<a,c<b,d<c,a==b,b==c,c==d,a<=x<=d]
        if any(check[:3]):
            #Throw an invalid param exception
            pass
        if not check[6]:
#            print('outside of range')
            return 0
        if check[4]:
            return self.mfTriangle(x,[a,b,d])
        if check[3]:
            return min(1,(d-x)/(d-c))
        if check[5]:
            return min((x-a)/(b-a),1)
        else:
            return min((x-a)/(b-a),1,(d-x)/(d-c))
    
    def mfTruncTriLeftUpper(self,x,params=None):
        if params is not None:
            a,b,c,d = params
        else:
            a,b,c,d = self.params
        check = [b<a,c<b,d<c]
        if any(check):
            #Throw an inalid parameter exception
            pass
        if x<=c:
            return 1
        else:
            return self.mfTriangle(x,[a,b,d])

    def mfTruncTriLeftLower(self,x,params=None):
        if params is not None:
            a,b,c,d = params
        else:
            a,b,c,d = self.params
        check = [b<a,c<b,d<c]
        if any(check):
            #Throw an inalid parameter exception
            pass
        if x<=b:
            return 0
        else:
            return self.mfTriangle(x,[a,c,d])

    def mfTruncTriRightUpper(self,x,params=None):
        if params is not None:
            a,b,c,d = params
        else:
            a,b,c,d = self.params
        check = [b<a,c<b,d<c]
        if any(check):
            #Throw an inalid parameter exception
            pass
        if x>=b:
            return 1
        else:
            return self.mfTriangle(x,[a,c,d])

    def mfTruncTriRightLower(self,x,params=None):
        if params is not None:
            a,b,c,d = params
        else:
            a,b,c,d = self.params
        check = [b<a,c<b,d<c]
        if any(check):
            #Throw an inalid parameter exception
            pass
        if x>=c:
            return 0
        else:
            return self.mfTriangle(x,[a,b,d])

    def mfGaussian(self,x,params=None):
        if params is not None:
            sigma,c = params
        else:
            sigma,c = self.params
        if sigma == 0:
            #Throw invalid param exception
            pass
        t = (x-c)/sigma
        return exp(-t*t/2)
    
    def mfGaussian2(self):
        pass
        
class Rule(object):
    def __init__(self,antecedent,consequent,weight,connection):
        self.antecedent = antecedent
        self.consequent = consequent
        self.weight = weight
        self.connection = connection

    def __str__(self,indent=''):
        num_a = len(self.antecedent)
        num_c = len(self.consequent)
        ant = ' '.join('{%d!s:>4}'%i for i in xrange(num_a))
        con = ' '.join('{%d!s:>4}'%i for i in xrange(num_a,num_a+num_c))
        s = ant + ', ' + con + '  ({%d}) : {%d}'%(num_a+num_c,num_a+num_c+1)
        a = tuple(self.antecedent) + tuple(self.consequent) + \
                                     (self.weight,self.connection,)
        return indent + s.format(*a)
    
    def encode(self):
        return self.antecedent + self.consequent + [self.weight, self.connection]
