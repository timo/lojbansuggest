#!/usr/bin/env python
# -*- coding=utf8 -*-
from pprint import pprint
from camxes import call_camxes

# TODO: there needs to be some kind of intelligence for place
#       structures somewhere…

class LojbansuggestError(Exception):
    pass
class MalformedTreeError(LojbansuggestError): 
    pass

def leaf_tip(branch):
    if len(branch) > 2:
        raise MalformedTreeError("Tried to get the tip of a branch.")
    if len(branch) == 1:
        return branch[0]
    else:
        return leaf_tip(branch[1])

def parse_tree(text):
    stack = [[]]
    for tok in text.split(" "):
        if tok == "": # whitespace are irrelevant
            continue
        elif tok[-1] == "(": # opened a new construct
            stack[-1].append(tok[:-1])
            stack.append([])
        elif tok[0] == '"' and tok[-1] == '"': # add a string leaf
            stack[-1].append(tok[1:-1])
        elif tok[0] == ")": # close a construct
            stack[-2].append(stack.pop())
            if tok == "),": # append a new argument
                stack[-2].append(stack.pop())
                stack.append([])
    return stack[0]

def same_group(one, two, recurse = True):
    if isinstance(one, list): one = one[0]
    # check for gismu, gismu1, gismu2, ...
    if ((len(one) > 1 and two.startswith(one[:-1])) or
            (one[-1] == "1" and two[:-1] == one) 
            and two[-1].isalnum()):
        return True
    # stack together I and IPre or IClause and IPre for example
    if two.endswith("Pre"):
        if one.startswith(two[:-3]):
            return True
    if one == "tailTerms" and two.startswith("terms"):
        return True
    if one == "statement" and two == "sentence":
        return True
    if recurse and same_group(two, one, False):
        return True
    if one == two: return True
    return False

SIMPLE_MAP = {'tailTerms': 'terms',
             'statement': 'sentence'}
def simple_name(name):
    try: return SIMPLE_MAP[name]
    except: pass
    if name[-1].isdigit():
        return name[:-1]
    if name.endswith("Clause"):
        return name[:-len("Clause")]
    return name

def simplify(part):
    # try to simplify [fooclause [cmavo [foo ['foo'] ] ] ] to [foo ['foo'] ]
    try:
        if (part[1][0] == "CMAVO" and
                part[0].replace("h", "H").isupper() and
                part[0].startswith(part[1][1][0])):
            return [part[0], [part[1][1][1][0]]]
    except IndexError: pass
    # only simplify nodes that have one child only
    if len(part) > 1:
        res = []
        fadni = True
        for sp in part[1:]:
            # do not try to simplify string leafs
            if isinstance(sp[0], str):
                # only simplify nodes of the same group 
                # (like sumti with sumti1, sumti2, ...)
                if same_group(part[0], sp[0]):
                    if len(sp) > 1:
                        res.extend([simplify(a) for a in sp[1:]])
                        fadni = False
                        continue
            res.append(sp)
        if not fadni:
            return simplify([simple_name(part[0])] + res)
    # let's try that again with the children.
    elif len(part) == 1:
        return part
    return [part[0]] + [simplify(p) for p in part[1:]]

class SumtiPositionHint(object):
    def hook_up(self, prev):
        self.prev = prev
        return self

class NextPositionHint(SumtiPositionHint): # take the next free sumti spot
    def hook_up(self, prev):
        self.counter = prev.next()
        self.prev = prev
        return self

    def next(self):
        self.counter += 1
        return self.counter - 1

# FIXME: already filled places must be skipped
#        (fe ti dunda fa mi do == mi ti do dunda)
class FAPositionHint(NextPositionHint): 
    def __init__(self, pos): 
        self.counter = pos # use a tagged position

    def hook_up(self, prev): return self

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
    def hook_up(self, prev):
        self.counter = 1
        return self

class SamePositionHint(SumtiPositionHint):
    def hook_up(self, prev):
        return prev


# this is a special case of a baitag,
# because we can just take the bai to be the tanru element.
class BEPositionHint(BAIPositionHint): pass 

# this is an even more special case.
class COPositionHint(BEPositionHint): pass

ALL_SE = "jai se te ve xe".split()
def apply_se(SE, nums):
    for se in SE:
        i = ALL_SE.index(se)
        if i == 0: pass # jai comes much later.
        else:
            nums = nums[i] + nums[0:i] + nums[i + 1:]

ALL_FA = "y fa fe fi fo fu fai".split()
def pos_of_fa(fa):
    return ALL_FA.index(fa)

class Sumti(object): pass

class CmeneSumti(Sumti):
    def __init__(self, gadri, cmene):
        self.gadri = gadri
        self.cmene = cmene

    def __repr__(self):
        return "CmeneSumti(%r, %r)" % (self.gadri, self.cmene)

class CmavoSumti(Sumti):
    def __init__(self, cmavo):
        self.cmavo = cmavo

    def __repr__(self):
        return "CmavoSumti(%r)" % self.cmavo

class SelbriSumti(Sumti):
    def __init__(self, gadri, selbri):
        self.gadri = gadri
        self.selbri = selbri
    
    def __repr__(self):
        return "SelbriSumti(%r, %r)" % (self.gadri, self.selbri)

