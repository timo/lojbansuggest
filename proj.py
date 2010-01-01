from socket import *
from select import *
from tree import *
from sys import stderr
from pprint import pprint
from subprocess import Popen, PIPE
from tempfile import mkstemp
from os import remove, kill
from signal import SIGTERM

num = 0

def nextNum():
    global num
    num += 1
    return str(num)

def mangleTree(tree):
    if isinstance(tree, str):
        return tree + nextNum()
    return [mangleTree(a) for a in tree]

def makeDot(tre):
    dot = "digraph {"
    for a in tre[1:]:
        dot += tre[0] + " -> " + a[0] + "\n"
        dot += makeConnections(a[0], a[1:])
    dot += "}"
    return dot

def makeConnections(head, tree, ind = "  "):
    ret = ""
    for foo in tree:
        if foo[1:]:
            ret += ind + head + " -> " + foo[0] + "\n"
            ret += "\n".join([makeConnections(foo[0], foo[1:], ind + "  ")])
        else:
            ret += ind + head + " -> " + foo[0] + "\n" + ind + "  node " + foo[0] + " [color=\"red\"]\n"
    return ret

a = socket(AF_INET, SOCK_STREAM)
a.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
a.bind(("0.0.0.0", 1234))
a.listen(10)

clients = []
tmpfiles = []

fehp = None

try:
    while True:
        (rsocks, wsocks, esocks) = select([a] + clients, [], [])
        print "wait done. socks: ", rsocks
        if a in rsocks:
            (ns, foo) = a.accept()
            ns.send("welcome. please type any lojban sentence.\n")
            clients.append(ns)
            print "accepted client ", foo
        for rs in rsocks:
            if rs is not a:
                print "gotten something:"
                text = rs.recv(1024)
                print `text`
                ct = call_camxes(text, ["-e"])
                pprint(ct)
                t = parseTree(ct)
                s = simplify(t)
                tmpimgfo, tmpimgpath = mkstemp(".png", "proj")
                print "making image"
                dotp = Popen(["dot", "-Tpng"], stdout = tmpimgfo, stdin=PIPE)
                dotp.stdin.write(makeDot(mangleTree(s)))
                dotp.stdin.close()
                print "wait"
                dotp.wait()
                print "opening"
                if fehp:
                    kill(fehp.pid, SIGTERM)
                fehp = Popen(["feh", "-FZ", tmpimgpath])
                print "showed."
                tmpfiles.append(tmpimgpath)
finally:
    print "cleaning up"
    a.close()
    for tmpfile in tmpfiles:
        remove(tmpfile)
