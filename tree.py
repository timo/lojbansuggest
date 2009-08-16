#!/usr/bin/env python
from liblojbansuggest import *
from pprint import pprint

def parseTree(text):
  stack = [[]]
  for c in text.split(" "):
    if c == "":
      pass
    elif c[-1] == "(":
      stack[-1].append(c[:-1])
      stack.append([])
    elif c[0] == '"' and c[-1] == '"':
      stack[-1].append(c[1:-1])
    elif c[0] == ")":
      stack[-2].append(stack.pop())
      if c == "),":
        stack.append([])
  return stack

def sameGroup(a, b, recurse = True):
  print "same?", a, b
  if recurse and sameGroup(b, a, False):
    return True
  # check for gismu, gismu1, gismu2, ...
  if b.startswith(a[:-1]) or (b[-1] == "1" and b[:-1] == a):
    return True

def simplify(part):
  pprint(part)
  # only simplify nodes that have one child only
  if len(part) == 2:
    # do not try to simplify string leafs
    if isinstance(part[1][0], str):
      # only simplify nodes of the same group (like sumti with sumti1, sumti2, ...)
      if sameGroup(part[0][0], part[1][0]):
        return [part[0], simplify(part[1][1])]
  # let's try that again with the children.
  if len(part) == 1:
    return part
  return [part[0], simplify(part[1])]
  

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
  t = parseTree(i)
  s = simplify(t)
  print t
  print s
