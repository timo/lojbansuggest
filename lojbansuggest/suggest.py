import sys
from camxes import call_camxes

def findall(string, sub, listindex, offset = 0):
    if (string.find(sub) == -1):
        return listindex
    else:
        offset = string.index(sub)+offset
        listindex.append(offset)
        string = string[(string.index(sub)+1):]
        return findall(string, sub, listindex, offset+1)

class LojbanNode:
    def __init__(self, ltype):
        self.ltype = ltype
        self.children = []
        self.parent = None

    def test(self, fun):
        return fun(self) + sum(bla.test(fun) for bla in self.children)

    def parent_test(self, fun):
        if self.parent:
            return fun(self) + self.parent.parent_test(fun)
        else:
            return fun(self)

    def __str__(self):
        return "%s=( %s )" % (self.ltype, " ".join(str(child)
                                                   for child in self.children))

class TextNode:
    def __init__(self, text):
        self.ltype = "text"
        self.text = text
        self.parent = None

    def test(self, fun):
        return fun(self)

    def parent_text(self, fun):
        if self.parent:
            return fun(self) + self.parent.parent_test(fun)
        else:
            return fun(self)

    def __str__(self):
        return self.text

class parseTree:
    def __init__(self, parse_text):

        def construct_node(text):

            def bracket_range(text):
                bracket_depth = 0
                for i in range(len(text)):
                    char = text[i]
                    if char == "(":
                        bracket_depth += 1
                    if char == ")": 
                        bracket_depth -= 1
                        if bracket_depth == 0:
                            return i

            text = text.strip()

            nodes = []

            if "=(" in text:
                while len(text) > 0 and "=(" in text:
                    # we got a LojbanNode!
                    node = LojbanNode(text[:text.find("=(")])

                    insideText = text[text.find("=(") + 1:]
                    insideText = insideText[:bracket_range(insideText) + 1]
                    insideText = insideText.strip()

                    if not insideText:
                        break

                    node.children = construct_node(insideText[1:-1])

                    for ch in node.children:
                        ch.parent = node

                    rem_text = str(node)
                    while "  " in text:
                        text = text.replace("  ", " ")
                    text = (text[:text.find(rem_text)] + 
                           text[text.find(rem_text) + len(rem_text):])

                    text = text.strip()

                    nodes.append(node)
                    text = text.strip()
            else:
                # we got a textnode
                nodes.append(TextNode(text))

            return nodes

        self.root_node = construct_node(parse_text)[0]

        # make another, flat representation of the tree
        self.nodes = {}
        def sum_dicts(d1, ds):
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
                return sum_dicts(d1, sum_dicts(ds[0], ds[1:]))

        def collect_nodes(node):
            if isinstance(node, TextNode):
                return {"text": [node]}
            else:
                return sum_dicts({node.ltype: [node]},
                                [collect_nodes(n) for n in node.children])

        self.nodes = collect_nodes(self.root_node)

    def __str__(self):
        return str(self.root_node)

class LojbanText:
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
            if call_camxes(sent, ["-t"]).strip() == sent.strip():
                self.items.append(LojbanSentence(sent))
            else:
                self.items.append(UnparsableText(sent))

        print "\n".join([str(it) for it in self.items])

class LojbanSentence:
    def __init__(self, textdata):
        self.textdata = textdata
        # 1. run camxes to get a parse tree
        self.part = call_camxes(textdata, ["-f"]).strip()

        self.part = parseTree(self.part)

        self.sug = []

        # 2. run checkers...
        for checker in LT_CHECKERS:
            self.sug.extend(checker(self.textdata, self.part))

        print "\n".join(str(a) for a in self.sug)

    def __str__(self):
        return "Lojbanic Sentence: %s" % self.part

class UnparsableText:
    def __init__(self, textdata):
        self.textdata = textdata

        self.sug = []

        # see what broke...
        for checker in UT_CHECKERS:
            self.sug.extend(checker(self.textdata))

        print "\n".join(str(a) for a in self.sug)

    def __str__(self):
        return "Unparsable Text: %s" % self.textdata

###############################################################################
# checkers look at the text or parse tree and check for known mistakes, making
# suggestions if they are found.
# they return a list of dicts with the keys "range", "mistake" and "suggestion"
#

LT_CHECKERS = []
UT_CHECKERS = []

def ltcheck(fun):
    LT_CHECKERS.append(fun)
    return fun

def utcheck(fun):
    UT_CHECKERS.append(fun)
    return fun

###############################################################################
# checkers for lojban text
#

@ltcheck
def forgot_cu_checker(text, pt):
    if "sentence" not in pt.nodes:
        # there is no sentence node in the parse tree. Look for a selbri that
        # has more than one brivla inside.

        # only look if there's a selbri, sentences with only
        # vocatives for example are valid, too
        if "selbri3" in pt.nodes:
            selbrinode = pt.nodes['selbri3'][0]
            if selbrinode.test(lambda node: node.ltype == "BRIVLA") > 0:
                return [{"range": [0, 10], # FIXME: this sucks.
                         "mistake": "forgot cu",
                         "suggestion": "There is no bridi in this sentence, "
                         "but there is a tanru. Did you maybe forget to use "
                         "cu to seperate a sumti from the intended selbri?"}]
    return []

