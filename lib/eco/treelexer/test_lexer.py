from lexer import PatternMatcher, RegexParser, RE_CHAR, RE_OR, RE_STAR, RE_PLUS

class Test_RegexParser(object):

    def setup_class(cls):
        cls.regparse = RegexParser()

    def test_simple(self):
        assert self.regparse.load("ab|cd") is True
        assert self.regparse.load("ab|(cd") is False

    def test_ast(self):
        assert self.regparse.ast("ab") == [RE_CHAR("a"), RE_CHAR("b")]
        assert self.regparse.ast("a|b") == RE_OR(RE_CHAR("a"), RE_CHAR("b"))
        assert self.regparse.ast("a*") == RE_STAR(RE_CHAR("a"))
        assert self.regparse.ast("a+") == RE_PLUS(RE_CHAR("a"))
        assert self.regparse.ast("(a)") == RE_CHAR("a")
        assert self.regparse.ast("(ab)") == [RE_CHAR("a"), RE_CHAR("b")]
        assert self.regparse.ast("(ab)*") == RE_STAR([RE_CHAR("a"), RE_CHAR("b")])

        assert self.regparse.ast("(a|b)*|c+") == RE_OR(\
                                                   RE_STAR(\
                                                     RE_OR(\
                                                       RE_CHAR("a"),
                                                       RE_CHAR("b")
                                                     )
                                                   ),
                                                   RE_PLUS(RE_CHAR("c"))
                                                 )

class Test_PatternMatcher(object):

    def setup_class(cls):
        cls.pmatch = PatternMatcher()

    def test_match_one(self):
        assert self.pmatch.match_one("a", "a") is True
        assert self.pmatch.match_one(".", "c") is True
        assert self.pmatch.match_one("x", "c") is False
        assert self.pmatch.match_one("", "c") is True
        assert self.pmatch.match_one("c", "") is False

    def test_match_more(self):
        assert self.pmatch.match("aa", "aa") is True
        assert self.pmatch.match("a.b", "axb") is True

    def test_match_question(self):
        assert self.pmatch.match("ab?", "a") is True
        assert self.pmatch.match("ab?", "ab") is True
        assert self.pmatch.match("ab?", "ac") is True # but 'c' is left over

    def test_match_star(self):
        assert self.pmatch.match("a*", "aaaaaa") is True
        assert self.pmatch.match("a*", "bbbbb") is True
        assert self.pmatch.match("ab*", "abbbbbb") is True
        assert self.pmatch.match("a*b*", "aaaaaabbbbbbbbbb") is True # but 'c' is left over
        assert self.pmatch.match(".*", "absakljsadklajd") is True # but 'c' is left over

    def test_match_plus(self):
        assert self.pmatch.match("a+", "aaaaaa") is True
        assert self.pmatch.match("a+", "bbbbb") is False
        assert self.pmatch.match("ab+", "abbbbbb") is True
        assert self.pmatch.match("a+b+", "aaaaaabbbbbbbbbb") is True # but 'c' is left over
        assert self.pmatch.match("a+b+", "bbbbbbbbbb") is False # but 'c' is left over
        assert self.pmatch.match("a+b+", "aaaaaaa") is False # but 'c' is left over

    def test_mixed(self):
        assert self.pmatch.match("a+b*c?d*", "aabbcdd") is True
        assert self.pmatch.match("a+b*c?d*", "aabbdd") is True
        assert self.pmatch.match("a+b*c?d*", "aadd") is True
        assert self.pmatch.match("a+b*c?d*", "aabb") is True
        assert self.pmatch.match("a+b*c?d*", "aa") is True
        assert self.pmatch.match("a+b*c?d*", "aac") is True
        assert self.pmatch.match("a+b*c?d*", "aacdd") is True
        assert self.pmatch.match("a+b*c?d*", "cdd") is False
        assert self.pmatch.match("a+b*c?d*", "bbcdd") is False

