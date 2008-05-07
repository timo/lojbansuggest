import subprocess
import os, sys, signal

class lojbanNode:
  def __init__(self, ltype):
    self.ltype = ltype
    self.children = []

  def test(self, fun):
    return fun(self) + sum(bla.test(fun) for bla in self.children)

  def __str__(self):
    return "%s=( %s )" % (self.ltype, " ".join(str(child) for child in self.children))

class textNode:
  def __init__(self, text):
    self.ltype = "text"
    self.text = text

  def test(self, fun):
    return fun(self)

  def __str__(self):
    return self.text

class parseTree:
  def __init__(self, pt):

    def constructNode(text):

      def bracketRange(text):
        bd = 0
        for i in range(len(text)):
          c= text[i]
          if c == "(": bd += 1
          if c == ")": 
            bd -= 1
            if bd == 0:
              return i

      text = text.strip()

      ns = []

      if "=(" in text:
        while len(text) > 0 and "=(" in text:
          # we got a lojbanNode!
          n = lojbanNode(text[:text.find("=(")])

          insideText = text[text.find("=(") + 1:]
          insideText = insideText[:bracketRange(insideText) + 1]
          insideText = insideText.strip()

          if not insideText:
            break

          n.children = constructNode(insideText[1:-1])

          remText = str(n)
          while "  " in text:
            text = text.replace("  ", " ")
          text = text[:text.find(remText)] + text[text.find(remText) + len(remText):]

          text = text.strip()

          ns.append(n)
          text = text.strip()
      else:
        # we got a textnode
        ns.append(textNode(text))

      return ns

    self.rootNode = constructNode(pt)[0]

    # make another, flat representation of the tree
    self.nodes = {}
    def sumDicts(d1, ds):
      if isinstance(ds, dict):
        ds = [ds]
      if len(ds) == 1:
        d2 = ds[0]
        for k in d2.keys():
          if k in d1:
            d1[k].extend(d2[k])
          else:
            d1[k] = d2[k]
        return d1
      else:
        return sumDicts(d1, sumDicts(ds[0], ds[1:]))

    def collectNodes(node):
      if isinstance(node, textNode):
        return {"text": [node]}
      else:
        return sumDicts({node.ltype: [node]}, [collectNodes(n) for n in node.children])

    self.nodes = collectNodes(self.rootNode)

  def __str__(self):
    return str(self.rootNode)

def find_camxes():
  return os.path.expanduser("~/lojban/lojban_peg_parser.jar")

def call_camxes(text, arguments=[]):
  camxesPath = find_camxes()
  sp = subprocess.Popen(["java", "-jar", camxesPath] + arguments,
                        stdin = subprocess.PIPE, stdout=subprocess.PIPE)
  sp.stdin.write(text)
  sp.stdin.write("\n")
  sp.stdin.close()
  a = sp.stdout.readlines()
  sp.stdout.close()
  os.kill(sp.pid, signal.SIGTERM)
  return a

class lojbantext:
  def splittext(self):
    # TODO: this must be easier
    tds = self.td.split(" ")
    def ion(ar, wo): # index or not
      try:
        return ar[1:].index(wo) + 1
      except:
        return len(ar)
    sp = lambda ar: min(ion(ar, ".i"), ion(ar, "i"), ion(ar, "ni'o"))
    sentences = []
    while len(tds) > 0:
      sentences.append(" ".join(tds[:sp(tds)]))
      tds = tds[sp(tds):]

    self.sent = sentences

  def __init__(self, textdata):
    # newlines are evil.
    self.td = textdata.replace("\n", " ")
    # 1. break up the text at i and ni'o
    self.splittext()

    # 2. seperate lu-quoted passages TODO: is this sensible?

    self.items = []

    # 3. see what can be parsed (camxes -t)
    for sent in self.sent:
      if call_camxes(sent, ["-t"])[1].strip() == sent:
        self.items.append(lojbansentence(sent))
      else:
        self.items.append(unparsabletext(sent))

    print "\n".join([str(it) for it in self.items])

class lojbansentence:
  def __init__(self, textdata):
    self.td = textdata
    # 1. run camxes to get a parse tree
    self.pt = call_camxes(textdata, ["-f"])[1].strip()

    self.pt = parseTree(self.pt)

    self.sug = []

    # 2. run checkers...
    for ch in ltcheckers:
      self.sug.extend(ch(self.td, self.pt))

    print "\n".join(str(a) for a in self.sug)

  def __str__(self):
    return "Lojbanic Sentence: %s" % self.pt

class unparsabletext:
  def __init__(self, textdata):
    self.td = textdata

    self.sug = []

    # see what broke...
    for ch in utcheckers:
      self.sug.extend(ch(self.td, self.pt))

  def __str__(self):
    return "Unparsable Text: %s" % self.td

###############################################################################
# checkers look at the text or parse tree and check for known mistakes, making
# suggestions if they are found.
# they return a list of dicts with the keys "range", "mistake" and "suggestion"
#

ltcheckers = []
utcheckers = []

def ltcheck(fun):
  ltcheckers.append(fun)
  return fun

def utcheck(fun):
  utcheckers.append(fun)
  return fun

###############################################################################
# checkers for lojban text
#

@ltcheck
def forgotCuChecker(text, pt):
  if "sentence" not in pt.nodes:
    # there is no sentence node in the parse tree. Look for a selbri that has
    # more than one brivla inside.
    selbrinode = pt.nodes['selbri3'][0]
    if selbrinode.test(lambda node: node.ltype == "BRIVLA") > 0:
      return [{"range": [0, 10],
               "mistake": "forgot cu",
               "suggestion": "There is no bridi in this sentence, but there is a tanru. Did you maybe forget to use cu to seperate a sumti from the intended selbri?"}]
  return []

###############################################################################
# checkers for unparsable text
#

#
# end of checkers
###############################################################################

def analyze(text):
  pass
  # return a list of suggestions or something?!

def main():
  text = sys.stdin.readlines()
  analyze(text)

if __name__ == "__main__":
  main()
