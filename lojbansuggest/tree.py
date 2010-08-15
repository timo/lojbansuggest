#!/usr/bin/env python
# -*- coding=utf8 -*-
from suggest import *
from pprint import pprint
from camxes import call_camxes
import readline

# TODO: there needs to be some kind of intelligence for place structures somewhere…

class LojbansuggestError(Exception): pass
class MalformedTreeError(LojbansuggestError): pass

def leafTip(branch):
    if len(branch) > 2:
        raise MalformedTreeError("Tried to get the tip of a branch.")
    if len(branch) == 1:
        return branch[0]
    else:
        return leafTip(branch[1])

def parseTree(text):
    stack = [[]]
    for c in text.split(" "):
        if c == "": # whitespace are irrelevant
            continue
        elif c[-1] == "(": # opened a new construct
            stack[-1].append(c[:-1])
            stack.append([])
        elif c[0] == '"' and c[-1] == '"': # add a string leaf
            stack[-1].append(c[1:-1])
        elif c[0] == ")": # close a construct
            stack[-2].append(stack.pop())
            if c == "),": # append a new argument
                stack[-2].append(stack.pop())
                stack.append([])
    return stack[0]

def sameGroup(a, b, recurse = True):
    if isinstance(a, list): a = a[0]
    # check for gismu, gismu1, gismu2, ...
    if (len(a) > 1 and b.startswith(a[:-1])) or (b[-1] == "1" and b[:-1] == a) and b[-1].isalnum():
        return True
    # stack together I and IPre or IClause and IPre for example
    if b.endswith("Pre"):
        if a.startswith(b[:-3]):
            return True
    if a == "tailTerms" and b.startswith("terms"):
        return True
    if a == "statement" and b == "sentence":
        return True
    if recurse and sameGroup(b, a, False):
        return True
    if a == b: return True
    return False

simpleMap = {'tailTerms': 'terms',
             'statement': 'sentence'}
def simpleName(name):
    try: return simpleMap[name]
    except: pass
    if name[-1].isdigit():
        return name[:-1]
    if name.endswith("Clause"):
        return name[:-len("Clause")]
    return name

def simplify(part):
    # try to simplify [fooclause [cmavo [foo ['foo'] ] ] ] to [foo ['foo'] ]
    try:
        if part[1][0] == "CMAVO" and part[0].replace("h", "H").isupper() and part[0].startswith(part[1][1][0]):
            return [part[0], [part[1][1][1][0]]]
    except IndexError: pass
    # only simplify nodes that have one child only
    if len(part) > 1:
        res = []
        fadni = True
        for sp in part[1:]:
            # do not try to simplify string leafs
            if isinstance(sp[0], str):
                # only simplify nodes of the same group (like sumti with sumti1, sumti2, ...)
                if sameGroup(part[0], sp[0]):
                    if len(sp) > 1:
                        res.extend([simplify(a) for a in sp[1:]])
                        fadni = False
                        continue
            res.append(sp)
        if not fadni:
            return simplify([simpleName(part[0])] + res)
    # let's try that again with the children.
    elif len(part) == 1:
        return part
    return [part[0]] + [simplify(p) for p in part[1:]]

class SumtiPositionHint(object):
    def hookUp(self, prev):
        self.prev = prev
        return self

class NextPositionHint(SumtiPositionHint): # take the next free sumti spot
    def hookUp(self, prev):
        self.counter = prev.next()
        self.prev = prev
        return self

    def next(self):
        self.counter += 1
        return self.counter - 1

# FIXME: already filled places must be skipped (fe ti dunda fa mi do == mi ti do dunda)
class FAPositionHint(NextPositionHint): 
    def __init__(self, pos): 
        self.counter = pos # use a tagged position

    def hookUp(self, prev): return self

class BAIPositionHint(SumtiPositionHint): 
    def __init__(self, bai, pos): 
        self.bai = bai
        self.pos = pos # use a bai-tagged position
        self.exhausted = False
    
    def next(self):
        if not self.exhausted:
            self.exhausted = True
            return (self.bai, self.pos)
        else:
            return self.prev.next()

class InitialPositionHint(NextPositionHint):
    def hookUp(self, prev):
        self.counter = 1
        return self

class SamePositionHint(SumtiPositionHint):
    def hookUp(self, prev):
        return prev
 
class BEPositionHint(BAIPositionHint): pass # this is a special case of a baitag, because we can just take the bai to be the tanru element.
class COPositionHint(BEPositionHint): pass # this is an even more special case.

allSE = "jai se te ve xe".split()
def applySe(SE, nums):
    for se in SE:
        i = allSE.index(se)
        if i == 0: pass # jai comes much later.
        else:
            nums = nums[i] + nums[0:i] + nums[i + 1:]

allFA = "y fa fe fi fo fu fai".split()
def posOfFA(fa):
    return allFA.index(fa)

class Sumti(object): pass

class CmeneSumti(Sumti):
    def __init__(self, gadri, cmene):
        self.gadri = gadri
        self.cmene = cmene

    def __repr__(self):
        return "CmeneSumti(" + `self.gadri` + ", " + `self.cmene` + ")"

class CmavoSumti(Sumti):
    def __init__(self, cmavo):
        self.cmavo = cmavo

    def __repr__(self):
        return "CmavoSumti(" + `self.cmavo` + ")"

