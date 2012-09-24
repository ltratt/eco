class State(object):

    def __init__(self, production, pos, backpointer, lookaheadsymbol=None):
        self.p = production
        self.d = pos
        self.b = backpointer
        self.k = lookaheadsymbol

    def next_symbol(self):
        try:
            return self.p.right[self.d]
        except IndexError:
            return None

    def isfinal(self):
        return len(self.p.right) == self.d

    def get_left(self):
        return self.p.left

    def get_lookahead(self):
        if self.d+1 >= len(self.p.right):
            return self.k
        return self.p.right[self.d+1].name

    def get_backpointer(self):
        return self.b

    def get_lookahead_raw(self):
        return self.get_lookahead().strip("\"")

    def clone(self):
        return State(self.p, self.d, self.b, self.k)

    def __repr__(self):
        return "State(%s, %s, %s, %s)" % (self.p, self.d, self.b, self.k)

    def __str__(self):
        """Displays the state in readable form as used in the Earley paper"""
        if not self.p.left:
            left = "None"
        else:
            left = self.p.left.name
        right = [x.name for x in self.p.right]
        right.insert(self.d, ".")
        right = "".join(right)
        s = "%s ::= %s %s %s" % (left, right, self.k, self.b)
        return s

    def equals_str(self, s):
        return self.__str__() == s

    def __eq__(self, other):
        return self.p == other.p and self.d == other.d and self.b == other.b and self.k == other.k
