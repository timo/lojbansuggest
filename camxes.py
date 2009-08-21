#!/bin/env python
import os
import subprocess

def find_camxes():
  return os.path.expanduser("~/lojban/lojban_peg_parser.jar")

camxesinstances = {}

def call_camxes(text, arguments=()):
  arguments = tuple(arguments)
  if arguments in camxesinstances:
    sp = camxesinstances[arguments]
  else:
    camxesPath = find_camxes()
    sp = subprocess.Popen(["java", "-jar", camxesPath] + list(arguments),
                          stdin = subprocess.PIPE, stdout=subprocess.PIPE)
    # eat the "hello" line for each of the arguments
    for arg in arguments:
      a = sp.stdout.readline()
    camxesinstances[arguments] = sp
  sp.stdin.write(text)
  sp.stdin.write("\n")
  a = sp.stdout.readline()
  return a