class SelbriSumti(Sumti):
    def __init__(self, gadri, selbri):
        self.gadri = gadri
        self.selbri = selbri
    
    def __repr__(self):
        return "SelbriSumti(" + `self.gadri` + ", " + `self.selbri` + ")"

class Sentence(object):
    def __init__(self, selbri, sumti):
        self.selbri = selbri
        self.sumti = sumti

    def __repr__(self):
        return "Sentence(" + `self.selbri` + ")," + `self.sumti` + ")"

class Selbri(object):
    def __init__(self, tanruUnits):
        self.tanruUnits = tanruUnits

    def __repr__(self):
        return "Selbri(" + `self.tanruUnits` + ")"

class tanruUnit(object):
    def __init__(self, brivla):
        self.brivla = brivla
    
    def __repr__(self):
        return "tanruUnit(" + `self.brivla` + ")"

class SubsentenceTanruUnit(tanruUnit):
    def __init__(self, abstractor, sentence):
        self.abstractor = abstractor
        self.sentence = sentence

    def __repr__(self):
        return "SubsentenceTanruUnit(" + `self.abstractor` + ", " + `self.sentence` + ")"

def sumtiFromTerms(tree):
    sumti = []
    hint = SamePositionHint() # use whatever came before.
    def addSumti(sum):
        sumti.append((hint, sum))
    if tree[0] != "terms": raise MalformedTreeError("Expected terms as root node, but got " + tree[0])
    for part in tree[1:]:
        if part[0] not in ("sumti", "FA", "tag"): raise MalformedTreeError("Expected sumti, FA or tag, but got " + part[0])
        if part[0] == "sumti":
            if part[1][0] == "KOhA":
                addSumti(CmavoSumti(part[1][1][0]))
            if part[1][0] == "LE":
                addSumti(SelbriSumti(part[1][1][0], makeSelbri(part[2])))
            if part[1][0] == "LA":
                if part[2][0] == "CMENE":
                    addSumti(CmeneSumti(part[1][1][0], " ".join([leafTip(l) for l in part[2:]])))
                elif part[2][0] == "selbri":
                    addSumti(CmeneSumti(part[1][1][0], [makeSelbri(part[2])]))
        elif part[0] == "FA":
            hint = FAPositionHint(posOfFA(part[1][0]))
    return sumti

def sumtiFromBridiTail(tree):
    # we expect one terms somewhere in there.
    for tu in tree[1:]:
        if tu[0] == "terms":
            return sumtiFromTerms(tu)
    # apparently there were none.
    return []

def makeTanruUnit(tree):
    fss = [sp for sp in tree[1:] if sp[0] == "subsentence"]
    if fss:
        abs = ""
        for part in tree[1:]:
            if part[0] == "SE":
                abs += part[1][0]
            elif part[0] == "NU":
                abs += part[1][0]
        return SubsentenceTanruUnit(abs, makeSentence(fss[0][1]))
    return tanruUnit(" ".join(leafTip(tp) for tp in tree[1:])) # come up with something clever for SE here as well

def makeSelbri(tree):
    # we expect one selbri with or more tanruUnit -> BRIVLA -> gismu -> "gismu".
    res = []
    if tree[0] != "selbri": raise MalformedTreeError("Expected a selbri, got a " + tree[0])
    for tu in tree[1:]:
        res.append(makeTanruUnit(tu))
    return Selbri(res) # this should be have a more meaningful analysis at base.

def selbriFromBridiTail(tree):
    if tree[0] != "bridiTail": raise MalformedTreeError("Expected a bridiTail, got a " + tree[0])
    for ch in tree[1:]:
        if ch[0] == "selbri":
            return makeSelbri(ch)
    raise MalformedTreeError("A briditail had no selbri. wtf?")

# we may get a terms and then a bridiTail.
def makeSentence(tree):
    sumti = {}
    sumtiCounter = InitialPositionHint().hookUp(None) # this is ugly :|
    selbri = None
    print "tree:", tree
    for part in tree[1:]:
        if part[0] not in ("bridiTail", 'terms'): continue
        if part[0] in ['terms', 'bridiTail']:
            if part[0] == 'terms':
                newSumti = sumtiFromTerms(part)
            elif part[0] == 'bridiTail': 
                newSumti = sumtiFromBridiTail(part)
                selbri = selbriFromBridiTail(part)
            for nsumti in newSumti:
                sumtiCounter = nsumti[0].hookUp(sumtiCounter)
                sumti[sumtiCounter.next()] = nsumti[1]
    return Sentence(selbri, sumti)

# we expect a text node with either one paragraphs child or
# one or more of i or ni'o and then a paragraphs child.
def makeText(tree):
    res = []
    if tree[0] != "text": raise MalformedTreeError("Expected 'text' as base node.")
    for block in tree[-1]: # ignore all the stuff up front
        if block[0] in ["I", "NIhO"]: continue # TODO: come up with a solution for nihos and is.
        elif block[0] == "sentence":
            res.append(makeSentence(block))
    return res

if __name__ == "__main__":
    while True:
        i = raw_input()
        ct = call_camxes(i, ["-e"])
        t = parseTree(ct)
        s = simplify(t)
        pprint(s)
        a = makeText(s)
        pprint(a)