class Sentence(object):
    def __init__(self, selbri, sumti):
        self.selbri = selbri
        self.sumti = sumti

    def __repr__(self):
        return "Sentence(%r, %r)" % (self.selbri, self.sumti)

class Selbri(object):
    def __init__(self, tanruUnits):
        self.tanruUnits = tanruUnits

    def __repr__(self):
        return "Selbri(%r)" % self.tanruUnits

class tanruUnit(object):
    def __init__(self, brivla):
        self.brivla = brivla
    
    def __repr__(self):
        return "tanruUnit(%r)" % self.brivla

class SubsentenceTanruUnit(tanruUnit):
    def __init__(self, abstractor, sentence):
        self.abstractor = abstractor
        self.sentence = sentence

    def __repr__(self):
        return ("SubsentenceTanruUnit(%r, %r)" %
                   (self.abstractor, self.sentence))

def sumti_from_terms(tree):
    sumti = []
    hint = SamePositionHint() # use whatever came before.
    def add_sumti(sum):
        sumti.append((hint, sum))
    if tree[0] != "terms": 
        raise MalformedTreeError("Expected terms as root node, "
                                 "but got " + tree[0])
    for part in tree[1:]:
        if part[0] not in ("sumti", "FA", "tag"):
            raise MalformedTreeError("Expected sumti, FA or tag, "
                                     "but got " + part[0])
        if part[0] == "sumti":
            if part[1][0] == "KOhA":
                add_sumti(CmavoSumti(part[1][1][0]))
            if part[1][0] == "LE":
                add_sumti(SelbriSumti(part[1][1][0], make_selbri(part[2])))
            if part[1][0] == "LA":
                if part[2][0] == "CMENE":
                    add_sumti(CmeneSumti(part[1][1][0],
                             " ".join([leaf_tip(l) for l in part[2:]])))
                elif part[2][0] == "selbri":
                    add_sumti(CmeneSumti(part[1][1][0], [make_selbri(part[2])]))
        elif part[0] == "FA":
            hint = FAPositionHint(pos_of_fa(part[1][0]))
    return sumti

def sumti_from_bridi_tail(tree):
    # we expect one terms somewhere in there.
    for tu in tree[1:]:
        if tu[0] == "terms":
            return sumti_from_terms(tu)
    # apparently there were none.
    return []

def make_tanru_unit(tree):
    fss = [sp for sp in tree[1:] if sp[0] == "subsentence"]
    if fss:
        abs = ""
        for part in tree[1:]:
            if part[0] == "SE":
                abs += part[1][0]
            elif part[0] == "NU":
                abs += part[1][0]
        return SubsentenceTanruUnit(abs, make_sentence(fss[0][1]))
    # come up with something clever for SE here as well
    return tanruUnit(" ".join(leaf_tip(tp) for tp in tree[1:]))

def make_selbri(tree):
    # we expect one selbri with or more tanruUnit -> BRIVLA -> gismu -> "gismu"
    res = []
    if tree[0] != "selbri": raise MalformedTreeError("Expected a selbri, "
                                                     "got a " + tree[0])
    for tu in tree[1:]:
        res.append(make_tanru_unit(tu))
    return Selbri(res) # this should be have a more meaningful analysis at base

def selbri_from_bridi_tail(tree):
    if tree[0] != "bridiTail":
        raise MalformedTreeError("Expected a bridiTail, got a " + tree[0])
    for ch in tree[1:]:
        if ch[0] == "selbri":
            return make_selbri(ch)
    raise MalformedTreeError("A briditail had no selbri. wtf?")

# we may get a terms and then a bridiTail.
def make_sentence(tree):
    sumti = {}
    sumti_counter = InitialPositionHint().hook_up(None) # this is ugly :|
    selbri = None
    print "tree:", tree
    for part in tree[1:]:
        if part[0] not in ("bridiTail", 'terms'): continue
        if part[0] in ['terms', 'bridiTail']:
            if part[0] == 'terms':
                new_sumti = sumti_from_terms(part)
            elif part[0] == 'bridiTail': 
                new_sumti = sumti_from_bridi_tail(part)
                selbri = selbri_from_bridi_tail(part)
            for nsumti in new_sumti:
                sumti_counter = nsumti[0].hook_up(sumti_counter)
                sumti[sumti_counter.next()] = nsumti[1]
    return Sentence(selbri, sumti)

# we expect a text node with either one paragraphs child or
# one or more of i or ni'o and then a paragraphs child.
def make_text(tree):
    res = []
    if tree[0] != "text": 
        raise MalformedTreeError("Expected 'text' as base node.")
    for block in tree[-1]: # ignore all the stuff up front
        if block[0] in ["I", "NIhO"]: 
            continue # TODO: come up with a solution for nihos and is.
        elif block[0] == "sentence":
            res.append(make_sentence(block))
    return res

def main():
    while True:
        inp = raw_input()
        camxestree = call_camxes(inp, ["-e"])
        tree = parse_tree(camxestree)
        simple = simplify(tree)
        pprint(simple)
        result = make_text(simple)
        pprint(result)

if __name__ == "__main__":
    main()