@ltcheck
def gadriless_nu_checker(text, part):
    sug = []
    if "NU" in part.nodes:
        for nu_node in part.nodes['NU']:
            if not nu_node.parent_test(lambda node: node.ltype == "sumti6"):
                sug.append({"range": [0, 1], # FIXME: this sucks.
                            "mistake": "possibly accidental gadriless NU",
                            "suggestion": "while it's possible to build tanru "
                            "with NU elements inside, it's probable that you "
                            "forgot to put a gadri (lo usually) before "
                            "your NU."})

    return sug

@ltcheck
def dotside_cmevla_checker(text, part):
    sug = []

    if "cmene" in part.nodes:
        for cmene_node in part.nodes["cmene"]:
            cmene = cmene_node.children[0].text
            if True in [a in cmene for a in ["la", "doi"]]:
                sug.append({"range": [0, 1], # FIXME: blergh.
                            "mistake": "non-dotside incompatible cmevla",
                            "suggestion": "cmevla are not allowed to contain "
                            "la or doi. The only way to use cmevla with la and "
                            "doi inside is to be on the dot side"})

    return sug

###############################################################################
# checkers for unparsable text
#

@utcheck
def invalid_chars_checker(text):
    sug = []
    text = text.lower()
    if "h" in text:
        sug.append({"range": [text.find("h"), text.find("h") + 1],
                    "mistake": "invalid character",
                    "suggestion": "There is no h in the lojbanic alphabet! "
                    "Use the character ' instead."})
    
    if "q" in text:
        sug.append({"range": [text.find("q"), text.find("q") + 1],
                    "mistake": "invalid character",
                    "suggestion": "There is no q in the lojbanic alphabet! "
                    "Usually you can use k instead."})

    if "w" in text:
        sug.append({"range": [text.find("q"), text.find("q") + 1],
                    "mistake": "invalid character",
                    "suggestion": "There is no w in the lojbanic alphabet! "
                    "Usually you can use a diphtong with u or a v instead."})

    return sug

@utcheck
def invalid_h_placement_checker(text):
    sug = []
    hs = findall(text, "'", [])
    print hs
    for h in hs:
        if (h == 0 or h >= len(text) - 1 or
           text[h-1] not in "aeiouy" or text[h+1] not in "aeiou"):
            sug.append({"range": [h, h+1],
                        "mistake": "' in invalid position",
                        "suggestion": "The ' can only appear between vowels."})

    return sug

@utcheck
def bai_missing_gadri_checker(text):
    sug = []
    # ki'u du'u is invalid, as is 
    allbai = ("ba'i bai bau be'i ca'i cau ci'e ci'o ci'u cu'u de'i di'o do'e "
    "du'i du'o fa'e fau fi'e ga'a gau ja'e ja'i ji'e ji'o ji'u ka'a ka'i "
    "kai ki'i ki'u koi ku'u la'u le'a li'e ma'e ma'i mau me'a me'e mu'i mu'u "
    "ni'i pa'a pa'u pi'o po'i pu'a pu'e ra'a ra'i rai ri'a ri'i sau si'u ta'i "
    "tai ti'i ti'u tu'i va'o va'u zau zu'e").split()
    allgadri = [a + " " for a in "le le'e le'i lei lo lo'e lo'i loi".split()]
    
    # TODO: Find out if all those test cases are really necessary, or if they
    #             would fail for text that parses anyway (what if there are
    #             other mistakes in the sentence?
    for bai in allbai:
        if bai in text:
            allpos = findall(text, bai, [], 0)
            for pos in allpos:
                print "checking %s at %s" % (bai, pos)
                if (text[pos - 1] == " " or
                        text[pos - 2:pos] in "se te ve xe" or
                        text[pos - 4:pos].endswith("jai")):
                    if text[pos + len(bai)] == " ":
                        if not any([text[pos + len(bai):pos + len(bai) + 4].
                                    startswith(gadri) for gadri in allgadri]):
                            sug.append({"range": [pos, pos + len(bai) + 4],
                                        "mistake": "apparently used a BAI "
                                        "without a sumti",
                                        "suggestion": "add a lo or le after "
                                        "%s; BAI are sumtcita, so they need "
                                        "to be followed by a sumti." % bai})
                else:
                    print "'%s', '%s'" % (text[pos - 1], text[pos - 2:pos])
    return sug

#
# end of checkers
###############################################################################

def analyze(text):
    lto = LojbanText(text)
    return lto

    # return a list of suggestions or something?!

def main():
    text = " ".join(sys.stdin.readlines())
    lto = analyze(text)
    print "%r" % lto

print >> sys.stderr, """Available checkers:
 - for valid sentences:
   -""", "\n   - ".join(a.__name__ for a in LT_CHECKERS), """
 - for invalid sentences:
   -""", "\n   - ".join(a.__name__ for a in UT_CHECKERS)

if __name__ == "__main__":
    main()
