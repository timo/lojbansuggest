import subprocess
import os, sys, signal
import time

def findall(string, sub, listindex, offset = 0):
  if (string.find(sub) == -1):
    return listindex
  else:
    offset = string.index(sub)+offset
    listindex.append(offset)
    string = string[(string.index(sub)+1):]
    return findall(string, sub, listindex, offset+1)

class lojbanNode:
  def __init__(self, ltype):
    self.ltype = ltype
    self.children = []
    self.parent = None

  def test(self, fun):
    return fun(self) + sum(bla.test(fun) for bla in self.children)

  def parentTest(self, fun):
    if self.parent:
      return fun(self) + self.parent.parentTest(fun)
    else:
      return fun(self)

  def __str__(self):
    return "%s=( %s )" % (self.ltype, " ".join(str(child) for child in self.children))

class textNode:
  def __init__(self, text):
    self.ltype = "text"
    self.text = text
    self.parent = None

  def test(self, fun):
    return fun(self)

  def parentText(self, fun):
    if self.parent:
      return fun(self) + self.parent.parentTest(fun)
    else:
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

          for ch in n.children:
            ch.parent = n

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
  sp.stdin.write(text)
  sp.stdin.write("\n")
  a = sp.stdout.readline()
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
      if call_camxes(sent, ["-t"]).strip() == sent:
        self.items.append(lojbansentence(sent))
      else:
        self.items.append(unparsabletext(sent))

    print "\n".join([str(it) for it in self.items])

class lojbansentence:
  def __init__(self, textdata):
    self.td = textdata
    # 1. run camxes to get a parse tree
    self.pt = call_camxes(textdata, ["-f"]).strip()

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
      self.sug.extend(ch(self.td))

    print "\n".join(str(a) for a in self.sug)

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

    # only look if there's a selbri, sentences with only vocatives for example
    # are valid, too
    if "selbri3" in pt.nodes:
      selbrinode = pt.nodes['selbri3'][0]
      if selbrinode.test(lambda node: node.ltype == "BRIVLA") > 0:
        return [{"range": [0, 10], # FIXME: this sucks.
                 "mistake": "forgot cu",
                 "suggestion": "There is no bridi in this sentence, but there is a tanru. Did you maybe forget to use cu to seperate a sumti from the intended selbri?"}]
  return []

@ltcheck
def gadrilessNuChecker(text, pt):
  sug = []
  if "NU" in pt.nodes:
    for nuNode in pt.nodes['NU']:
      if not nuNode.parentTest(lambda node: node.ltype == "sumti6"):
        sug.append({"range": [0, 1], # FIXME: this sucks.
                    "mistake": "possibly accidental gadriless NU",
                    "suggestion": "while it's possible to build tanru with NU elements inside, it's probable that you forgot to put a gadri (lo usually) before your NU."})

  return sug

@ltcheck
def dotSideCmevlaChecker(text, pt):
  sug = []

  if "cmene" in pt.nodes:
    for cmeneNode in pt.nodes["cmene"]:
      cmene = cmeneNode.children[0].text
      if True in [a in cmene for a in ["la", "doi"]]:
        sug.append({"range": [0, 1], # FIXME: blergh.
                    "mistake": "non-dotside incompatible cmevla",
                    "suggestion": "cmevla are not allowed to contain la or doi. The only way to use cmevla with la and doi inside is to be on the dot side"})

  return sug

###############################################################################
# checkers for unparsable text
#

@utcheck
def invalidCharsChecker(text):
  sug = []
  text = text.lower()
  if "h" in text:
    sug.append({"range": [text.find("h"), text.find("h") + 1],
                "mistake": "invalid character",
                "suggestion": "There is no h in the lojbanic alphabet! Use the character ' instead."})
  
  if "q" in text:
    sug.append({"range": [text.find("q"), text.find("q") + 1],
                "mistake": "invalid character",
                "suggestion": "There is no q in the lojbanic alphabet! Usually you can use k instead."})

  if "w" in text:
    sug.append({"range": [text.find("q"), text.find("q") + 1],
                "mistake": "invalid character",
                "suggestion": "There is no w in the lojbanic alphabet! Usually you can use a diphtong with u or a v instead."})

  return sug

@utcheck
def invalidHPlacementChecker(text):
  sug = []
  hs = findall(text, "'", [])
  print hs
  for h in hs:
    if h == 0 or text[h-1] not in "aeiouy" or text[h+1] not in "aeiou":
      sug.append({"range": [h, h+1],
                  "mistake": "' in invalid position",
                  "suggestion": "The ' can only appear between vowels."})

  return sug

@utcheck
def baiMissingGadriChecker(text):
  sug = []
  # ki'u du'u is invalid, as is 
  allbai = "ba'i bai bau be'i ca'i cau ci'e ci'o ci'u cu'u de'i di'o do'e du'i du'o fa'e fau fi'e ga'a gau ja'e ja'i ji'e ji'o ji'u ka'a ka'i kai ki'i ki'u koi ku'u la'u le'a li'e ma'e ma'i mau me'a me'e mu'i mu'u ni'i pa'a pa'u pi'o po'i pu'a pu'e ra'a ra'i rai ri'a ri'i sau si'u ta'i tai ti'i ti'u tu'i va'o va'u zau zu'e".split()
  allgadri = [a + " " for a in "le le'e le'i lei lo lo'e lo'i loi".split()]
  
  # TODO: Find out if all those test cases are really necessary, or if they
  #       would fail for text that parses anyway (what if there are other 
  #       mistakes in the sentence?
  for bai in allbai:
    if bai in text:
      allpos = findall(text, bai, [], 0)
      for pos in allpos:
        print "checking %s at %s" % (bai, pos)
        if text[pos - 1] == " " or text[pos - 2:pos] in "se te ve xe" or text[pos - 4:pos].endswith("jai"):
          if text[pos + len(bai)] == " ":
            if True not in [text[pos + len(bai):pos + len(bai) + 4].startswith(gadri) for gadri in allgadri]:
              sug.append({"range": [pos, pos + len(bai) + 4],
                          "mistake": "apparently used a BAI without a sumti",
                          "suggestion": "add a lo or le after %s; BAI are sumtcita, so they need to be followed by a sumti." % bai})
        else:
          print "'%s', '%s'" % (text[pos - 1], text[pos - 2:pos])
  return sug

#
# end of checkers
###############################################################################

def analyze(text):
  pass
  # return a list of suggestions or something?!

def main():
  text = sys.stdin.readlines()
  analyze(text)

print "Available checkers:"
print " - for valid sentences:"
print "   -",
print "\n   - ".join(a.__name__ for a in ltcheckers)
print " - for invalid sentences:"
print "   -",
print "\n   - ".join(a.__name__ for a in utcheckers)

if __name__ == "__main__":
  main()
