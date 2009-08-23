#!/usr/bin/env python
from liblojbansuggest import *
from pprint import pprint
from camxes import call_camxes

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

class CmavoSumti(object):
  def __init__(self, cmavo):
    self.cmavo = cmavo

  def __repr__(self):
    return self.cmavo

class SelbriSumti(object):
  def __init__(self, gadri, selbri):
    self.gadri = gadri
    self.selbri = selbri
  
  def __repr__(self):
    return `self.gadri` + " " + `self.selbri`

class Sentence(object):
  def __init__(self, selbri, sumti):
    self.selbri = selbri
    self.sumti = sumti

  def __repr__(self):
    return "Sentence with selbri {" + `self.selbri` + "} and sumti " + `self.sumti`

class Selbri(object):
  def __init__(self, selbri):
    self.selbri = selbri # TODO: come up with stuff for this class

  def __repr__(self):
    return self.selbri

def sumtiFromTerms(tree):
  sumti = []
  if tree[0] != "terms": raise MalformedTreeError("Expected terms as root node, but got " + tree[0])
  for part in tree[1:]:
    if part[0] != "sumti": raise MalformedTreeError("Expected sumti, but got " + part[0])
    if part[1][0] == "KOhA":
      sumti.append(CmavoSumti(part[1][1][0]))
    if part[1][0] == "LE":
      pprint(part)
      #sumti.append(SelbriSumti(
  return sumti

def sumtiFromBridiTail(tree):
  # we expect one terms somewhere in there.
  for tu in tree[1:]:
    if tu[0] == "terms":
      return sumtiFromTerms(tu)
  # apparently there were none.
  return []

def selbriFromBridiTail(tree):
  # we expect one selbri with or more tanruUnit -> BRIVLA -> gismu -> "gismu".
  res = []
  for sl in tree[1:]:
    if sl[0] == "selbri":
      for tu in sl[1:]:
        res.append(leafTip(tu))
  return Selbri(" ".join(res)) # this should be have a more meaningful analysis at base.

# we may get a terms and then a bridiTail.
def makeSentence(tree):
  sumti = {}
  sumtiCounter = 1
  selbri = None
  print "tree:", tree
  for part in tree[1:]:
    if part[0] not in ("bridiTail", 'terms'): continue
    if part[0] == 'terms':
      newSumti = sumtiFromTerms(part)
      for nsumti in newSumti:
        sumti[sumtiCounter] = nsumti
        sumtiCounter += 1
    elif part[0] == 'bridiTail': 
      newSumti = sumtiFromBridiTail(part)
      for nsumti in newSumti:
        sumti[sumtiCounter] = nsumti
        sumtiCounter += 1
      
      selbri = makeSelbri(part)
  return Sentence(selbri, sumti)

# we expect a text node with either one paragraphs child or
# one or more of i or ni'o and then a paragraphs child.
def makeText(tree):
  res = []
  if tree[0] != "text": raise MalformedTreeError("Expected 'text' as base node.")
  for block in tree[-1]: # ignore all the stuff up front
    if block[0] in ["I", "NIhO"]: continue # TODO: come up with a solution for nihos and is.
    if block[0] == "sentence":
      res.append(makeSentence(block))
  return res

while True:
  i = raw_input()
  ct = call_camxes(i, ["-e"])
  t = parseTree(ct)
  s = simplify(t)
  pprint(s)
  a = makeText(s)
  pprint(a)
