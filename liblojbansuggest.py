import subprocess
import os, sys, signal

def find_camxes():
  return os.path.expanduser("~/lojban/lojban_peg_parser.jar")

def call_camxes(text, arguments=[])
  camxesPath = find_camxes()
  sp = subprocess.Popen(["java", "-jar", camxespath] + arguments,
                        stdin = subprocess.PIPE, stdout=subprocess.PIPE)
  sp.stdin.write(text)
  sp.stdin.write("\n")
  sp.stdin.close()
  sp.stdout.readlines()
  sp.stdout.close()
  sys.kill(sp.pid, signal.SIGTERM)


class lojbantext:
  def __init__(self, textdata):
    pass

    # 1. break up the text at i and ni'o
    # 2. seperate lu-quoted passages TODO: is this sensible?
    # 3. see what can be parsed (camxes -t)
    #    
    #    if there are unparsable sentences/parts:
    #      1. TODO: figure out something sensible
    #
    #      n. remove the erroneous parts from the text
    #      n+1. continue with the rest
    #
    #    if everything is parsable:
    #      -> continue with 4.
    #
    # create a class lojbansentence for each sentence.
    # create a class unparsabletext for each unparsable text.

class lojbansentence:
  def __init__(self, textdata):
    pass

    # 1. run camxes to get a parse tree
    # 2. run checkers...

class unparsabletext:
  def __init__(self, textdata):
    pass

    # see what broke...

def analyze(text):
  pass
  # return a list of suggestions or something?!

def main():
  text = sys.stdin.readlines()
  analyze(text)

if __name__ == "__main__":
  main()
