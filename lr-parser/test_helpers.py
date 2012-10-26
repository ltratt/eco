import sys
sys.path.append("../")

from gparser import Parser, Terminal, Nonterminal, Epsilon
from syntaxtable import FinishSymbol
from state import State, StateSet, LR1Element
from production import Production
from helpers import first, follow, closure_0, goto_0, closure_1

grammar = """
Z ::= S
S ::= S "b"
    | "b" A "a"
    | "a"
A ::= "a" S "c"
    | "a"
    | "a" S "b"

B ::= A S

C ::= D A

D ::= "d"
    |

F ::= C D "f"
"""

p = Parser(grammar)
p.parse()
r = p.rules

grammar2 = """
    E ::= P
        | E "+" P
    P ::= "a"
"""

p = Parser(grammar2)
p.parse()
r2 = p.rules

a = Terminal("a")
b = Terminal("b")
c = Terminal("c")
d = Terminal("d")
f = Terminal("f")
plus = Terminal("+")
epsilon = Epsilon()
finish = FinishSymbol()

Z = Nonterminal("Z")
S = Nonterminal("S")
A = Nonterminal("A")
B = Nonterminal("B")
C = Nonterminal("C")
D = Nonterminal("D")
F = Nonterminal("F")
E = Nonterminal("E")
P = Nonterminal("P")

def test_first():
    assert first(r, a) == set([a])
    assert first(r, b) == set([b])
    assert first(r, c) == set([c])
    assert first(r, S) == set([a, b])
    assert first(r, A) == set([a])
    assert first(r, B) == first(r, A)
    assert first(r, C) == set([d, a])
    assert first(r, D) == set([d, epsilon])
    assert first(r, F) == set([d, a])
    assert first(r, [D, A]) == set([d, a])
    assert first(r, [C, D, f]) == set([d, a])

def test_follow():
    assert follow(r, S) == set([b, c])
    assert follow(r, A) == set([a, b, d, f])
    assert follow(r, B) == set([])
    assert follow(r, C) == set([d, f])
    assert follow(r, D) == set([a, f])

def test_closure_0():
    s1 = StateSet()
    s =  State(Production(Nonterminal("Z"), [Nonterminal("S")]), 0) # first state Z ::= .S
    s1.add(s)
    closure = closure_0(r, s1)
    assert len(closure.elements) == 4
    assert State(Production(Z, [S]), 0) in closure
    assert State(Production(S, [S, b]), 0) in closure
    assert State(Production(S, [b, A, a]), 0) in closure
    assert State(Production(S, [a]), 0) in closure

    s2 = StateSet()
    s =  State(Production(F, [C, D, f]), 0)
    s2.add(s)
    closure = closure_0(r, s2)
    assert len(closure.elements) == 4
    assert State(Production(F, [C, D, f]), 0) in closure
    assert State(Production(C, [D, A]), 0) in closure
    assert State(Production(D, [d]), 0) in closure
    assert State(Production(D, [Epsilon()]), 1) in closure

    s3 = StateSet()
    s =  State(Production(C, [D, A]), 1)
    s3.add(s)
    closure = closure_0(r, s3)
    assert len(closure.elements) == 4
    assert State(Production(C, [D, A]), 1) in closure
    assert State(Production(A, [a, S, c]), 0) in closure
    assert State(Production(A, [a, S, b]), 0) in closure
    assert State(Production(A, [a]), 0) in closure

def test_goto_0():
    ss = StateSet([State(Production(Z, [S]), 0)])
    closure = closure_0(r, ss)
    g1 = goto_0(r, closure, b)
    expected = closure_0(r, StateSet([State(Production(S, [b, A, a]), 1)]))
    assert expected.elements == g1.elements
    g2 = goto_0(r, closure, a)
    assert [State(Production(S, [a]), 1)] == g2.elements

    assert goto_0(r, closure, c) == StateSet()
    assert goto_0(r, closure, d) == StateSet()
    assert goto_0(r, closure, f) == StateSet()

def test_closure_1():
    s1 = StateSet([LR1Element(Production(Z, [S]), 0, set([finish]))])
    closure = closure_1(r, s1)
    assert len(closure.elements) == 4
    assert LR1Element(Production(Z, [S]), 0, set([finish])) in closure
    assert LR1Element(Production(S, [S, b]), 0, set([b, finish])) in closure
    assert LR1Element(Production(S, [b, A, a]), 0, set([b, finish])) in closure
    assert LR1Element(Production(S, [a]), 0, set([b, finish])) in closure

    s2 = StateSet([LR1Element(Production(F, [C, D, f]), 0, set([finish]))])
    closure = closure_1(r, s2)
    assert len(closure.elements) == 4
    assert LR1Element(Production(F, [C, D, f]), 0, set([finish])) in closure
    assert LR1Element(Production(C, [D, A]), 0, set([d, f])) in closure
    assert LR1Element(Production(D, [d]), 0, set([a])) in closure
    assert LR1Element(Production(D, [epsilon]), 1, set([a])) in closure

def test_goto_1():
    lre = LR1Element(Production(Z, [S]), 0, set([finish]))
    clone = lre.clone()

    assert lre == clone

def test_closure_recursion():
    s1 = StateSet([LR1Element(Production(Z, [E]), 0, set([finish]))])

    closure = closure_1(r2, s1)
    assert len(closure.elements) == 4
    assert LR1Element(Production(Z, [E]), 0, set([finish])) in closure
    assert LR1Element(Production(E, [P]), 0, set([plus, finish])) in closure
    assert LR1Element(Production(E, [E, plus, P]), 0, set([plus, finish])) in closure
    assert LR1Element(Production(P, [a]), 0, set([plus, finish])) in closure