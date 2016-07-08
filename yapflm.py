# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 08:25:34 2016

@author: nick
"""
from __future__ import division , print_function
from math import exp
  
def prod(x):
    y = 1
    for _ in x:
        y *= _
    return y


class FIS(object):
    oper =      {'max'      :   max,
                 'min'      :   min,
                 'sum'      :   sum,
                 'prod'     :   prod}
                 
    def __init__(self,name='',fistype='mamdani',andMethod='min',orMethod='max',
                  impMethod='min',aggMethod='max',defuzzMethod='centroid'):
        self.defuzz =    {'centroid' :   defuzzCentroid}
        self.input,self.output = [],[]
        self.name = name
        self.type = fistype
        self.andMethod = andMethod
        self.orMethod = orMethod
        self.impMethod = impMethod
        self.aggMethod = aggMethod
        self.defuzzMethod = defuzzMethod
        self.rule = []

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
    
    def __eq__(self,other):
        return self.__dict__ == other.__dict__
    
    def check(self):
        return all(var.check() for var in self.input + self.output)
        
    def addvar(self,vartype,varname,varrange):
        if vartype in 'input':
            self.input.append(FuzzyVar(varname,varrange,self,1))
            if len(self.rule) > 0:
                for rule in self.rule:
                    rule.antecedent += [0]
        elif vartype in 'output':
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
        if not any(hasattr(rule,'__iter__') for rule in rules):
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
            mode = 1
            for out in xrange(numout):
                rulestrength = weight*comb[conn](mfout)
                outset = self.output[out].mf[con[out]].evalset(
                            firing_strength=rulestrength,impMethod=impMethod,mode=mode)
#                ruleout[-1].append([impMethod([rulestrength,y]) for y in outset])
                ruleout[-1].append(outset)
        for o in xrange(numout):
            if mode:
                ruletemp = [r[o] for r in ruleout]
                agg = [aggMethod([y[i] for y in ruletemp]) 
                                                 for i in xrange(len(ruletemp[0]))]
                outputs.append(defuzzMethod(agg,self.output[o].range))
            else:
                ruletemp = [r[o] for r in ruleout]
                infer = 0
        return outputs if len(outputs)>1 else outputs[0]

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
    
    def __eq__(self,other):
        local_dict = self.__dict__.copy()
        other_dict = other.__dict__.copy()
        local_dict.pop('parent')
        other_dict.pop('parent')
        return local_dict == other_dict
        
    def check(self):
        retval =  any(mf.evalmf(None) for mf in self.mf)
        return retval
        
    def addmf(self,mfname,mftype,mfparams=None):
        try:
            mf = MF(mfname,mftype,mfparams,self)
        except ParamError as e:
            raise e
        mf.range = self.range
        self.mf.append(mf)

class MF(object):
    def __init__(self,mfname,mftype,mfparams,parent=None):
        self.name = mfname
        self.type = mftype
        
        mfdict = {'trimf'           :   (mfTriangle,3),
                  'trapmf'          :   (mfTrapezoid,4),
                  'trunctrilumf'    :   (mfTruncTriLeftUpper,4),
                  'trunctrillmf'    :   (mfTruncTriLeftLower,4),
                  'trunctrirumf'    :   (mfTruncTriRightUpper,4),
                  'trunctrirlmf'    :   (mfTruncTriRightLower,4),
                  'gaussmf'         :   (mfGaussian,2),
                  'gauss2mf'        :   (mfGaussian2,2)}
        
        self.mf = mfdict[self.type][0]
        if mfparams is not None:
            self.params = mfparams
        elif parent is not None:
            r = parent.range[1] - parent.range[0]
            p = mfdict[self.type][1]
            dr = r/(p-1)
            self.params = [parent.range[0]+i*dr for i in xrange(p)]
        else:
            self.params = [0]*mfdict[self.type][1]
        if not mfdict[self.type][1] == len(self.params):
            #Throw invalid param number exception
#            raise(Exception)
            pass
        try:
            self.mf(None,self.params)
#            self.params = mfparams
        except ParamError as e:
            raise e

    def __str__(self,indent=''):
        mf_atts = ['name','type','params']
        s = ''
        for att in mf_atts:
            s += indent + '{0:>10}: {1}\n'.format(att,self.__dict__[att])
        return s
    
    def __eq__(self,other):
        local_dict = self.__dict__.copy()
        other_dict = other.__dict__.copy()
        local_dict.pop('parent')
        other_dict.pop('parent')
        return local_dict == other_dict

    def evalmf(self,x):
        return self.mf(x,self.params)
        
    def evalset(self,points=101,firing_strength=1,impMethod=min,mode=1):
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
        if mode:
            return [impMethod(firing_strength,self.mf(x,self.params)) for x in xlinspace]
        else:
            mv,start = 0,0
            for i,x in enumerate(xlinspace):
                outx = self.mf(x,self.params)
                mv,start = (outx,i) if outx>mv else (mv,start)
                if mv == firing_strength:
                    avg = sum(xlinspace[start:i])/(i-start)
            return mv,avg
                
        
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
    
    def __eq__(self,other):
        return self.__dict__ == other.__dict__
    
    def encode(self):
        return self.antecedent + self.consequent + (self.weight, self.connection)

def mfTriangle(x,params):
    a,b,c = params
    check = [a==b,b==c,a<=x<=c]
    if x is None:
        err = [b<a,c<b]
        if any(err):
            #Throw an invalid param exception
            errs = ['b<a','c<b']
            e = [errs[i] for i,_ in enumerate(err) if _]
            raise ParamError(params,'Invalid params {}: {}'.format(e,params))
        else:
            return 0 #Everything looks good
    if not check[2]:
#        print('outside of range')
        return 0
    if check[0]:
        return (c-x)/(c-b)
    elif check[1]:
        return (x-a)/(b-a)
    else:
        return min((x-a)/(b-a),(c-x)/(c-b))
        
def mfTrapezoid(x,params):
    a,b,c,d = params
    check = [a==b,b==c,c==d,a<=x<=d]
    if x is None:
        err = [b<a,c<b,d<c]
        if any(err):
            #Throw an invalid param exception
            errs = ['b<a','c<b','d<c']
            e = [errs[i] for i,_ in enumerate(err) if _]
            raise ParamError(params,'Invalid params {}: {}'.format(e,params))
        else:
            return 0 #Everything looks good
    if not check[3]:
#            print('outside of range')
        return 0
    if check[1]:
        return mfTriangle(x,[a,b,d])
    if check[0]:
        return min(1,(d-x)/(d-c))
    if check[2]:
        return min((x-a)/(b-a),1)
    else:
        return min((x-a)/(b-a),1,(d-x)/(d-c))

def mfTruncTriLeftUpper(x,params):
    a,b,c,d = params
    if x is None:
        err = [b<a,c<b,d<c]
        if any(err):
            #Throw an invalid param exception
            errs = ['b<a','c<b','d<c']
            e = [errs[i] for i,_ in enumerate(err) if _]
            raise ParamError(params,'Invalid params {}: {}'.format(e,params))
        else:
            return 0 #Everything looks good
    if x<=c:
        return 1
    else:
        return mfTriangle(x,[a,b,d])

def mfTruncTriLeftLower(x,params):
    a,b,c,d = params
    if x is None:
        err = [b<a,c<b,d<c]
        if any(err):
            #Throw an invalid param exception
            errs = ['b<a','c<b','d<c']
            e = [errs[i] for i,_ in enumerate(err) if _]
            raise ParamError(params,'Invalid params {}: {}'.format(e,params))
        else:
            return 0 #Everything looks good
    if x<=b:
        return 0
    else:
        return mfTriangle(x,[a,c,d])

def mfTruncTriRightUpper(x,params):
    a,b,c,d = params
    if x is None:
        err = [b<a,c<b,d<c]
        if any(err):
            #Throw an invalid param exception
            errs = ['b<a','c<b','d<c']
            e = [errs[i] for i,_ in enumerate(err) if _]
            raise ParamError(params,'Invalid params {}: {}'.format(e,params))
        else:
            return 0 #Everything looks good
    if x>=b:
        return 1
    else:
        return mfTriangle(x,[a,c,d])

def mfTruncTriRightLower(x,params):
    a,b,c,d = params
    if x is None:
        err = [b<a,c<b,d<c]
        if any(err):
            #Throw an invalid param exception
            errs = ['b<a','c<b','d<c']
            e = [errs[i] for i,_ in enumerate(err) if _]
            raise ParamError(params,'Invalid params {}: {}'.format(e,params))
        else:
            return 0 #Everything looks good
    if x>=c:
        return 0
    else:
        return mfTriangle(x,[a,b,d])

def mfGaussian(x,params):
    sigma,c = params
    if sigma == 0:
        #Throw invalid param exception
        pass
    t = (x-c)/sigma
    return exp(-t*t/2)

def mfGaussian2():
    pass
 
def defuzzCentroid(agg,outrange):
    a,b = outrange
    points = len(agg)
    dx = (b-a)/(points - 1)
    totarea = sum(agg)
    if totarea == 0:
#        print('Total area was zero. Using average of the range instead')
        return (a+b)/2
    totmom = 0
    for i,y in enumerate(agg):
        totmom += y*(a + i*dx)
    return totmom/totarea

class Error(Exception):
    pass

class ParamError(Error):
    def __init__(self,params,msg):
        self.params = params
        self.msg = msg
    def __str__(self):
        return repr(self.msg)