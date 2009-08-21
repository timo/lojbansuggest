#!/usr/bin/env python
from liblojbansuggest import *
from pprint import pprint
from camxes import call_camxes

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
  if b.startswith(a[:-1]) or (b[-1] == "1" and b[:-1] == a) and b[-1].isalnum():
    return True
  # stack together I and IPre or IClause and IPre for example
  if b.endswith("Pre"):
    if a.startswith(b[:-3]):
      return True
  if recurse and sameGroup(b, a, False):
    return True

def simplify(part):
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
      return simplify([part[0]] + res)
  # let's try that again with the children.
  elif len(part) == 1:
    return part
  return [part[0]] + [simplify(p) for p in part[1:]]

class lojbanNode(object):
  def __init__(self, typ, children):
    self.t = typ
    self.ch = children

class TreeBase:
  def __init__(self, content=[]):
    self.childs = {'list': []}
    for c in content:
      self.add(c)

  def add(self, other):
    self.childs['list'].append(other)

class Sentence(TreeBase):
  def add(self, other):
    # first lets check for the selbri,
    # it is a BRIVLA
    pass

while True:
  i = raw_input()
  ct = call_camxes(i, ["-e"])
  t = parseTree(ct)
  s = simplify(t)
  pprint(s)
