# Copyright (c) 2012--2014 King's College London
# Created by the Software Development Team <http://soft-dev.org/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from grammars.grammars import lang_dict, Language
from treemanager import TreeManager
from incparser.incparser import IncParser
from inclexer.inclexer import IncrementalLexer, IncrementalLexerCF
from incparser.astree import BOS, EOS, TextNode, MultiTextNode
from grammar_parser.gparser import MagicTerminal, Terminal
from utils import KEY_UP as UP, KEY_DOWN as DOWN, KEY_LEFT as LEFT, KEY_RIGHT as RIGHT

from PyQt5 import QtCore

from . import programs

import pytest
slow = pytest.mark.slow


calc = lang_dict["Basic Calculator"]
java = lang_dict["Java"]
python = lang_dict["Python 2.7.5"]
lua = lang_dict["Lua 5.3"]
sql = lang_dict["SQL (Dummy)"]
pythonprolog = lang_dict["Python + Prolog"]
phppython = lang_dict["PHP + Python"]
pythonphp = lang_dict["Python + PHP"]
pythonhtmlsql = lang_dict["Python + HTML + SQL"]
html = lang_dict["HTML"]

class Test_Typing:

    def setup_class(cls):
        parser, lexer = calc.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, calc.name)

        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def reset(self):
        self.parser.reset()
        self.treemanager = TreeManager()
        self.treemanager.add_parser(self.parser, self.lexer, calc.name)
        self.treemanager.set_font_test(7, 17)

    def test_normaltyping(self):
        assert self.parser.last_status == False
        self.treemanager.key_normal("1")
        assert self.parser.last_status == True
        self.treemanager.key_normal("+")
        assert self.parser.last_status == False
        self.treemanager.key_normal("2")
        assert self.parser.last_status == True

    def test_cursormovement1(self):
        self.treemanager.key_home()
        assert isinstance(self.treemanager.cursor.node, BOS)
        self.treemanager.cursor_movement(RIGHT)
        assert self.treemanager.cursor.node.symbol.name == "1"
        self.treemanager.key_end()
        assert self.treemanager.cursor.node.symbol.name == "2"

    def test_normaltyping2(self):
        self.treemanager.key_normal("\r")
        assert self.treemanager.cursor.node.symbol.name == "\r"
        self.treemanager.key_normal("3")
        assert self.treemanager.cursor.node.symbol.name == "3"
        self.treemanager.key_normal("+")
        assert self.treemanager.cursor.node.symbol.name == "+"
        self.treemanager.key_normal("5")
        assert self.treemanager.cursor.node.symbol.name == "5"

    def test_cursormovement2(self):
        assert self.treemanager.cursor.node.symbol.name == "5"
        self.treemanager.key_end()
        assert self.treemanager.cursor.node.symbol.name == "5"
        self.treemanager.cursor_movement(UP)
        assert self.treemanager.cursor.node.symbol.name == "2"
        self.treemanager.cursor_movement(LEFT)
        assert self.treemanager.cursor.node.symbol.name == "+"
        self.treemanager.cursor_movement(DOWN)
        assert self.treemanager.cursor.node.symbol.name == "+"

    def test_deletion(self):
        import pytest
        self.treemanager.key_end()
        assert self.treemanager.cursor.node.symbol.name == "5"
        self.treemanager.key_backspace()
        assert self.treemanager.cursor.node.symbol.name == "+"
        self.treemanager.key_delete()
        assert self.treemanager.cursor.node.symbol.name == "+"
        self.treemanager.cursor_movement(LEFT)
        self.treemanager.key_delete()
        assert self.treemanager.cursor.node.symbol.name == "3"

    def test_cursor_reset(self):
        self.treemanager.cursor_reset()
        assert isinstance(self.treemanager.cursor.node, BOS)

    def test_delete_selection(self):
        self.reset()
        self.treemanager.key_normal("a")
        self.treemanager.key_shift()
        self.treemanager.key_cursors(LEFT, shift=True)
        assert self.treemanager.hasSelection()
        nodes, _, _ = self.treemanager.get_nodes_from_selection()
        self.treemanager.key_delete()

    def test_paste(self):
        self.reset()
        assert self.parser.last_status == False
        self.treemanager.pasteText("1 + 2\r+4+5\r+6+789")
        assert self.parser.last_status == True
        assert self.treemanager.cursor.node.symbol.name == "789"
        assert self.treemanager.cursor.pos == 3

    def test_colon_colon_equals(self):
        # typing colon colon equals makes the cursor disappear
        grammar = Language("grammar with colon",
"""
S ::= "a" "assign" "b"
""",
"""
"a":a
"b":b
"::=":assign
":":colon
"=":equal
""")
        names = ["a","b","assign", "colon", "equal"]
        regex = ["a", "b", "::=", ":", "="]
        lexer = IncrementalLexerCF()
        lexer.from_name_and_regex(names, regex)
        parser = IncParser(grammar.grammar, 1, True)
        parser.init_ast()
        ast = parser.previous_version
        treemanager = TreeManager()
        treemanager.add_parser(parser, lexer, grammar.name)
        treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

        treemanager.key_normal(":")
        assert treemanager.cursor.node.lookup == "colon"
        assert treemanager.cursor.node.symbol.name == ":"
        assert treemanager.cursor.node.lookahead == 1

        treemanager.key_normal(":")
        assert treemanager.cursor.node.lookup == "colon"
        assert treemanager.cursor.node.symbol.name == ":"
        assert treemanager.cursor.node.lookahead == 1

        treemanager.key_normal("=")

        assert treemanager.cursor.node.lookup == "assign"
        assert treemanager.cursor.node.symbol.name == "::="

    def test_fix_cursor_bug(self):
        grammar = Language("bug",
"""
S ::= "brack" "htm"
    | "html"
""",
"""
"<":brack
"htm":htm
"<html":html
""")
        names = ["html","htm","brack"]
        regex = ["<html", "htm", "<",]
        lexer = IncrementalLexerCF()
        lexer.from_name_and_regex(names, regex)
        parser = IncParser(grammar.grammar, 1, True)
        parser.init_ast()
        ast = parser.previous_version
        treemanager = TreeManager()
        treemanager.add_parser(parser, lexer, grammar.name)
        treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

        treemanager.key_normal("<")
        assert treemanager.cursor.node.symbol.name == "<"
        assert treemanager.cursor.node.lookahead == 1
        treemanager.key_normal("h")
        treemanager.key_normal("t")
        treemanager.key_normal("m")
        assert treemanager.cursor.node.symbol.name == "htm"
        treemanager.key_normal("l")
        assert treemanager.cursor.node.symbol.name == "<html"
        treemanager.key_backspace()
        assert treemanager.cursor.node.symbol.name == "htm"

from grammars.grammars import EcoFile
class Test_General:

    def test_undo_bug(self):
        # Sometimes grammar changes can change subtrees that haven't been marked
        # as changed. As a consequence they are not marked with a version and
        # won't be reverted during an undo. This tests the fix in
        # incparser:reduce that version marks nodes whose parent has changed
        # during reparsing.
        grm = EcoFile("Undotest", "test/undobug1.eco", "Undo")
        t = TreeManager()
        parser, lexer = grm.load()
        t.add_parser(parser, lexer, python.name)

        t.key_normal("a")
        t.undo_snapshot()
        t.key_normal("b")
        t.undo_snapshot()
        t.key_normal("c")
        t.undo_snapshot()
        assert parser.last_status == True

        c = t.cursor.node
        assert c.symbol.name == "c"
        cp = c.parent

        t.key_cursors(LEFT)
        t.key_cursors(LEFT)
        t.key_normal("x")
        t.undo_snapshot()
        assert parser.last_status == True
        assert c.parent is not cp

        t.key_ctrl_z()
        assert parser.last_status == True

        assert c.parent is cp

    def test_load_file_with_error(self):
        t = TreeManager()

        from jsonmanager import JsonManager
        manager = JsonManager()
        language_boxes = manager.load("test/calcerror.eco")

        t.load_file(language_boxes)
        parser = t.get_mainparser()

        t.key_home()
        t.key_cursors(RIGHT)
        t.key_cursors(RIGHT)
        t.key_delete()
        assert parser.last_status is False

        t.key_cursors(RIGHT)
        t.key_cursors(RIGHT)
        t.key_delete()
        assert parser.last_status is True

    def test_lexing_save_load_bug(self):
        t = TreeManager()

        from jsonmanager import JsonManager
        manager = JsonManager()
        language_boxes = manager.load("test/range_lex_bug.eco")

        t.load_file(language_boxes)
        parser = t.get_mainparser()

        t.key_home()
        t.key_cursors(RIGHT)
        t.key_cursors(RIGHT)
        t.key_cursors(RIGHT)
        t.key_cursors(RIGHT)
        t.key_cursors(RIGHT)
        assert t.cursor.node.symbol.name == "range"
        t.key_delete()
        assert t.cursor.node.symbol.name == "rangex"

class Test_Helper:

    def reset(self):
        self.parser.reset()
        self.treemanager = TreeManager()
        self.treemanager.add_parser(self.parser, self.lexer, python.name)
        self.treemanager.set_font_test(7, 17)

    def view(self):
        import pgviewer
        pgviewer.debug(self.treemanager)

    def move(self, direction, times):
        for i in range(times): self.treemanager.cursor_movement(direction)

    def tree_compare(self, node1, node2):
        # XXX: test references (next_term, parent, lookup)
        while True:
            assert node1.symbol == node2.symbol
            if node1.right:
                assert node1.right.symbol == node2.right.symbol
            if node1.next_term:
                assert node1.next_term.symbol == node2.next_term.symbol
            if isinstance(node1.symbol, MagicTerminal):
                self.tree_compare(node1.symbol.ast, node2.symbol.ast)
            if isinstance(node1, EOS) and isinstance(node2, EOS):
                break
            node1 = self.next_node(node1)
            node2 = self.next_node(node2)

    def next_node(self, node):
        if node.children:
            return node.children[0]
        while(node.right_sibling() is None):
            node = node.parent
        return node.right_sibling()

class Test_Compare(Test_Helper):

    def test_compare(self):
        t = TreeManager()
        parser, lexer = python.load()
        t.add_parser(parser, lexer, python.name)
        inputstring = "class Test:\r    def x():\r        pass\r"
        t.import_file(inputstring)
        self.tree_compare(parser.previous_version.parent, parser.previous_version.parent)

    def test_compare2(self):
        t1 = TreeManager()
        parser1, lexer1 = python.load()
        t1.add_parser(parser1, lexer1, python.name)
        inputstring = "class Test:\r    def x():\r        pass\r"
        t1.import_file(inputstring)

        t2 = TreeManager()
        parser2, lexer2 = python.load()
        t2.add_parser(parser2, lexer2, python.name)
        inputstring = "class Test:\r    def x():\r        pass\r"
        t2.import_file(inputstring)

        self.tree_compare(parser1.previous_version.parent, parser2.previous_version.parent)

    def test_compare3(self):
        t1 = TreeManager()
        parser1, lexer1 = python.load()
        t1.add_parser(parser1, lexer1, python.name)
        inputstring = "class Test:\r    def x():\r    pass\r"
        t1.import_file(inputstring)

        t2 = TreeManager()
        parser2, lexer2 = python.load()
        t2.add_parser(parser2, lexer2, python.name)
        inputstring = "class Test:\r    def y():\r    pass\r"
        t2.import_file(inputstring)

        with pytest.raises(AssertionError):
            self.tree_compare(parser1.previous_version.parent, parser2.previous_version.parent)

class Test_Python(Test_Helper):
    def setup_class(cls):
        parser, lexer = python.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, python.name)

        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

class Test_Boogie(Test_Python):
    def test_simple(self):
        for c in "class X:\r    p":
            self.treemanager.key_normal(c)

class Test_Bugs(Test_Python):

    def test_bug_goto(self):
        inputstring = "class Test:\r    def x():\r    pass\r"
        for c in inputstring:
            self.treemanager.key_normal(c)
        for i in range(4): self.treemanager.key_backspace() # remove whitespace (unindent)
        inputstring = "def y():"
        for c in inputstring:
            self.treemanager.key_normal(c)
        assert self.treemanager.cursor.node.symbol.name == ":"
        for i in range(8):
            self.treemanager.key_backspace() # shouldn't throw AssertionError goto != None

    def test_bug_goto2(self):
        self.reset()
        inputstring = "class Test:\r    def x():\r    print()\r"
        for c in inputstring:
            self.treemanager.key_normal(c)
        inputstring = "br"
        for c in inputstring:
            self.treemanager.key_normal(c)
        assert self.treemanager.cursor.node.symbol.name == "br"
        self.treemanager.key_backspace()
        self.treemanager.key_backspace() # shouldn't throw AssertionError goto != None

    def test_last_line_nonlogical(self):
        self.reset()
        inputstring = "class Test:\r    pass"
        for c in inputstring:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True
        self.treemanager.key_normal("\r")
        assert self.parser.last_status == True
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_type_and_remove(self):
        self.reset()
        self.treemanager.key_normal("c")
        self.treemanager.key_backspace() # shouldn't throw IndexError in repair_indentations

    def test_delete_all(self):
        self.reset()
        source = "x = 1"
        for c in source:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True
        for c in source:
            self.treemanager.key_backspace()
        assert self.parser.last_status == True
        for c in source:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

    def test_select_and_paste(self):
        self.reset()
        source = "pass"
        for c in source:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

        self.treemanager.key_end()
        self.treemanager.key_shift()
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.pasteText("back")
        assert self.treemanager.export_as_text() == "back"

        self.treemanager.key_home()
        self.treemanager.key_shift()
        self.treemanager.key_cursors(RIGHT, True)
        self.treemanager.key_cursors(RIGHT, True)
        self.treemanager.key_cursors(RIGHT, True)
        self.treemanager.key_cursors(RIGHT, True)
        self.treemanager.pasteText("again")
        assert self.treemanager.export_as_text() == "again"

        self.move(LEFT, 2)
        self.treemanager.doubleclick_select()
        self.treemanager.pasteText("test")
        assert self.treemanager.export_as_text() == "test"

class Test_Indentation(Test_Python):

    def test_indentation(self):
        assert self.parser.last_status == True
        inputstring = "class Test:\r    def x():\r    return x"
        for c in inputstring:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

        self.treemanager.key_normal("\r")
        assert self.treemanager.cursor.node.symbol.name == "        "
        self.treemanager.key_backspace() # beware of auto indent
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        inputstring = "def y():\r    pass"
        for c in inputstring:
            self.treemanager.key_normal(c)

        assert self.parser.last_status == True

    def test_indentation_tokens(self):
        def check_next_nodes(node, l):
            for name in l:
                node = node.next_term
                assert node.symbol.name == name

        assert self.treemanager.lines[0].node.next_term.symbol.name == "class"

        node = self.treemanager.lines[1].node
        check_next_nodes(node, ["NEWLINE", "INDENT", "    ", "def"])

        node = self.treemanager.lines[2].node
        check_next_nodes(node, ["NEWLINE", "INDENT", "        ", "return"])

        node = self.treemanager.lines[3].node
        check_next_nodes(node, ["NEWLINE", "DEDENT", "    ", "def"])

        node = self.treemanager.lines[4].node
        check_next_nodes(node, ["NEWLINE", "INDENT", "        ", "pass", "NEWLINE", "DEDENT", "DEDENT", "eos"])

    def test_unexpected_indentation_after_bos(self):
        self.reset()
        inputstring = """test"""
        for i in inputstring:
            self.treemanager.key_normal(i)

        assert self.parser.last_status == True
        self.treemanager.key_home()
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == False
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_indentation_last_line(self):
        # change last line from unlogical to logical
        # dedents are now being created after \r not before eos
        self.reset()
        inputstring = """if x:
    x
"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        self.move(DOWN, 2)
        self.treemanager.key_normal("z")
        assert self.parser.last_status == True

    def test_indentation2(self):
        self.reset()
        assert self.parser.last_status == True
        inputstring = """class Test:
    def x():
        return x
    def y():
        execute_something()
        for i in range(10):
            x = x + 1
            if x > 10:
                print("message")
                break
    def z():
        pass"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        assert isinstance(self.treemanager.cursor.node, BOS)

        # move cursor to 'break'
        self.move(DOWN, 9)
        self.move(RIGHT, 16)

        assert self.treemanager.cursor.node.symbol.name == "                "
        assert self.treemanager.cursor.node.next_term.symbol.name == "break"

        # add space
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == False
        # undo
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

        # dedent 'break' 2 times
        # dedent 4 spaces
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        assert self.parser.last_status == False
        self.treemanager.key_backspace()
        assert self.parser.last_status == True
        # dedent 4 spaces
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        assert self.parser.last_status == False
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_indentation3(self):
        self.reset()
        assert self.parser.last_status == True
        inputstring = """class Test:
    def x():
        return x
    def y():
        for i in range(10):
            x = x + 1
            if x > 10:
                print("message")
    def z():
        pass"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        assert isinstance(self.treemanager.cursor.node, BOS)

        # move cursor to 'break'
        self.move(DOWN, 4)
        self.move(RIGHT, 8)

        # indent 'for' and 'x = x + 1'
        assert self.treemanager.cursor.node.next_term.symbol.name == "for"
        for i in range(4): self.treemanager.key_normal(" ")
        assert self.parser.last_status == False
        self.move(DOWN, 1)
        assert self.treemanager.cursor.node.next_term.symbol.name == "x"
        for i in range(4): self.treemanager.key_normal(" ")
        assert self.parser.last_status == True

    def test_indentation4(self):
        self.reset()
        assert self.parser.last_status == True
        inputstring = """class Test:
    def x():
        x = 1
        return x
    def y():
        y = 2
        return y
    def z():
        z = 3
        return z"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        assert isinstance(self.treemanager.cursor.node, BOS)

        # move cursor to 'break'
        self.move(DOWN, 4)
        self.move(RIGHT, 4)

        # indent 'def y', 'y = 2' and 'return y'
        assert self.treemanager.cursor.node.next_term.symbol.name == "def"
        for i in range(4): self.treemanager.key_normal(" ")
        assert self.parser.last_status == False
        self.move(DOWN, 1)
        assert self.treemanager.cursor.node.next_term.symbol.name == "y"
        for i in range(4): self.treemanager.key_normal(" ")
        assert self.parser.last_status == True
        self.move(DOWN, 1)
        self.move(LEFT, 4)
        assert self.treemanager.cursor.node.next_term.symbol.name == "return"
        for i in range(4): self.treemanager.key_normal(" ")
        assert self.parser.last_status == True

    @slow
    def test_indentation_stresstest(self):
        import random
        self.reset()

        self.treemanager.import_file(programs.connect4)
        assert self.parser.last_status == True

        deleted = {}
        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)
        for linenr in random_lines:
            whitespace = self.treemanager.get_indentation(linenr)
            if whitespace:
                del_ws = random.randint(0, whitespace)
                if del_ws > 0:
                    self.treemanager.cursor_reset()
                    print("self.treemanager.cursor_reset()")
                    print("self.move(DOWN, %s)" % linenr)
                    print("self.move(RIGHT, %s)" % del_ws)
                    self.move(DOWN, linenr)
                    self.move(RIGHT, del_ws)
                    assert self.treemanager.cursor.node.symbol.name == " " * whitespace
                    for i in range(del_ws):
                        print("self.treemanager.key_backspace()")
                        self.treemanager.key_backspace()
                    deleted[linenr] = del_ws
        assert self.parser.last_status == False

        # undo
        for linenr in deleted:
            del_ws = deleted[linenr]
            print("self.treemanager.cursor_reset()")
            self.treemanager.cursor_reset()
            print("self.move(DOWN, %s)" % linenr)
            self.move(DOWN, linenr)
            for i in range(del_ws):
                self.treemanager.key_normal(" ")
        assert self.parser.last_status == True

    def test_indentation_stresstest_bug(self):
        self.reset()
        self.treemanager.import_file(programs.connect4)
        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        self.move(RIGHT, 7)
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 8)
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()

        # undo
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        # shouldn't cause AttributeError: 'NoneType' object has no attribute 'relex'
        self.treemanager.key_normal(" ")

    def test_indentation_stresstest_bug_short(self):
        self.reset()
        self.treemanager.import_file("""class Connect4():
    def __init__():
       pass1
       pass2
       pass3

    def _set_status_text():
       pass4""")
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()

    def test_indentation_stresstest_bug2_indentation(self):
        self.reset()
        s = """class Connect4(object):
    UI_DEPTH = 5

    def __init__(self):
        x
        y

        z"""
        self.treemanager.import_file(s)
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 7)
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.treemanager.key_normal(' ')
        self.treemanager.key_normal(' ')
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.treemanager.key_normal(' ')
        self.treemanager.key_normal(' ')
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.treemanager.key_normal(' ')

    def test_indentation_stresstest_bug3(self):
        self.reset()
        connect4 = """class Connect4():

    def _update_from_pos_one_colour():
        assert colour in x

        for c in pylist:
            a"""
        self.treemanager.import_file(connect4)

        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 15)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 10)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 13)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 4)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 12)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 5)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 17)
        self.treemanager.key_delete()

    def test_indentation_stresstest_bug_retain(self):
        # In the `pass1` method `textlength` needs to check the yield of the
        # previous version of the program. Wagner's thesis uses the current
        # version, which is limited by the error and thus can never have a
        # greater yield than the location of error
        self.reset()

        prog = """class Connect4(object):

    def __init__():
        top

        # comment
        turn

        for colno in cols:
            grid
            append1
            append2

        grid2
        grid3

    def _turn():
            if ai:
                break
            pass"""

        self.treemanager.import_file(prog)
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 4)
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 1)
        self.treemanager.key_backspace()
        self.treemanager.cursor_reset()
        self.move(DOWN, 17)
        self.move(RIGHT, 11)
        self.treemanager.key_backspace()
        # This is the part where the bug is introduced, leading to an
        # error later on
        self.treemanager.cursor_reset()
        self.move(DOWN, 14)
        self.move(RIGHT, 2)
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.cursor_reset()
        self.move(DOWN, 18)
        self.move(RIGHT, 7)
        self.treemanager.key_backspace()

    def test_indentation_stresstest_bug_retain2(self):
        # When retaining a subtree we need to enforce `mark_changed` on it to
        # make sure the retained changes are being saved once parsing is
        # complete
        self.reset()
        prog = """class Connect4():

    def __init__():
        pass1
        pass2
        pass3
        pass4"""
        self.treemanager.import_file(prog)
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('(')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('!')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 4)
        self.treemanager.key_normal('4')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('%')

    def test_single_statement(self):
        self.reset()
        assert self.parser.last_status == True
        inputstring = """x = 12"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True

    def test_line_becomes_first_line(self):
        self.reset()
        assert self.parser.last_status == True
        inputstring = """class X:\r    pass"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True

        for i in range(13):
            self.treemanager.key_delete()

        assert self.parser.last_status == True

    def test_not_logical_lines(self):
        self.reset()
        inputstring = """class X(object):\r    def test():\r        return asd\r        \r    def relex(self, startnode):\r        pass"""

        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True

    def test_paste(self):
        self.reset()
        inputstring = """class X(object):\r    pass1\rx"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        self.treemanager.key_end()
        assert self.treemanager.cursor.node.symbol.name == ":"
        self.treemanager.key_normal("\r")
        assert self.treemanager.cursor.node.symbol.name == "\r"
        self.treemanager.pasteText("""    if a:
        pass2
    pass3
if b:
    if c:
        pass4""")
        assert self.treemanager.cursor.node.symbol.name == "pass4"
        assert self.parser.last_status == True

    def test_bug(self):
        self.reset()
        inputstring = """class X(object):\rpass"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == False
        self.treemanager.cursor_movement(DOWN)
        self.treemanager.key_home()
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == True

    def test_bug2(self):
        self.reset()
        inputstring = """a = 3
while True:
    a = 4"""
        for c in inputstring:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True
        self.treemanager.key_normal("\r")
        self.treemanager.key_normal("x")
        assert self.parser.last_status == True

    def test_opt_push_last_before_eos_1(self):
        self.reset()
        inputstring = """class X:\r    def x():\r        pass\r    def y():\r        pass"""
        self.treemanager.import_file(inputstring)
        self.move(DOWN, 3)
        assert self.parser.last_status == True
        # delete whitespace before def y():
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        assert self.parser.last_status == False
        self.treemanager.key_delete()
        assert self.parser.last_status == True
        # put whitespace back in
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == False
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == True

    def test_opt_push_last_before_eos_2(self):
        self.reset()
        inputstring = """class X:\r    def x():\r        pass\rdef y():\r        pass"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        self.move(DOWN, 3)
        # insert whitespace before def y()
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == False
        self.treemanager.key_normal(" ")
        assert self.parser.last_status == True
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        assert self.parser.last_status == False
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_indentation_and_any_symbol(self):
        # when making a line unlogical, need to mark all newlines afterwards as changed
        # ??? only mark the first and last line as changed, and update the indent-attribute on all other <return>
        self.reset()
        inputstring = """def x():
    if x:
        x = \"\"\"
string
    else:
        y"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == False
        self.move(DOWN, 3)
        self.treemanager.key_end()
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        assert self.parser.last_status == True

    def test_indentation_bug(self):
        self.reset()
        inputstring = """class X:
    def x():
      pass
      def z():
        pass  
x()"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        self.move(DOWN, 1)
        self.move(RIGHT, 4)
        self.treemanager.key_normal("    ")
        assert self.parser.last_status == False
        self.treemanager.key_shift()
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_indentation_bug2(self):
        self.reset()
        inputstring = """class X:
    def y():
      if x:
        def x():
          pass
x()
"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        self.move(DOWN, 3)
        self.treemanager.key_end()
        self.treemanager.key_normal("p")
        assert self.parser.last_status == False
        self.move(DOWN, 1)
        self.move(LEFT, 4)
        self.treemanager.key_shift()
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_cursors(LEFT, True)
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_indentation_bug3(self):
        self.reset()
        inputstring = """def x():
    pass
x()
"""
        for k in inputstring:
            self.treemanager.key_normal(k)
        self.move(UP, 2)
        self.treemanager.key_home()
        assert self.parser.last_status == True
        self.treemanager.key_normal("    ")
        assert self.parser.last_status == False

    def test_indentation_multiline_bug(self):
        self.reset()
        inputstring = """class X:
    def x():
        s = 2
        pass1
    def x():
        pass2
def z():
    z"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True
        self.move(DOWN, 4)
        self.treemanager.key_end()
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        self.move(UP, 2)
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        assert self.parser.last_status == True
        # remove quotes again
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.move(DOWN, 2)
        self.treemanager.key_end()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

    def test_indentation_comment(self):
        self.reset()
        inputstring = """class X:
    # test
    pass"""
        self.treemanager.import_file(inputstring)
        assert self.parser.last_status == True

    def test_indentation_reuse(self):
        self.reset()
        for c in """class X:\n    """:
            self.treemanager.key_normal(c)

        newline = self.treemanager.cursor.node.next_term
        assert newline.symbol.name == "NEWLINE"

        self.treemanager.key_normal("p")

        newline2 = self.treemanager.cursor.node.next_term
        assert newline2.symbol.name == "NEWLINE"

        assert newline is newline2

class Test_Incremental_AST(Test_Python):

    def test_simple(self):
        self.reset()
        self.treemanager.import_file("def x():\n    pass")
        root = self.parser.previous_version.parent
        funcdef = root.children[1].children[1].children[0].children[0].children[0].children[0]
        assert funcdef.symbol.name == "funcdef"
        assert funcdef.alternate.name == "FuncDef"

    def test_reuse(self):
        self.reset()
        self.treemanager.import_file("def x():\n    pass")
        root = self.parser.previous_version.parent
        funcdef = root.children[1].children[1].children[0].children[0].children[0].children[0]
        assert funcdef.symbol.name == "funcdef"
        assert funcdef.alternate.name == "FuncDef"

        oldastnode = funcdef.alternate
        self.move(DOWN, 1)
        self.treemanager.key_end()
        self.treemanager.key_normal("2")
        newfuncdef = root.children[1].children[1].children[0].children[0].children[0].children[0]
        assert newfuncdef is funcdef
        assert newfuncdef.alternate is oldastnode

class Test_Relexing(Test_Python):

    def test_dont_stop_relexing_after_first_error(self):
        self.reset()
        inputstring = """def x():
    1

def y():
    2"""
        for c in inputstring:
            self.treemanager.key_normal(c)

        # create 1st lexing error
        self.treemanager.cursor_movement(UP)
        self.treemanager.cursor_movement(UP)
        self.treemanager.cursor_movement(UP)
        self.treemanager.key_end()
        self.treemanager.key_normal("*")
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")

        # create 2nd lexing error
        self.treemanager.cursor_movement(DOWN)
        self.treemanager.cursor_movement(DOWN)
        self.treemanager.cursor_movement(DOWN)
        self.treemanager.key_end()
        self.treemanager.key_normal("+")
        self.treemanager.key_normal("3")

        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")
        self.treemanager.key_normal("\"")

        assert type(self.treemanager.cursor.node.parent) is MultiTextNode

    def test_lexingerror_bug(self):
        self.reset()

        self.treemanager.pasteText("""def x():
    x = 1\"\"\"
    

""")
        assert self.parser.last_status is False

        self.move(UP, 3)
        self.treemanager.key_end()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()

        assert self.parser.last_status is True

    def test_newline_after_error(self):
        self.reset()

        for c in "   $x=1;\n":
            self.treemanager.key_normal(c)
        assert self.parser.last_status is False

        # Check that the node `\n   ` has been split up
        assert self.treemanager.cursor.node.symbol.name == "   "

class Test_NestedLboxWithIndentation():
    def setup_class(cls):
        parser, lexer = calc.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, calc.name)

        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def reset(self):
        self.parser.reset()
        self.treemanager = TreeManager()
        self.treemanager.add_parser(self.parser, self.lexer, calc.name)
        self.treemanager.set_font_test(7, 17)

    def test_simple(self):
        inputstring = "1+"
        for c in inputstring:
            self.treemanager.key_normal(c)
        self.treemanager.add_languagebox(lang_dict["Python 2.7.5"])
        inputstring = "def x():\r    pass"
        for c in inputstring:
            self.treemanager.key_normal(c)

        assert self.treemanager.parsers[1][2] == "Python 2.7.5"
        assert self.treemanager.parsers[1][0].last_status == True

    def test_remove_empty_lbox(self):
        # whitespace sensitive languages still contain indentation tokens when they are "empty"
        self.reset()
        self.treemanager.add_languagebox(lang_dict["Python 2.7.5"])
        self.treemanager.key_normal("a")
        self.treemanager.key_backspace()
        assert isinstance(self.treemanager.cursor.node, BOS)
        assert isinstance(self.treemanager.cursor.node.next_term, EOS)

    def test_remove_empty_lbox2(self):
        # whitespace sensitive languages still contain indentation tokens when they are "empty"
        self.reset()
        self.treemanager.add_languagebox(lang_dict["Python 2.7.5"])
        self.treemanager.key_normal("a")
        self.treemanager.key_shift()
        self.treemanager.key_cursors(LEFT, shift=True)
        self.treemanager.deleteSelection()
        assert isinstance(self.treemanager.cursor.node, BOS)
        assert isinstance(self.treemanager.cursor.node.next_term, EOS)

#from grammars.grammars import lang_dict, python_prolog
class Test_Languageboxes(Test_Python):

    def setup_class(cls):
        parser, lexer = pythonprolog.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, pythonprolog.name)

        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def test_simple(self):
        assert self.parser.last_status == True
        inputstring = "class Test:\r    def x():\r    return x"
        for c in inputstring:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True
        self.treemanager.key_backspace()
        assert self.parser.last_status == True
        self.treemanager.add_languagebox(lang_dict["Prolog"])
        assert self.parser.last_status == True
        assert self.treemanager.parsers[1][2] == "Prolog"
        assert self.treemanager.parsers[1][0].last_status == False
        self.treemanager.key_normal("x")
        assert self.treemanager.parsers[1][0].last_status == False
        self.treemanager.key_normal(".")
        assert self.treemanager.parsers[1][0].last_status == True

    def test_backspace_return_in_box(self):
        self.reset()
        inputstring = "class Test:\r    def x():\r    return x"
        for c in inputstring:
            self.treemanager.key_normal(c)
        self.treemanager.key_backspace()
        self.treemanager.add_languagebox(lang_dict["Prolog"])
        self.treemanager.key_normal("x")
        self.treemanager.key_normal("\r")
        for i in range(8):
            self.treemanager.key_backspace()

    def test_lbox_skips_newline(self):
        # when inserting a languagebox at the line beginning the next token
        # skips NEWLINE tokens. It should only skip INDENT/DEDENT
        self.reset()
        self.treemanager.key_normal("a") # needs to be valid once
        assert self.treemanager.parsers[0][0].last_status == True
        self.treemanager.key_backspace()
        self.treemanager.add_languagebox(lang_dict["Prolog"])
        self.treemanager.key_normal("a")
        self.treemanager.key_normal(".")
        self.treemanager.leave_languagebox()
        self.treemanager.key_normal(".")
        self.treemanager.key_normal("x")
        assert self.treemanager.parsers[0][0].last_status == True

    def test_delete_selection(self):
        self.reset()
        for c in "a = 1":
            self.treemanager.key_normal(c)
        self.treemanager.key_normal("\r")
        self.treemanager.add_languagebox(lang_dict["Prolog"])
        lbox = self.treemanager.cursor.node.get_root().get_magicterminal()
        assert lbox.symbol.name == "<Prolog>"
        for c in "abc def":
            self.treemanager.key_normal(c)
        self.treemanager.key_cursors(LEFT)
        # select "bc de"
        self.treemanager.key_shift()
        self.treemanager.key_cursors(LEFT, shift=True)
        self.treemanager.key_cursors(LEFT, shift=True)
        self.treemanager.key_cursors(LEFT, shift=True)
        self.treemanager.key_cursors(LEFT, shift=True)
        self.treemanager.key_cursors(LEFT, shift=True)
        self.treemanager.deleteSelection()
        assert lbox.symbol.name == "<Prolog>"

    def test_auto_indent(self):
        self.reset()
        self.treemanager.add_languagebox(lang_dict["Prolog"])
        for c in "abc:\r    def":
            self.treemanager.key_normal(c)
        self.treemanager.leave_languagebox()
        self.treemanager.key_normal("\r")
        self.treemanager.key_normal("a")
        assert self.treemanager.export_as_text() == "abc:\n    def\na"

    def test_auto_indent2(self):
        self.reset()
        self.treemanager.add_languagebox(lang_dict["Prolog"])
        for c in "abc:\r    def":
            self.treemanager.key_normal(c)
        self.treemanager.key_normal("\r")
        self.treemanager.add_languagebox(lang_dict["Python 2.7.5"])
        for c in "def x():\r        pass":
            self.treemanager.key_normal(c)
        self.treemanager.leave_languagebox()
        self.treemanager.key_normal("\r")
        self.treemanager.key_normal("a")
        assert self.treemanager.export_as_text() == "abc:\n    def\n    def x():\n        pass\n    a"

    def test_java_python_dont_lex_lboxes(self):
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    int x = 1 * 2;
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(UP)
        treemanager.key_end()

        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_backspace()

        treemanager.add_languagebox(lang_dict["Python expression"])
        treemanager.key_normal("1")

        assert treemanager.cursor.node.get_root().magic_backpointer.lookup == ""
        assert len(treemanager.parsers) == 2
        assert parser.last_status is True

class Test_Backslash(Test_Python):

    def test_parse(self):
        self.reset()

        program = """class X:\r    def x():\r        return \\\r            [1,2,3]"""

        for c in program:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

    def test_parse_fail(self):
        self.reset()

        program = """class X:\r    def x():\r        return \\ \r            [1,2,3]"""

        for c in program:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == False

    def test_parse_delete_insert(self):
        self.reset()

        program = """class X:\r    def x():\r        return \\\r            [1,2,3]"""

        for c in program:
            self.treemanager.key_normal(c)

        assert self.parser.last_status == True
        self.move(UP, 1)
        self.treemanager.key_end()
        self.treemanager.key_backspace()
        assert self.parser.last_status == False
        self.treemanager.key_normal("\\")
        assert self.parser.last_status == True

class Test_Java:
    def setup_class(cls):
        parser, lexer = java.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, java.name)

        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def reset(self):
        self.parser.reset()
        self.treemanager = TreeManager()
        self.treemanager.add_parser(self.parser, self.lexer, python.name)
        self.treemanager.set_font_test(7, 17)

    def move(self, direction, times):
        for i in range(times): self.treemanager.cursor_movement(direction)

class Test_JavaBugs(Test_Java):

    def test_incparse_optshift_bug(self):
        prog = """class Test {\r    public static void main() {\r        String y = z;\r    }\r}"""
        for c in prog:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True
        self.move(LEFT, 1)
        self.move(UP, 3)
        self.treemanager.key_end()
        self.treemanager.key_normal("\r")
        for c in "int x = 1;":
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

    def test_cursor_jumping_bug(self):
        self.reset()
        prog = "x = 1  + 2"
        for c in prog:
            self.treemanager.key_normal(c)
        self.treemanager.key_home()
        self.treemanager.key_cursors(RIGHT)
        self.treemanager.key_cursors(RIGHT)
        self.treemanager.key_cursors(RIGHT)
        self.treemanager.key_cursors(RIGHT)
        self.treemanager.key_normal("\"")
        self.treemanager.key_cursors(RIGHT)
        self.treemanager.key_cursors(RIGHT)
        self.treemanager.key_normal("\"")
        assert self.treemanager.cursor.node.symbol.name == "\"1 \""

    def test_inclexing_bug(self):
        self.reset()
        prog = """class C {
    int x = cur;
	/*
	 */
	/*
	 */
    int x = '+';
}"""
        self.treemanager.import_file(prog)
        self.move(DOWN, 1)
        self.move(RIGHT, 16)
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_backspace()
        self.treemanager.key_normal("'")

    def test_cursor_jumping_bug2(self):
        self.reset()
        prog = """class C {
int x = 1;
}"""
        self.treemanager.import_file(prog)
        self.move(DOWN, 1)
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_backspace()
        self.treemanager.add_languagebox(lang_dict["Basic Calculator"])
        self.treemanager.key_normal("1")
        self.treemanager.leave_languagebox()
        self.treemanager.key_normal(" ")
        assert self.treemanager.cursor.node.symbol.name == " "

class Test_Lua:
    def setup_class(cls):
        parser, lexer = lua.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, java.name)
        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def test_comment(self):
        prog = """--[[cmt\rcmt\ncmt]]\rx = {}"""
        for c in prog:
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

class Test_Undo(Test_Python):

    def reset(self):
        Test_Python.reset(self)
        self.treemanager.version = 1
        self.treemanager.last_saved_version = 1

    def compare(self, text):
        import tempfile
        f = tempfile.NamedTemporaryFile()
        result = self.treemanager.export_as_text("/tmp/temp.py")
        assert result == text
        f.close()

    def type_save(self, text):
        self.treemanager.key_normal(text)
        self.treemanager.undo_snapshot() # tells treemanager to save after the next operation and increase the version

    def save(self):
        self.treemanager.version += 1
        self.treemanager.save()

    def test_simple_undo_redo(self):
        self.treemanager.key_normal("1")
        self.treemanager.undo_snapshot()
        self.treemanager.key_normal("+")
        self.treemanager.undo_snapshot()
        self.treemanager.key_normal("2")
        self.compare("1+2")
        self.treemanager.key_ctrl_z()
        self.compare("1+")
        self.treemanager.key_ctrl_z()
        self.compare("1")
        self.treemanager.key_ctrl_z()
        self.compare("")

        self.treemanager.key_shift_ctrl_z()
        self.compare("1")
        self.treemanager.key_shift_ctrl_z()
        self.compare("1+")
        self.treemanager.key_shift_ctrl_z()
        self.compare("1+2")

    def test_undo_indentation(self):
        self.reset()
        self.type_save("class")
        self.type_save(" X:")
        self.type_save("\r    ")
        self.type_save("pass")
        self.compare("class X:\n    pass")

        self.treemanager.key_ctrl_z()
        self.compare("class X:\n    ")

        self.treemanager.key_ctrl_z()
        self.compare("class X:")
        # with the new indentation that NEWLINE is only added after a successful parse
        #assert self.treemanager.cursor.node.next_term.symbol.name == "NEWLINE"
        #assert isinstance(self.treemanager.cursor.node.next_term.next_term, EOS)

        self.treemanager.key_ctrl_z()
        self.compare("class")

        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.compare("class X:\n    pass")
        assert self.treemanager.cursor.node.next_term.symbol.name == "NEWLINE"
        assert self.treemanager.cursor.node.next_term.next_term.symbol.name == "DEDENT"
        assert isinstance(self.treemanager.cursor.node.next_term.next_term.next_term, EOS)

    def test_undo_and_type(self):
        self.reset()
        self.type_save("12")
        self.type_save("+")
        self.type_save("34")
        self.compare("12+34")

        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.compare("12")
        self.type_save("-56")
        self.compare("12-56")

        self.treemanager.key_shift_ctrl_z()
        self.compare("12-56")

    def test_redo_bug(self):
        self.reset()
        self.type_save("1")
        self.type_save("\r")
        self.type_save("2")
        self.move(UP, 1)
        self.compare("1\n2")
        self.type_save("\r")
        self.type_save("3")
        self.compare("1\n3\n2")

        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.compare("1")

        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.compare("1\n3\n2")

        self.move(DOWN, 1)
        self.treemanager.key_backspace()
        self.compare("1\n3\n")
        self.treemanager.key_backspace()
        self.compare("1\n3")
        self.treemanager.key_backspace()
        self.compare("1\n")
        self.treemanager.key_backspace()
        self.compare("1")

    def test_redo_bug2(self):
        self.reset()
        self.type_save("1")
        self.type_save("+")
        self.type_save("2")
        self.move(LEFT, 2)
        self.compare("1+2")
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.compare("12")

        self.treemanager.key_ctrl_z()
        self.compare("1+2")
        self.treemanager.key_ctrl_z()
        self.compare("1+")
        self.treemanager.key_ctrl_z()
        self.compare("1")

        self.treemanager.key_shift_ctrl_z()
        self.compare("1+")
        self.treemanager.key_shift_ctrl_z()
        self.compare("1+2")
        self.treemanager.key_shift_ctrl_z()
        self.compare("12")

    def test_bug_lingering_nodes(self):
        self.reset()
        p = """class X:
    def foo():
        return 23"""
        self.treemanager.import_file(p)
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("s")
        self.treemanager.undo_snapshot()
        dp = self.copy()

        self.move(DOWN, 2)
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("+")
        self.treemanager.undo_snapshot()

        self.treemanager.key_ctrl_z()

        self.text_compare("""class Xs:
    def foo():
        return 23""")
        self.tree_compare(self.parser.previous_version.parent, dp)

    def test_bug_lingering_after_redo(self):
        self.reset()

        p = """class X:
    def x():
        pass

    def y():
        pass"""

        ast = self.parser.previous_version
        self.treemanager.import_file(p)
        imp = self.copy()
        imptext = self.treemanager.export_as_text()

        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("a")
        self.treemanager.undo_snapshot()
        a = self.copy()
        atext = self.treemanager.export_as_text()

        self.move(DOWN, 1)
        self.treemanager.key_end()
        self.move(LEFT, 3)
        self.treemanager.key_normal("b")
        self.treemanager.undo_snapshot()
        b = self.copy()
        btext = self.treemanager.export_as_text()

        self.move(DOWN, 1)
        self.treemanager.key_end()
        self.treemanager.key_normal("c")
        self.treemanager.undo_snapshot()
        #c = self.copy()
        ctext = self.treemanager.export_as_text()

        self.move(DOWN, 2)
        self.treemanager.key_end()
        self.move(LEFT, 3)
        self.treemanager.key_normal("d")
        self.treemanager.undo_snapshot()
        #d = self.copy()
        dtext = self.treemanager.export_as_text()

        self.move(DOWN, 1)
        self.treemanager.key_end()
        self.treemanager.key_normal("e")
        self.treemanager.undo_snapshot()
        #e = self.copy()
        etext = self.treemanager.export_as_text()

        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()

        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()

        self.text_compare(etext)
        self.treemanager.key_ctrl_z()
        self.text_compare(dtext)
        self.treemanager.key_ctrl_z()
        self.text_compare(ctext)
        self.treemanager.key_ctrl_z()
        self.text_compare(btext)
        self.treemanager.key_ctrl_z()
        self.text_compare(atext)
        self.treemanager.key_ctrl_z()
        self.text_compare(imptext)

    def text_compare(self, original):
        original = original.replace("\r", "").split("\n")
        current = self.treemanager.export_as_text("/dev/null").replace("\r", "").split("\n")

        for i in range(len(current)):
            assert original[i] == current[i]

    def copy(self):
        import copy
        return copy.deepcopy(self.parser.previous_version.parent)

    def test_import(self):
        self.reset() # saves automatically

        self.treemanager.import_file("class X:\n    def x():\n         pass") # saves automatically
        self.move(DOWN, 2)
        self.treemanager.key_end()
        self.treemanager.key_normal("1")
        self.compare("class X:\n    def x():\n         pass1")
        self.treemanager.key_ctrl_z()
        self.compare("class X:\n    def x():\n         pass")

    def test_overflow(self):
        self.reset() # this saves the inital version as 1
        self.treemanager.import_file("class X:\n    def x():\n        pass")
        min_version = self.treemanager.version
        max_version = self.treemanager.version

        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        assert self.treemanager.version == min_version

        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        self.treemanager.key_shift_ctrl_z()
        assert self.treemanager.version == max_version

    @slow
    def test_undo_random_deletion_short(self):
        import random
        self.reset()

        program = """class Connect4(object):
    UI_DEPTH = 5 # lookahead for minimax

    def __init__(self, p1_is_ai, p2_is_ai):
        self.top = tk.Tk()
        self.top.title("Unipycation: Connect 4 GUI (Python)")

    def _set_status_text(self, text):
        self.status_text["text"] = text

    def _update_from_pos_one_colour(self, pylist, colour):
        assert colour in ["red", "yellow"]

        for c in pylist:
            assert c.name == "c"
            (x, y) = c
            self.cols[x][y]["background"] = colour"""

        self.treemanager.import_file(program)
        assert self.parser.last_status == True

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(10))
            random.shuffle(cols)
            for col in cols:
                self.treemanager.cursor_reset()
                print("self.treemanager.cursor_reset()")
                self.move(DOWN, linenr)
                print("self.move(DOWN, %s)" % linenr)
                self.move(RIGHT, col)
                print("self.move(RIGHT, %s)" % col)
                print("self.treemanager.key_delete()")
                x = self.treemanager.key_delete()
                if x == "eos":
                    continue
            self.treemanager.undo_snapshot()
            print("self.treemanager.undo_snapshot()")

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

    def test_undo_random_deletion_short_bug1(self):
        self.reset()

        program = """class Connect4(object):
    UI_DEPTH = 5 # lookahead for minimax

    def __init__(self, p1_is_ai, p2_is_ai):
        self.top = tk.Tk()
        self.top.title("Unipycation: Connect 4 GUI (Python)")

    def _set_status_text(self, text):
        self.status_text["text"] = text

    def _update_from_pos_one_colour(self, pylist, colour):
        assert colour in ["red", "yellow"]

        for c in pylist:
            assert c.name == "c"
            (x, y) = c
            self.cols[x][y]["background"] = colour"""

        self.treemanager.import_file(program)

        self.treemanager.cursor_reset()
        self.move(DOWN, 13)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.move(RIGHT, 6)
        self.treemanager.key_delete()
        self.move(RIGHT, 2)
        self.treemanager.key_delete()
        self.move(RIGHT, 1)
        self.treemanager.key_delete()
        self.move(LEFT, 3)
        self.treemanager.key_delete()
        self.move(LEFT, 1)
        self.treemanager.key_delete()
        self.move(RIGHT, 3)
        self.treemanager.key_delete()
        self.move(LEFT, 4)
        self.treemanager.key_delete()
        self.move(RIGHT, 1)
        self.treemanager.key_delete()
        self.move(LEFT, 5)
        self.treemanager.key_delete()
        self.move(RIGHT, 9)
        self.treemanager.key_delete()
        self.move(LEFT, 7)
        self.treemanager.key_delete()
        self.move(RIGHT, 4)
        self.treemanager.key_delete()

    def test_undo_random_deletion_fast(self):
        # fast fuzzy test that can be run on normal test runs
        import random
        self.reset()

        self.treemanager.import_file(programs.pythonsmall)
        assert self.parser.last_status == True

        self.text_compare(programs.pythonsmall)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(20))
            random.shuffle(cols)
            for col in cols[:5]:
                self.treemanager.cursor_reset()
                print("self.treemanager.cursor_reset()")
                self.move(DOWN, linenr)
                print("self.move(DOWN, %s)" % linenr)
                self.move(RIGHT, col)
                print("self.move(RIGHT, %s)" % col)
                print("self.treemanager.key_delete()")
                x = self.treemanager.key_delete()
                if x == "eos":
                    continue
            self.treemanager.undo_snapshot()
            print("self.treemanager.undo_snapshot()")

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.pythonsmall)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.pythonsmall)

        t1 = TreeManager()
        parser, lexer = python.load()
        parser.init_ast()
        t1.add_parser(parser, lexer, python.name)
        t1.set_font_test(7, 17)
        t1.import_file(programs.pythonsmall)

        assert self.parser.last_status == True
        assert parser.last_status == True

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    @slow
    def test_undo_random_deletion(self):
        import random
        self.reset()

        self.treemanager.import_file(programs.connect4)
        assert self.parser.last_status == True

        self.text_compare(programs.connect4)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(20))
            random.shuffle(cols)
            for col in cols:
                self.treemanager.cursor_reset()
                print("self.treemanager.cursor_reset()")
                self.move(DOWN, linenr)
                print("self.move(DOWN, %s)" % linenr)
                self.move(RIGHT, col)
                print("self.move(RIGHT, %s)" % col)
                print("self.treemanager.key_delete()")
                x = self.treemanager.key_delete()
                if x == "eos":
                    continue
            self.treemanager.undo_snapshot()
            print("self.treemanager.undo_snapshot()")

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.connect4)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.connect4)

        t1 = TreeManager()
        parser, lexer = python.load()
        parser.init_ast()
        t1.add_parser(parser, lexer, python.name)
        t1.set_font_test(7, 17)
        t1.import_file(programs.connect4)

        assert self.parser.last_status == True
        assert parser.last_status == True

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_undo_random_deletion_bug1(self):
        self.reset()

        src = """class X:
    def _end(self, winner_colour=None):
        for i in self.insert_buttons:
            i["state"] = tk.DISABLED
        """
        self.treemanager.import_file(src)
        assert self.parser.last_status == True

        self.text_compare(src)
        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 12)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 19)
        self.treemanager.key_delete()

        self.treemanager.undo_snapshot()

        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(src)

    def test_undo_random_deletion_bug2(self):
        self.reset()
        self.treemanager.import_file("""class Connect4(object):
    UI_DEPTH = 5

    def __init__():
        self.top = 1
        self.top.title()

        self.pl_engine = 2


        self.turn = None
        self.ai_players = 3

        self.cols = []
        self.insert_buttons = []

    def _set_status_text():
        self.status_text = 4""")
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 5)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 10)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 14)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 16)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 13)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 7)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 8)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 15)
        self.treemanager.key_delete() # infinite loop

    def test_undo_random_deletion_bug3(self):
        self.reset()

        program = """class Connect4():
    pass
    def __init__():
        pass
        for x in y:
            pass

            for x in y:
                pass
                pass
            pass

        pass

    def _end():
        if winner_colour:
            pass
            pass"""
        self.treemanager.import_file(program)
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 16)
        self.move(RIGHT, 8)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 15)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 2)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 16)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 1)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 13)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 10)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 7)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 9)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 2)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 8)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 3)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 5)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 6)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 2)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 1)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 7)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 5)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 3)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 4)
        self.treemanager.key_delete()

    def test_undo_random_deletion_bug3_short(self):
        self.reset()

        program = """class Connect4():
        pass
        def __init__():
            pass
            for x in y:
                pass

                for x in y:
                    pass
                    pass
                pass

            pass

        def _end():
            if winner_colour:
                pass
                pass"""
        self.treemanager.import_file(program)
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 16)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 15)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()

    def test_random_undo_deletion_bug4(self):
        # Occured during implementing retain changes

        self.reset()

        connect4 = """class X:

    def __init__():
        if x:
            for rowno in ROWS:
                a
                b
                c
            d
        e"""

        self.treemanager.import_file(connect4)

        self.treemanager.cursor_reset()
        self.move(DOWN, 6)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()

    def test_undo_random_deletion_bug5(self):
        self.reset()

        connect4 = """class Connect4:
    def __init__(self):
        pass1X

    def _update_from_pos_one_colour():
        pass2

    def _turn(self):
        while True:
            pass3X

    def _end():
        for i in buttons:
            pass4

        if winner_colour:
            pass5"""

        self.treemanager.import_file(connect4)

        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        self.move(RIGHT, 19)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_end()
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        self.move(RIGHT, 6)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 15)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()

    def test_undo_random_deletion_bug6(self):
        self.reset()

        self.treemanager.import_file("""class X:
    def helloworld():
        for x in y:
            if x:
                pass1
            else:
                pass2
        pass3

    def foo(x):
        pass4""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 1)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 1)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 6)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 5)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 9)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 2)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 5)
        self.treemanager.key_delete()

    def test_undo_random_deletion_bug7(self):
        self.reset()

        self.treemanager.import_file("""class Connect4():
    def _update_from_pos_one_colour():
        self.cols[x][y]["background"] = colour""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 19)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 18)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 17)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()

    def test_undo_random_deletion_bug8(self):
        # This is a test for a bug in the out-of-context analysis, where the
        # boundaries of the subtree being parsed were not strictly defined,
        # causing the parser to reduce and reuse nodes outside of the original
        # subtree. After the analysis failed, those reused subtrees would then
        # not be reverted causing errors with subtrees that have become detached
        # from the main parse tree.
        # This was solved by cutting off the subtree's root from its parent during
        # out-of-context analysis and reattaching is after analysis is done.

        self.reset()

        self.treemanager.import_file("""class Connect4():
    def f1():
        a
        b
        for c in d:
            e

        f

        g
        h

        for i in j:
            k

    def f2():
        while True:
            l
            if m:
                n

    def f3():
        for o in p:
            q

        if r:
            s
            t("%s wins" % winner_colour)""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 25)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_end()
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 24)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 14)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 24)
        self.move(RIGHT, 14)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 24)
        self.move(RIGHT, 26)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 24)
        self.move(RIGHT, 16)
        self.treemanager.key_delete()

    def test_undo_random_deletion_bug9(self):
        self.reset()
        self.treemanager.import_file("""class Connect4():
    UI_DEPTH = 5

    def __init__():
        self.top = tk.Tk()

        self.pl_engine = uni.Engine()""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 8)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 15)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 13)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 12)
        self.treemanager.key_delete()
        self.treemanager.key_delete()

    def get_random_key(self):
        import random
        keys = list("abcdefghijklmnopqrstuvwxyz0123456789 \r:,.[]{}()!$%^&*()_+=")
        return random.choice(keys)

    @slow
    def test_undo_random_insertion(self):
        import random
        self.reset()

        self.treemanager.import_file(programs.connect4)
        assert self.parser.last_status == True

        self.text_compare(programs.connect4)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(20))
            random.shuffle(cols)
            for col in cols:
                print("self.treemanager.cursor_reset()")
                print("self.move(DOWN, %s)" % linenr)
                print("self.move(RIGHT, %s)" % col)
                self.treemanager.cursor_reset()
                self.move(DOWN, linenr)
                self.move(RIGHT, col)
                k = self.get_random_key()
                print("self.treemanager.key_normal(%s)" % repr(k))
                x = self.treemanager.key_normal(k)
                if x == "eos":
                    continue
            print("self.treemanager.undo_snapshot()")
            self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.connect4)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.connect4)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(programs.connect4)

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_undo_random_insertion_fast(self):
        import random
        self.reset()

        self.treemanager.import_file(programs.pythonsmall)
        assert self.parser.last_status == True

        self.text_compare(programs.pythonsmall)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(10))
            random.shuffle(cols)
            for col in cols:
                print("self.treemanager.cursor_reset()")
                self.treemanager.cursor_reset()
                print("self.move(DOWN, %s)" % linenr)
                print("self.move(RIGHT, %s)" % col)
                self.move(DOWN, linenr)
                self.move(RIGHT, col)
                k = self.get_random_key()
                print("self.treemanager.key_normal('%s')" % repr(k))
                x = self.treemanager.key_normal(k)
                if x == "eos":
                    continue
            print("self.treemanager.undo_snapshot()")
            self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.pythonsmall)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.pythonsmall)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(programs.pythonsmall)

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_undo_random_insertion_fast_bug1(self):
        self.reset()

        self.treemanager.import_file(programs.pythonsmall)
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 8)
        self.treemanager.key_normal('5')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('p')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 8)
        self.treemanager.key_normal('\r')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 4)
        self.treemanager.key_normal('\r')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 7)
        self.treemanager.key_normal('.')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('9')
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('1')
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 13)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('6')
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 6)
        self.treemanager.key_normal('$')
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 1)
        self.treemanager.key_normal('j')
        self.treemanager.cursor_reset()
        self.move(DOWN, 10)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('o')
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 6)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('2')
        self.treemanager.undo_snapshot()

        for i in range(20):
            self.treemanager.key_ctrl_z()

    def test_undo_random_insertion_retain_bug(self):
        self.reset()
        self.treemanager.import_file("""class Connect4():
    UI_DEPTH = 5""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 14)
        self.treemanager.key_normal('b')
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('w')
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 5)
        self.treemanager.key_normal('^')
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 8)
        self.treemanager.key_normal('!')

    def test_undo_random_newlines(self):
        import random
        self.reset()

        p = """class X:
    def helloworld(x, y, z):
        for x in range(0, 10):
            if x == 1:
                return 1
            else:
                return 12
        return 13

    def foo(x):
        x = 1
        y = 2
        foo()
        return 12"""
        self.treemanager.import_file(p)
        assert self.parser.last_status == True

        self.text_compare(p)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines[:2]:
            cols = list(range(20))
            random.shuffle(cols)
            for col in cols[:1]: # add one newline per line
                self.treemanager.cursor_reset()
                print("self.move(DOWN, %s)" % linenr)
                print("self.move(RIGHT, %s)" % col)
                print("self.treemanager.key_normal(\"\r\")")
                self.move(DOWN, linenr)
                self.move(RIGHT, col)
                x = self.treemanager.key_normal("\r")
                if x == "eos":
                    continue
            self.treemanager.undo_snapshot()
            print("self.treemanager.undo_snapshot()")

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(p)

        self.text_compare(t1.export_as_text())

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_bug_insert_newline_2(self):
        import random
        self.reset()

        p = """class X:
    def helloworld():
        for x in y:
            if x:
                return 1
            else:
                return 12
        return 13"""
        self.treemanager.import_file(p)
        assert self.parser.last_status == True

        self.text_compare(p)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 1)
        self.treemanager.key_normal("\r")
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 6)
        self.move(RIGHT, 1)
        self.treemanager.key_normal("\r")
        self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(p)

        self.text_compare(t1.export_as_text())

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_bug_insert_newlines_3(self):
        import random
        self.reset()

        p = """class X:
    def helloworld():
        for x in range(0, 10):
            if x == 1:
                return 1
            else:
                return 12
        return 13"""
        self.treemanager.import_file(p)
        assert self.parser.last_status == True

        self.move(DOWN, 1)
        self.move(RIGHT, 3)
        self.treemanager.key_normal("\r")

        self.treemanager.undo_snapshot()
        self.move(DOWN, 5)
        self.move(RIGHT, 7)
        self.treemanager.key_normal("\r")

    def test_bug_delete(self):
        import random
        self.reset()

        p = """class X:
    def helloworld():
        for x in y:
            if x:
                return 1
            else:
                return 12
        return 13"""
        self.treemanager.import_file(p)
        assert self.parser.last_status == True

        self.text_compare(p)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 6)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 7)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 10)
        self.treemanager.key_delete()
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(p)

        self.text_compare(t1.export_as_text())

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_bug_insert_newline(self):
        self.reset()

        p = """class X:
    def helloworld(x, y, z):
        for x in range(0, 10):
            if x == 1:
                return 1
            else:
                return 12
        return 13

    def foo(x):
        x = 1
        y = 2
        foo()
        return 12"""
        self.treemanager.import_file(p)
        assert self.parser.last_status == True

        self.text_compare(p)

        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 7)
        self.move(RIGHT, 10)
        self.treemanager.key_normal("\r")
        self.treemanager.undo_snapshot()

        self.treemanager.cursor_reset()
        self.move(DOWN, 6)
        self.move(RIGHT, 0)
        self.treemanager.key_normal("\r") # this has to be \r not \n (Eco works with \r)
        self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(p)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(p)

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    @slow
    def test_undo_random_insertdelete(self):
        import random
        self.reset()
        print("self.reset()")
        #self.save()

        print("self.treemanager.import_file(programs.connect4)")
        self.treemanager.import_file(programs.connect4)
        assert self.parser.last_status == True
        #self.save()

        self.text_compare(programs.connect4)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(20))
            random.shuffle(cols)
            for col in cols:
                print("self.treemanager.cursor_reset()")
                print("self.move(%s, %s)" % (DOWN, linenr))
                print("self.move(%s, %s)" % (RIGHT, col))
                self.treemanager.cursor_reset()
                self.move(DOWN, linenr)
                self.move(RIGHT, col)
                k = self.get_random_key()
                if k in ["a", "c", "e", "g", "i", "k", "m", "1", "3", "5", "7"]:
                    # for a few characters DELETE instead of INSERT
                    print("self.treemanager.key_delete()")
                    x = self.treemanager.key_delete()
                else:
                    rk = self.get_random_key()
                    print("self.treemanager.key_normal(%s)" % rk)
                    x = self.treemanager.key_normal(rk)
                if x == "eos":
                    continue
            print("self.treemanager.undo_snapshot()")
            self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.connect4)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()
        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.connect4)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(programs.connect4)

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    @slow
    def test_undo_random_insertdeleteundo_slow(self):
        self.random_insert_delete_undo(programs.connect4)

    @slow
    def test_undo_random_insertdeleteundo(self):
        self.random_insert_delete_undo(programs.pythonsmall)

    def test_undo_random_insertdeleteundo_bug1(self):
        self.reset()

        program = """class Connect4():
    UI_DEPTH = 5

    def __init__():
        pass"""

        self.treemanager.import_file(program)
        assert self.parser.last_status == True

        self.text_compare(program)
        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 0)
        self.treemanager.key_normal(',')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 3)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 4)
        self.treemanager.key_normal(' ')
        self.treemanager.undo_snapshot()


        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

    def test_undo_random_insertdeleteundo_bug2(self):
        self.reset()

        prog = """class X:
    def hello():
        pass
        
    def foo():
        do
        something
        here"""
        self.treemanager.import_file(prog)
        assert self.parser.last_status == True

        self.text_compare(prog)
        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 0)
        self.treemanager.key_normal(' ')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 3)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.key_ctrl_z()
        self.treemanager.cursor_reset()
        self.move(DOWN, 6)
        self.move(RIGHT, 11)
        self.treemanager.key_normal('x')
        self.treemanager.undo_snapshot()

        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()
        self.text_compare(prog)

    def test_undo_random_insertdeleteundo_bug3(self):
        self.reset()

        self.treemanager.import_file("""class C:
    x = 5
""")
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 1)
        self.treemanager.key_normal('\r')
        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('\r')
        self.treemanager.cursor_reset()
        self.move(DOWN, 0)
        self.move(RIGHT, 2)
        self.treemanager.key_delete()

        assert self.parser.last_status == False

    def test_undo_random_insertdeleteundo_bug4(self):
        self.reset()

        program = """class X:
    def helloworld():
        for x in y:
            if x:
                return 1"""
        self.treemanager.import_file(program)
        assert self.parser.last_status == True

        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 1)
        self.treemanager.key_normal('c')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('(')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('b')
        self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # bug causes the 'b' to be ignored by undo
        assert self.treemanager.cursor.node.symbol.name == "bc"
        self.treemanager.key_ctrl_z()
        assert self.treemanager.cursor.node.next_term.next_term.symbol.name == "c"

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()

        self.text_compare(broken)

    def test_undo_random_insertdeleteundo_bug5(self):
        self.reset()
        program = """class X:
    def x():
        pass

    def y():
        pass2"""
        self.treemanager.import_file(program)
        assert self.parser.last_status == True
        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('&')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('!')
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.move(DOWN, 3)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('^')
        self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()

        self.text_compare(broken)

    def test_undo_random_insertdeleteundo_bug6(self):
        self.reset()
        program = """class X:
    def x():
        pass

    def y():
        pass2"""
        self.treemanager.import_file(program)
        assert self.parser.last_status == True
        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 4)
        self.treemanager.key_normal('$')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('a')
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 1)
        self.treemanager.key_normal('0')
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 1)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('2')

    def test_undo_random_insertdeleteundo_bug7_retain(self):
        self.reset()
        prog = """def __init__():
        pass1
        # controls cpu/human players
        pass2"""

        self.treemanager.import_file(prog)
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 1)
        self.treemanager.key_normal('m')
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('f')
        self.treemanager.cursor_reset()
        self.move(DOWN, 2)
        self.move(RIGHT, 1)
        self.treemanager.key_normal('=')

    def test_undo_random_insertdeleteundo_bug8(self):
        self.reset()
        self.treemanager.import_file("""class Connect4():
    UI_DEPTH = 5

    def __init__():
        self.top = tk.Tk()
        self.top.title()

        self.turn = None
        self.ai_players = 1

        pass""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 18)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 6)
        self.treemanager.key_normal('4')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 11)
        self.treemanager.key_normal(')')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 13)
        self.treemanager.key_normal('n')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('9')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('&')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('+')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 14)
        self.treemanager.key_normal('5')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 0)
        self.treemanager.key_normal(',')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('1')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 7)
        self.treemanager.key_normal('c')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 9)
        self.treemanager.key_normal('(')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 15)
        self.treemanager.key_normal('*')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 6)
        self.treemanager.key_normal('}')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 4)
        self.treemanager.key_normal('v')

    def test_undo_random_insertdeleteundo_bug8_loop(self):
        self.reset()
        self.treemanager.import_file("""class Connect4():
    UI_DEPTH = 5

    def __init__():
        self.top = tk.Tk()
        self.top.title()

        self.turn = None
        self.ai_players = 1

        pass""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 18)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 6)
        self.treemanager.key_normal('4')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 11)
        self.treemanager.key_normal(')')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 13)
        self.treemanager.key_normal('n')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('9')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 2)
        self.treemanager.key_normal('&')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('+')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 14)
        self.treemanager.key_normal('5')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 0)
        self.treemanager.key_normal(',')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 0)
        self.treemanager.key_normal('1')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 7)
        self.treemanager.key_normal('c')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 15)
        self.treemanager.key_normal('*')
        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 9)
        self.treemanager.key_normal('(')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 6)
        self.treemanager.key_normal('}')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 4)
        self.treemanager.key_normal('v')

    def test_undo_random_insertdeleteundo_bug9(self):
        """This test fails if the retainablity check doesn't include a same_pos
        check as described by Wagner. The node `(` which pre-parse is a child of
        `atom` is moved outside of (and before) `atom` during the parse. Then
        error recovery happens and `atom` is checked for retainablity, but now
        it does not contain `(` but instead has gained a newline. This means the
        textlength-check succeeds, but it's position has changed due to `(` now
        being before `atom`. So the retain check must fail."""
        self.reset()
        self.treemanager.import_file("""class Connect4():
    def __init__():
        self.top

        self.newgamebutton
        self.new""")

        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 9)
        self.treemanager.key_normal('(')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 13)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 8)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 9)
        self.treemanager.key_normal(' ')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 6)
        self.treemanager.key_delete()
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 4)
        self.treemanager.key_normal('=')
        self.treemanager.cursor_reset()
        self.move(DOWN, 4)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('[')

    def random_insert_delete_undo(self, program):
        import random
        self.reset()
        #self.save()

        self.treemanager.import_file(program)
        assert self.parser.last_status == True
        #self.save()

        self.text_compare(program)

        line_count = len(self.treemanager.lines)
        random_lines = list(range(line_count))
        random.shuffle(random_lines)

        start_version = self.treemanager.version
        for linenr in random_lines:
            cols = list(range(5))
            random.shuffle(cols)
            for col in cols:
                last_was_undo = False
                print("self.treemanager.cursor_reset()")
                self.treemanager.cursor_reset()
                print("self.move(DOWN, %s)" % (linenr))
                print("self.move(RIGHT, %s)" % (col))
                self.move(DOWN, linenr)
                self.move(RIGHT, col)
                k = self.get_random_key()
                if k in ["a", "c", "e", "g", "i", "k", "m", "1", "3", "5", "7"]:
                    # for a few characters DELETE instead of INSERT
                    print("self.treemanager.key_delete()")
                    x = self.treemanager.key_delete()
                elif k in ["o", "q", "s", "u"]:
                    print("self.treemanager.key_ctrl_z()")
                    x = self.treemanager.key_ctrl_z()
                    last_was_undo = True
                else:
                    key = self.get_random_key()
                    print("self.treemanager.key_normal(%s)" % (repr(key)))
                    x = self.treemanager.key_normal(key)
                if x == "eos":
                    continue
            if not last_was_undo:
                print("self.treemanager.undo_snapshot()")
                self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

        # redo all and compare with broken
        while self.treemanager.version < end_version:
            self.treemanager.key_shift_ctrl_z()

        self.text_compare(broken)

        # undo again and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(program)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(program)

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)



    def test_bug_infinite_loop(self):
        self.reset()

        self.treemanager.import_file(programs.pythonsmall)
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 8)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()
        self.treemanager.undo_snapshot()
        self.treemanager.cursor_reset()
        self.treemanager.key_ctrl_z()
        self.treemanager.cursor_reset()
        self.move(DOWN, 9)
        self.move(RIGHT, 0)
        self.treemanager.key_delete()

    def test_bug_undo_loop_2(self):

        self.reset()

        self.treemanager.import_file(programs.pythonsmall)
        assert self.parser.last_status == True

        start_version = self.treemanager.version

        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 3)
        self.treemanager.key_normal('#')
        self.treemanager.cursor_reset()
        self.move(DOWN, 5)
        self.move(RIGHT, 3)
        self.treemanager.key_normal(')')
        self.treemanager.undo_snapshot()

        end_version = self.treemanager.version
        broken = self.treemanager.export_as_text()

        # undo all and compare with original
        while self.treemanager.version > start_version:
            self.treemanager.key_ctrl_z()
        self.text_compare(programs.pythonsmall)

        t1 = TreeManager()
        parser, lexer = python.load()
        t1.add_parser(parser, lexer, python.name)
        t1.import_file(programs.pythonsmall)

        self.tree_compare(self.parser.previous_version.parent, parser.previous_version.parent)

    def test_bug_undo_typing(self):
        self.reset()

        self.treemanager.import_file(programs.pythonsmall)
        assert self.parser.last_status == True

        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 0)
        self.treemanager.key_normal("g")
        self.treemanager.key_ctrl_z()

        self.treemanager.cursor_reset()
        self.move(DOWN, 12)
        self.move(RIGHT, 2)
        self.treemanager.key_normal("%")
        self.treemanager.key_ctrl_z()

        self.treemanager.cursor_reset()
        self.move(DOWN, 13)
        self.move(RIGHT, 0)
        self.treemanager.key_normal("y")


class Test_Undo_LBoxes(Test_Helper):

    def setup_class(cls):
        parser, lexer = phppython.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, phppython.name)

        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def test_simple(self):
        self.reset()
        self.treemanager.import_file(programs.phpclass)
        self.move(UP, 1)

        self.treemanager.add_languagebox(lang_dict["Python + PHP"])

        self.treemanager.key_normal("p")
        self.treemanager.key_normal("a")
        self.treemanager.key_normal("s")
        self.treemanager.key_normal("s")
        self.treemanager.undo_snapshot()

        self.move(DOWN, 1)
        self.treemanager.key_end()
        self.treemanager.key_normal("a")
        self.treemanager.undo_snapshot()

        self.treemanager.key_ctrl_z()
        self.treemanager.key_ctrl_z()

    def test_simple2(self):
        pytest.skip("For some reason copy.deepcopy errors on this test with the new history service.")
        self.versions = []
        self.reset()
        self.versions.append(self.treemanager.export_as_text())
        self.treemanager.import_file(programs.phpclass)
        self.versions.append(self.treemanager.export_as_text())
        self.move(DOWN, 1)

        self.treemanager.add_languagebox(lang_dict["Python + PHP"])

        text = "def x():\r    pass"
        for c in text:
            self.treemanager.key_normal(c)

        self.treemanager.undo_snapshot()

        import copy
        dp = copy.deepcopy(self.parser.previous_version.parent)
        self.versions.append(self.treemanager.export_as_text())
        self.treemanager.key_normal("a")
        self.treemanager.undo_snapshot()
        self.versions.append(self.treemanager.export_as_text())

        self.move(UP, 2)
        self.treemanager.key_end()
        self.treemanager.key_normal("\r")
        self.treemanager.undo_snapshot()
        self.versions.append(self.treemanager.export_as_text())
        self.treemanager.key_normal("a")
        self.treemanager.undo_snapshot()
        self.versions.append(self.treemanager.export_as_text())

        assert self.versions.pop() == self.treemanager.export_as_text()
        self.treemanager.key_ctrl_z()
        assert self.versions.pop() == self.treemanager.export_as_text()
        self.treemanager.key_ctrl_z()
        assert self.versions.pop() == self.treemanager.export_as_text()
        self.treemanager.key_ctrl_z()
        assert self.versions.pop() == self.treemanager.export_as_text()

        self.tree_compare(self.parser.previous_version.parent, dp)

    def test_clean_version_bug(self):
        self.reset()
        self.treemanager.import_file(programs.phpclass)
        self.move(DOWN, 1)

        self.treemanager.add_languagebox(lang_dict["Python + PHP"])
        self.treemanager.key_normal("p")
        self.treemanager.key_normal("a")
        self.treemanager.key_normal("s")
        self.treemanager.key_normal("s")
        self.treemanager.undo_snapshot()

        import copy
        dp = copy.deepcopy(self.parser.previous_version.parent)

        self.treemanager.key_normal("a")
        self.treemanager.undo_snapshot()
        self.treemanager.key_ctrl_z()

        self.tree_compare(self.parser.previous_version.parent, dp)

        self.move(UP, 1)
        self.treemanager.key_end()
        self.move(LEFT, 2)
        self.treemanager.key_normal("x")
        self.treemanager.undo_snapshot()

        dp2 = copy.deepcopy(self.parser.previous_version.parent)
        self.treemanager.key_ctrl_z()
        self.treemanager.key_shift_ctrl_z()

        self.tree_compare(self.parser.previous_version.parent, dp2)

class Test_InputLogger(Test_Python):
    def test_simple(self):
        log = """self.key_normal('c')
self.key_normal('l')
self.key_normal('a')
self.key_normal('s')
self.key_normal('s')
self.key_normal(' ')
self.key_shift()
self.key_normal('X')
self.key_shift()
self.key_normal(':')
self.key_normal('\r')
self.key_normal('    ')
self.key_normal('d')
self.key_normal('e')
self.key_normal('f')
self.key_normal(' ')
self.key_normal('x')
self.key_backspace()
self.key_normal('y')
self.key_shift()
self.key_normal('o')
self.key_normal('o')
self.key_shift()
self.key_normal('(')
self.key_shift()
self.key_normal(')')
self.key_normal(':')
self.key_normal('\r')
self.key_normal('    ')
self.key_normal('x')
self.key_normal(' ')
self.key_normal('=')
self.key_normal(' ')
self.key_normal('1')
self.key_cursors(KEY_UP, False)
self.key_cursors(KEY_LEFT, False)
self.key_cursors(KEY_LEFT, False)
# mousePressEvent
self.cursor.line = 1
self.cursor.move_to_x(11)
self.selection_start = self.cursor.copy()
self.selection_end = self.cursor.copy()
self.cursor.line = 1
self.cursor.move_to_x(8)
self.selection_end = self.cursor.copy()
self.cursor.line = 2
self.key_normal('f')
self.key_normal('o')
self.key_normal('o')
# mousePressEvent
self.cursor.line = 2
self.cursor.move_to_x(16)
self.selection_start = self.cursor.copy()
self.selection_end = self.cursor.copy()
self.key_backspace()
self.add_languagebox('SQL (Dummy)')
self.key_shift()
self.key_normal('S')
self.key_normal('E')
self.key_normal('L')
self.key_normal('E')
self.key_normal('C')
self.key_normal('T')
self.key_normal(' ')
self.key_shift()
self.key_normal('*')
self.key_shift()
self.key_normal(' ')
self.key_normal('F')
self.key_normal('R')
self.key_normal('O')
self.key_normal('M')
self.key_normal(' ')
self.key_normal('t')
self.key_normal('a')
self.key_normal('b')
self.key_normal('l')
self.key_normal('e')"""

        self.treemanager.apply_inputlog(log)
        assert self.treemanager.export_as_text() == """class X:
    def foo():
        x = SELECT * FROM table"""

class Test_Comments_Indents(Test_Python):
    def test_newline(self):
        self.reset()
        for c in "y = 12 # blaz = 13":
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

        self.move(LEFT, 6)
        self.treemanager.key_normal("\r")
        assert self.parser.last_status == True

    def test_single_line_comment(self):
        self.reset()
        for c in """x = 12
y = 13""":
            self.treemanager.key_normal(c)
        assert self.parser.last_status == True

        self.move(LEFT, 6)
        self.move(UP, 1)
        self.treemanager.key_normal("#")
        assert self.parser.last_status == True
        
class Test_ChangeReporting(Test_Helper):

    def setup_class(cls):
        parser, lexer = calc.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, calc.name)
        cls.treemanager.set_font_test(7, 17) # hard coded. PyQt segfaults in test suite

    def test_right_sibling_bug(self):
        for k in "1+2+3":
            self.treemanager.key_normal(k)

        self.move(LEFT, 3)
        self.treemanager.key_normal("+")
        self.move(RIGHT, 2)
        self.treemanager.key_normal("+")
        self.move(LEFT, 1)
        self.treemanager.key_normal("4")

class Test_ErrorRecovery(Test_Helper):

    def setup_class(cls):
        parser, lexer = calc.load()
        cls.lexer = lexer
        cls.parser = parser
        cls.parser.init_ast()
        one = TextNode(Terminal("1"))
        one.lookup = "INT"
        cls.parser.previous_version.parent.children[0].insert_after(one)
        cls.ast = cls.parser.previous_version
        cls.treemanager = TreeManager()
        cls.treemanager.add_parser(cls.parser, cls.lexer, calc.name)
        cls.treemanager.set_font_test(7, 17)

    def test_simple(self):
        self.treemanager.import_file("1*1+2+3*4+2")
        assert self.parser.last_status == True

        self.treemanager.key_end()
        self.move(LEFT, 3)
        self.treemanager.key_normal("+")

        assert self.parser.last_status == False

    def test_empty(self):
        self.reset()
        assert self.parser.last_status == False

    def test_slow_input(self):
        self.reset()
        assert self.parser.last_status == False
        self.treemanager.key_normal("1")
        self.treemanager.key_normal("+")
        assert self.parser.last_status == False
        self.treemanager.key_normal("2")
        assert self.parser.last_status == True

    def test_simple2(self):
        self.reset()
        self.treemanager.import_file("1+2")
        assert self.parser.last_status == True

        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("*")

        assert self.parser.last_status == False

    def test_simple3(self):
        self.reset()
        self.treemanager.import_file("1+2")
        assert self.parser.last_status == True

        self.treemanager.key_end()
        self.move(LEFT, 2)
        self.treemanager.key_normal("*")

        assert self.parser.last_status == False

    def test_double_error(self):
        self.reset()
        assert self.parser.last_status == False
        self.treemanager.import_file("1*1+2+3*4+2")
        assert self.parser.last_status == True

        self.treemanager.key_end()
        self.move(LEFT, 3)
        self.treemanager.key_normal("+")
        self.move(LEFT, 5)
        self.treemanager.key_normal("*")

        assert self.parser.last_status == False

        assert len(self.parser.error_nodes) == 2

    def test_triple_error(self):
        self.reset()
        assert self.parser.last_status == False
        self.treemanager.import_file("1*1+2+3*4+2")
        assert self.parser.last_status == True

        self.treemanager.key_end()
        self.move(LEFT, 3)
        self.treemanager.key_normal("+")
        assert len(self.parser.error_nodes) == 1
        self.move(LEFT, 5)
        self.treemanager.key_normal("*")
        assert len(self.parser.error_nodes) == 2
        self.move(LEFT, 3)
        self.treemanager.key_normal("+")
        assert len(self.parser.error_nodes) == 3

        assert self.parser.last_status == False

    def test_error_in_isotree(self):
        self.reset()
        self.treemanager.import_file("1+2*3")
        self.treemanager.key_home()
        self.move(RIGHT, 2)
        self.treemanager.key_normal("*")
        assert len(self.parser.error_nodes) == 1

        self.move(RIGHT, 2)
        self.treemanager.key_normal("+")
        assert len(self.parser.error_nodes) == 2

    def test_error_in_isotree_reverse(self):
        self.reset()
        self.treemanager.import_file("1+2*3")
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("+")
        assert len(self.parser.error_nodes) == 1

        self.move(LEFT, 3)
        self.treemanager.key_normal("*")
        assert len(self.parser.error_nodes) == 2

    def test_testing_ooc1(self):
        # Testing out-of-context analysis where the analysis fails and the result
        # can not be integrated into the tree
        self.reset()
        self.treemanager.import_file("1+2")
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("*")
        self.treemanager.key_end()
        self.treemanager.key_normal("+")
        self.treemanager.key_normal("3")

    def test_testing_ooc2(self):
        # Testing out-of-context analysis where the analysis succeeds and the result
        # is being integrated into the tree
        self.reset()
        self.treemanager.import_file("1+2")
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("*")
        self.treemanager.key_end()
        self.treemanager.key_normal("*")
        assert self.treemanager.cursor.node.symbol.name == "*"
        self.treemanager.key_normal("3")
        assert self.treemanager.cursor.node.symbol.name == "3"
        assert self.treemanager.cursor.node.left == None # if ooc fails, this would be '*'

    def test_typing_after_successfull_ooc(self):
        self.reset()
        self.treemanager.import_file("1+2")
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_normal("*")
        self.treemanager.key_end()
        self.treemanager.key_normal("*")
        self.treemanager.key_normal("3")
        assert self.parser.last_status == False
        assert len(self.parser.error_nodes) > 0

        # continue after successful out-of-context analysis and integration
        self.treemanager.key_normal("+")
        assert self.parser.last_status == False
        assert len(self.parser.error_nodes) > 0

        self.treemanager.key_normal("3")
        assert self.parser.last_status == False
        assert len(self.parser.error_nodes) > 0

    def test_temp(self):
        self.reset()
        self.treemanager.import_file("1+2*3")
        self.treemanager.key_end()
        self.move(LEFT, 4)
        self.treemanager.key_normal("*")
        self.move(RIGHT, 2)
        self.treemanager.key_normal("+")

    def test_changes_in_isotree(self):
        self.reset()
        self.treemanager.import_file("1+2*3")
        self.treemanager.key_home()
        self.move(RIGHT, 1)
        self.treemanager.key_normal("*")
        assert self.parser.last_status == False
        self.treemanager.key_backspace()
        assert self.parser.last_status == True
        self.move(RIGHT, 3)
        self.treemanager.key_normal("+")
        assert self.parser.last_status == False

    def test_nested_errors(self):
        self.reset()
        self.treemanager.key_normal("1")
        self.treemanager.key_normal("+")
        self.treemanager.key_normal("2")
        self.move(LEFT, 2)
        self.treemanager.key_normal("*")
        assert self.parser.last_status == False
        self.move(RIGHT, 1)
        self.treemanager.key_normal("+")
        assert self.parser.last_status == False
        self.move(LEFT, 1)
        self.treemanager.key_normal("2")
        assert self.parser.last_status == False
        self.move(LEFT, 1)
        self.treemanager.key_backspace()
        assert self.parser.last_status == True

class Test_ErrorRecoveryPython(Test_Python):
    def test_delete(self):
        self.reset()
        self.treemanager.import_file("class X:\n    pass")
        for i in range(18):
            self.treemanager.key_delete()

    def test_foo(self):
        self.reset()
        self.treemanager.import_file("class X:\n    def x():\n        x = 1")

        self.move(DOWN, 2)
        self.treemanager.key_end()
        self.treemanager.key_backspace()
        self.treemanager.key_normal("]")
        self.treemanager.key_normal("e")

    def test_nodereuse_bug(self):
        t = TreeManager()
        parser, lexer = calc.load()
        t.add_parser(parser, lexer, "Calc")

        t.key_normal("1")
        t.key_normal("+")
        t.key_normal("2")

        # remember nodes
        t.key_home()
        t.key_cursors(RIGHT)
        assert t.cursor.node.symbol.name == "1"
        P = t.cursor.node.parent
        T = t.cursor.node.parent.parent
        E = t.cursor.node.parent.parent.parent
        assert P.symbol.name == "P"
        assert T.symbol.name == "T"
        assert E.symbol.name == "E"

        t.key_normal("+")

        # check if nodes have been reused
        t.key_home()
        t.key_cursors(RIGHT)
        assert t.cursor.node.symbol.name == "1"
        assert t.cursor.node.parent is P
        assert t.cursor.node.parent.parent is T
        assert t.cursor.node.parent.parent.parent is E

class Test_ErrorRecoveryJava(Test_Java):
    def test_delete(self):
        self.reset()
        self.treemanager.import_file("class X{\n    int x;\n}")
        for i in range(36):
            self.treemanager.key_delete()

    def test_foo(self):
        self.reset()
        self.treemanager.import_file("class X{\n    public void main()(){\n        int x = 1;\n}\n}")

        self.move(DOWN, 2)
        self.treemanager.key_end()
        self.move(LEFT, 1)
        self.treemanager.key_backspace()
        self.treemanager.key_normal("]")
        self.treemanager.key_normal("e")

from grammars.grammars import EcoFile
class Test_ErrorRecoveryRightbreakdown:
    def test_simple(self):
        # With the default Wagner implementation this test breaks upon
        # attempting a rightbreak on a subtree that has been isolated.
        # The Wagner thesis doesn't mention anything related to this, which
        # either means they didn't run into this or they are doing something
        # behind the scenes that they don't talk about.
        # My solution is simply to cancel the rightbreakdown procedure when it sees
        # an isolated subtree.
        grm = EcoFile("Errortest", "test/errortest.eco", "Error")
        t = TreeManager()
        parser, lexer = grm.load()
        t.add_parser(parser, lexer, python.name)

        t.key_normal("a")
        t.key_normal("b")
        t.key_normal("w")
        t.key_normal("s")

        assert parser.last_status == True

        t.key_cursors(LEFT)
        t.key_cursors(LEFT)
        t.key_cursors(LEFT)

        t.key_normal("c")
        t.key_delete()

        assert parser.last_status == False

class Test_ErrorRecoverySurroundingContext:
    def test_simple(self):
        # This test checks the correct behaviour for skipping already isolated
        # subtrees. Before we can skip an isolated subtree, we need to make sure
        # that it's surrounding context hasn't changed. The surrounding context
        # of an isolated subtree is it's next terminal. So if the left-most
        # subtree to the right of the isolated subtree has changes, we need to
        # reevalute the isolated subtree and cannot skip it.
        # Also tests if isolated subtrees are reached at all as we need to keep
        # a changed path down to the isotree to recheck their surrounding
        # context.
        grm = EcoFile("ErrortestSur", "test/errorsurroundingcontext.eco", "ErrorSurround")
        t = TreeManager()
        parser, lexer = grm.load()
        t.add_parser(parser, lexer, python.name)

        t.key_normal("a")
        t.key_normal("c")
        t.key_cursors(LEFT)
        t.key_normal("b")
        t.key_cursors(RIGHT)
        t.key_normal("d")

        assert parser.last_status == True
        t.key_home()
        t.key_cursors(RIGHT)
        assert t.cursor.node.symbol.name == "ab"
        # without checking surrounding context this would be 'left'
        assert t.cursor.node.parent.symbol.name == "left2"

class Test_RetainSubtree:

    def test_simple(self):
        # This test checks that if a node is being retained but it's parent node
        # was reset, that the siblings of the node are updated as well, as they
        # could have changed when the parent was reverted back to the previous
        # version.
        grm = EcoFile("RetainTest", "test/retaincalc.eco", "RetainTest")
        t = TreeManager()
        parser, lexer = grm.load()
        t.add_parser(parser, lexer, "RT")

        t.key_normal("1")
        t.key_normal("+")
        t.key_normal("2")

        t.key_home()
        t.key_cursors(RIGHT)

        assert t.cursor.node.symbol.name == "1"
        assert t.cursor.node.parent.symbol.name == "P"

        t.key_normal("*")
        t.key_cursors(LEFT)

        assert t.cursor.node.symbol.name == "1"
        assert t.cursor.node.parent.symbol.name == "P" # must not be 'X'

    def test_simple2(self):
        # Tests basic retainablity
        grm = EcoFile("RetainTest2", "test/retaincalc2.eco", "RetainTest2")
        t = TreeManager()
        parser, lexer = grm.load()
        t.add_parser(parser, lexer, "RT")

        t.key_normal("1")
        t.key_normal("*")
        t.key_normal("2")

        # Create an error
        t.key_cursors(LEFT)
        t.key_normal("*")

        # Add changes that can be retained
        t.key_home()
        t.key_cursors(RIGHT)
        t.key_normal("-")
        t.key_normal("3")

        assert t.cursor.node.symbol.name == "3"
        assert t.cursor.node.parent.symbol.name == "X" # will be 'P' without retaining

    def test_bug1(self):
        """There is currently a bug in the retainability algorithm that causes
        an infinite loop when a certain subtree is retained. In this test case
        the bug happens when an empty non-terminal A (child of node B) is being
        reused and becomes a child of another node C. After error recovery the
        previous parent (B) is reverted which includes resetting A as well.
        However the new parent (C) is being retained, causing it to keep a child
        reference to A. Now A is being referenced by two different parents (B
        and C), causing an infinite loop when traversing the parse tree. The
        implementation however is correct and the error can also be reproduced
        when manually applying Wagners algorithm to this problem. For this
        reason retainability is current disabled in the parser until this
        problem has been resolved."""
        t = TreeManager()
        parser, lexer = python.load()
        t.add_parser(parser, lexer, "Python")

        for c in "class X:\n pass":
            t.key_normal(c)

        t.key_cursors(UP)
        t.key_home()
        t.key_delete()
        t.key_delete()
        t.key_delete()
        t.key_delete()
        t.key_delete()

        startrule = parser.previous_version.parent.children[1]
        assert startrule.symbol.name == "Startrule"

        WS = startrule.children[0]
        assert WS.symbol.name == "WS"
        assert WS.parent is startrule

        classdef = startrule.children[1].children[0].children[0].children[0].children[0]
        assert classdef.symbol.name == "classdef"

        WS2 = classdef.children[1]
        assert WS2.symbol.name == "WS"

        WS3 = WS2.children[0]
        assert WS3.symbol.name == "WS"

        # current retaining creates a loop here as 'WS' is partly reverted and
        # retained at the same time
        assert WS3 is not WS

class Test_TopDownReuse(Test_Python):

    def test_basic(self):
        grm = EcoFile("Undotest", "test/undobug1.eco", "Undo")
        t = TreeManager()
        parser, lexer = grm.load()
        t.add_parser(parser, lexer, python.name)

        t.key_normal("a")
        t.undo_snapshot()
        t.key_normal("b")
        t.undo_snapshot()
        t.key_normal("c")
        t.undo_snapshot()
        assert parser.last_status == True

        startrule = parser.previous_version.parent.children[1]
        E = startrule.children[1]
        assert E.symbol.name == "E"
        Y = E.children[0]
        assert Y.symbol.name == "Y"

        t.key_cursors(LEFT)
        t.key_cursors(LEFT)
        t.key_normal("x")
        t.undo_snapshot()
        assert parser.last_status == True

        startrule2 = parser.previous_version.parent.children[1]
        E2 = startrule2.children[1]
        assert E2.symbol.name == "E"
        Y2 = E2.children[0]
        assert Y2.symbol.name == "Y"

        # check if they have been reused
        assert startrule is startrule2
        assert E is E2
        assert Y is Y2

sql_single = lang_dict["SQL Statement"]
javapy = lang_dict["Java + Python"]
javasql = lang_dict["Java + SQL"]
javasqlchemical = javasql

# Add some more compositions that we only need inside the test environment
pythonsql = EcoFile("Python + SQL", "grammars/python275.eco", "Python")
pythonsql.add_alternative("atom", sql_single)
lang_dict[pythonsql.name] = pythonsql

import json
from grammars.grammars import create_grammar_from_config
with open("test/javasqldummy.json") as f:
    cfg = json.load(f)
    javasql2_name = create_grammar_from_config(cfg, "test/javasqldummy.json")
    javasqlchemical = lang_dict[javasql2_name]

grm_cache = {}
def load_json_grammar(filename):
    if filename in grm_cache:
        return grm_cache[filename]

    with open(filename) as f:
        cfg = json.load(f)
        name = create_grammar_from_config(cfg, filename)
        grm = lang_dict[name]
        grm_cache[filename] = grm
        return grm

class Test_AutoLanguageBoxDetection():

    def test_pythonsql(self):
        parser, lexer = pythonsql.load()
        parser.setup_autolbox(pythonsql.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = SELECT * FROM table WHERE y=1":
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2
        assert parser.last_status == True

    def test_pythonsql2(self):
        parser, lexer = pythonsql.load()
        parser.setup_autolbox(pythonsql.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        treemanager.key_normal(";")
        treemanager.key_cursors(LEFT)

        for c in "x = SELECT * FROM table":
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2

    def test_java_python(self):
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "class X {\n\n}":
            treemanager.key_normal(c)
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        for c in "    def x():\n    ":
            treemanager.key_normal(c)
        assert parser.last_status == False
        assert len(treemanager.parsers) == 1

        treemanager.key_normal("p")
        assert parser.last_status == True
        assert len(treemanager.parsers) == 2

    def test_java_python2(self):
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "class X {\n\n\n\n}":
            treemanager.key_normal(c)
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        for c in "    def x():\n    ":
            treemanager.key_normal(c)
        assert parser.last_status == False
        assert len(treemanager.parsers) == 1

        treemanager.key_normal("p")
        assert parser.last_status == True
        assert len(treemanager.parsers) == 2

    @pytest.mark.xfail
    def test_java_python3(self):
        """Currently fails as `public` is being parsed into the Python language
        box."""
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        code = """class X {



    public void y(){
    }
}"""
        for c in code:
            treemanager.key_normal(c)
        assert parser.last_status == True

        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        for c in "    def x():\n    ":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == False

        treemanager.key_normal("p")
        assert len(treemanager.parsers) == 2
        assert parser.last_status == True

    def test_php_python5_first_line_box(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "def x():\n    ":
            treemanager.key_normal(c)

        treemanager.key_normal("p")
        assert parser.last_status == True
        assert len(treemanager.parsers) == 2

    def test_php_python_expression(self):
        """Results in two options for language box:
        Python or Python expression"""
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "$x = [x for x in range(10)":
            treemanager.key_normal(c)
        assert parser.last_status == False

        treemanager.key_normal("]")
        treemanager.leave_languagebox()
        treemanager.key_normal(";")

        assert len(parser.error_nodes) == 1
        assert len(parser.error_nodes[0].autobox) == 2

    def test_php_python_expression2(self):
        """Previously, we could only find the `not 2` option here.  With the
        introduction of the line heuristic, we can now find the full expression
        `1 or not 2` as well."""
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "$x = 1 or not ":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

        assert len(parser.error_nodes) == 1
        assert parser.error_nodes[0].autobox is None

        treemanager.key_normal("2")
        treemanager.key_normal(";")

        assert len(parser.error_nodes) == 1
        assert len(parser.error_nodes[0].autobox) == 4

    def test_include_rules(self):
        grm = EcoFile("Python + HTML (Include)", "grammars/python275.eco", "Python")
        grm.add_alternative("atom", html)
        grm.set_auto_include("HTML", set(["<html", "<img"]))
        lang_dict[grm.name] = grm

        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = <html></html>":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 2

        parser.reset()
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = <span></span>":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

    def test_exclude_rules(self):
        grm = EcoFile("Python + HTML (Exclude)", "grammars/python275.eco", "Python")
        grm.add_alternative("atom", html)
        grm.set_auto_exclude("HTML", set(["TEXT"]))
        lang_dict[grm.name] = grm

        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = <span></span>":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 2

        parser.reset()
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = FROM table":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.error_nodes[0].autobox is None # would be set without excluding TEXT

    def test_autoremove_pythonsql(self):
        parser, lexer = pythonsql.load()
        parser.setup_autolbox(pythonsql.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = SELECT * FROM table":
            treemanager.key_normal(c)

        assert parser.last_status == True
        assert len(treemanager.parsers) == 2

        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)

        treemanager.key_normal("*") # valid Python now
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

    def test_php_python_paste(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "class X{\n}":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(LEFT)
        treemanager.key_normal("\n")
        treemanager.key_cursors(UP)
        treemanager.key_normal(" ")
        treemanager.key_normal(" ")
        treemanager.key_normal(" ")
        treemanager.key_normal(" ")

        treemanager.pasteText("def x():\n        pass;")
        assert parser.last_status is True
        assert len(treemanager.parsers) == 2

    def test_php_python_paste2(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "function x(){\n}":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(LEFT)
        treemanager.key_normal("\n")
        treemanager.key_cursors(UP)
        treemanager.key_normal(" ")
        treemanager.key_normal(" ")
        treemanager.key_normal(" ")
        treemanager.key_normal(" ")

        treemanager.pasteText("$x = def x():\n        pass;")
        # XXX problem: error happens on `}` but `reduce_ends` only checks
        # next terminal which is `<return>` and can be parsed
        assert parser.last_status is True
        assert len(treemanager.parsers) == 2

    def test_python_sql_bug(self):
        parser, lexer = pythonsql.load()
        parser.setup_autolbox(pythonsql.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in "x = SELECT * FROM table":
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2

        for _ in range(5):
            treemanager.key_cursors(LEFT)
        treemanager.key_normal("*")

        assert len(treemanager.parsers) == 1

        treemanager.key_backspace()

        assert len(treemanager.parsers) == 2

    def test_newbug(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        phpprogram = """function x(){
    $x = 12;
}"""
        # delete 12
        treemanager.import_file(phpprogram)
        treemanager.key_cursors(DOWN)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_backspace()
        treemanager.key_backspace()

        for c in "[1,2.3]":
            treemanager.key_normal(c)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        # check that there wasn't a language box inserted around '1'
        assert treemanager.cursor.node.symbol.name == "1"

    def test_newbug2(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        for c in """function x(){
            $x = [1,2,3];
            }""":
            treemanager.key_normal(c)

    def test_newbug3(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """function x(){
    $x = [1,2,3];
}"""
        treemanager.import_file(p)
        treemanager.key_cursors(DOWN)
        treemanager.key_cursors(DOWN)
        treemanager.key_end()
        for c in range(len(p)):
            treemanager.key_backspace()

    def test_php_bug4(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """function x(){

    return 12;
}"""
        treemanager.import_file(p)
        treemanager.key_cursors(DOWN)
        treemanager.key_home()
        for c in "    $x = def y():":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 2

    def test_java_py_string(self):
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    int x = "test";
}"""
        for c in p:
            treemanager.key_normal(c)

    def test_java_sql_autoremove_valid_boxes(self):
        parser, lexer = javasqlchemical.load()
        parser.setup_autolbox(javasqlchemical.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    int x = 1;
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_backspace()
        for c in "SELECT * FROM table;":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 2

        treemanager.key_backspace() # delete ;
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_normal("*")
        assert len(treemanager.parsers) == 1

    def test_java_python_method_insert_bug1(self):
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {


    public boolean main(){}
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_home()

        for c in "    ":
            treemanager.key_normal(c)
        treemanager.key_normal("d")

        assert len(treemanager.parsers) == 1

    def test_deactivate_autobox_after_undo(self):
        """Once an automatically inserted language box has been
        undone, it shouldn't be inserted again on another change."""
        parser, lexer = javapy.load()
        parser.setup_autolbox(javapy.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        program = """class X {
    int x = 12;
}"""
        for c in program:
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        for c in " and ":
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2

        treemanager.key_ctrl_z()

        assert len(treemanager.parsers) == 1

        treemanager.key_cursors(RIGHT)
        for c in " or 3":
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1

    def test_php_python_whitespace_bug(self):
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    d();
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 2

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)

        assert treemanager.parsers[0][0].last_status is True # PHP
        assert treemanager.parsers[1][0].last_status is True # Python

        treemanager.key_normal(" ")

        assert treemanager.parsers[0][0].last_status is True
        assert treemanager.parsers[1][0].last_status is False

        treemanager.key_backspace()

        assert treemanager.parsers[0][0].last_status is True
        assert treemanager.parsers[1][0].last_status is True

    import os
    @pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason="JavaSQL takes too long to built on Travis. Skip!")
    def test_java_sql_skip_comments(self):
        p = """public class Scribble {

    public void init() {
        // A comment
        this.foo1(code.replace());

        // Another comment
        this.foo2();
    }
}"""

        parser, lexer = javasql.load()
        parser.setup_autolbox(javasql.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in p:
            treemanager.key_normal(c)

        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        for _ in range(14):
            treemanager.key_backspace()

        assert parser.last_status == True

        p = """SELECT ProductName
FROM Products
WHERE ProductID IN (SELECT ProductID FROM OrderDetails WHERE Quantity = 10);"""
        for c in p:
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2
        assert parser.last_status == True

    def test_java_sql_ranking(self):
        p = """class C {
int x = 1, y = 2;
int y = 1 + 2 * 3;
int z = 4 + 5 - 6;
}"""

        parser, lexer = javasql.load()
        parser.setup_autolbox(javasql.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")

        for c in p:
            treemanager.key_normal(c)

        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_cursors(UP)
        treemanager.key_end()
        for i in range(8): treemanager.key_cursors(LEFT)
        treemanager.key_backspace()
        for s in "SELECT a":
            treemanager.key_normal(s)
        assert len(parser.error_nodes[0].autobox) == 2

    def test_php_python_autoremove(self):
        """Sometimes automatically inserted boxes are valid in both languages.
        Previously we only autoremoved boxes that were invalid. However, we
        should always prioritise the outer language instead even if the language
        box is a valid insertion."""
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        treemanager.key_normal("f")
        assert len(treemanager.parsers) == 2
        treemanager.key_normal("o")
        assert len(treemanager.parsers) == 2
        treemanager.key_normal("o")
        assert len(treemanager.parsers) == 2
        treemanager.key_normal("(")
        assert len(treemanager.parsers) == 1
        treemanager.key_normal(")")
        assert len(treemanager.parsers) == 2
        treemanager.key_normal(";")
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

    @pytest.mark.xfail
    def test_php_python_auto_bug(self):
        """PHP equivalent to `test_java_python3`. Fails because `public` is
        optional in PHP and thus can be used in a Python box without making the
        PHP program invalid."""
        parser, lexer = phppython.load()
        parser.setup_autolbox(phppython.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    public function x(){}
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_home()
        treemanager.key_cursors(RIGHT)
        treemanager.key_cursors(RIGHT)
        treemanager.key_cursors(RIGHT)
        treemanager.key_cursors(RIGHT)
        treemanager.key_normal("d")

        assert len(treemanager.parsers) == 1
        assert parser.last_status == False

    def test_java_lua_dont_remove_explicit_lboxes(self):
        grm = load_json_grammar("test/javalua_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    int x = 1;
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.add_languagebox(lang_dict["Lua expr"])
        treemanager.key_normal("a")

        assert len(treemanager.parsers) == 2
        assert parser.last_status == False

    @pytest.mark.skip("Broken by line heuristic. Requires expanding boxes to include following language boxes.")
    def test_java_php_expand(self):
        grm = load_json_grammar("test/javaphp_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """class X {
    int x = 1 == 2;
}"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_backspace() # delete `1`
        p2 = "!e($x) ? $y : $z"
        for c in p2:
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2
        assert parser.last_status == False # only `!e($x)` wrapped in lbox

        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_backspace()
        treemanager.key_backspace()
        treemanager.key_backspace()
        treemanager.key_backspace()

        assert len(treemanager.parsers) == 2 # box now has been expanded
        assert parser.last_status == True

    def test_java_php_shrink_bug(self):
        grm = load_json_grammar("test/javaphp_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        assert len(treemanager.parsers) == 1
        p = """class X {
    public void println() {
        if (numPrinted >= numLines) {
        }

        int x = (a == 'x');
    }
}"""
        treemanager.import_file(p)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(DOWN)
        treemanager.key_cursors(DOWN)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        for i in range(22):
            treemanager.key_backspace()

        p2 = "'set_transient_' . $transient'"
        for c in p2:
            treemanager.key_normal(c)
        assert parser.last_status == True

    def test_java_php_shrink_bug2(self):
        grm = load_json_grammar("test/javaphp_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        assert len(treemanager.parsers) == 1
        p = """class X {
    public void println() {
        if (i < fDepth - 1) {
            System.out.print(',');
        }
    }
}"""
        treemanager.import_file(p)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(DOWN)
        treemanager.key_cursors(DOWN)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        for i in range(14):
            treemanager.key_backspace()

        p2 = "d('i') && $s->l('i')"
        for c in p2:
            treemanager.key_normal(c)
        assert parser.last_status == True

    def test_java_php_preparse_bug(self):
        grm = load_json_grammar("test/javaphp_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        assert len(treemanager.parsers) == 1
        p = """class C {
public static int contents = {
    { SOMEVAR, "strubg" },

    { ANOTHERVAR, "string ',' string!"}
};
}"""
        treemanager.import_file(p)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(DOWN)
        treemanager.key_cursors(DOWN)
        treemanager.key_end()
        for i in range(13):
            treemanager.key_cursors(LEFT)
        for i in range(7):
            treemanager.key_backspace()
        for c in "'test'":
            print("input", c)
            treemanager.key_normal(c)

    def test_java_php_slashslash_bug(self):
        grm = load_json_grammar("test/javaphp_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        assert len(treemanager.parsers) == 1
        p = """class C {
int x = 1;
}"""
        treemanager.import_file(p)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(DOWN)
        treemanager.key_end()
        treemanager.key_cursors(LEFT);
        treemanager.key_backspace()
        for c in "$this . 'http://":
            treemanager.key_normal(c)
        treemanager.key_normal("'")
        assert parser.last_status is True
        assert len(treemanager.parsers) == 2

    @pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason="Sqlite takes too long to built on Travis. Skip!")
    def test_lua_sqlite_expand(self):
        grm = load_json_grammar("test/luasqlite_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """x = 1
y = 2"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_backspace()
        p2 = "INSERT INTO k2 VALUES(a, NULL); PRAGMA f(k2);"
        for c in p2:
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2
        assert parser.last_status == True

    @pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason="Sqlite takes too long to built on Travis. Skip!")
    def test_sqlite_java_shrink(self):
        grm = load_json_grammar("test/sqlitejava_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = "SELECT a FROM t;"
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_home()
        for i in range(8):
            treemanager.key_cursors(RIGHT)
        treemanager.key_normal("(")
        treemanager.key_normal(")")
        treemanager.key_normal(".") # wrap `a(). FROM` in lbox
        treemanager.key_normal("d") # shrink box to `a().d`

        assert len(treemanager.parsers) == 2
        assert parser.last_status == True

    @pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason="Sqlite takes too long to built on Travis. Skip!")
    def test_lua_sqlite_bug(self):
        grm = load_json_grammar("test/luasqlite_expr.json")
        parser, lexer = grm.load()
        parser.setup_autolbox(grm.name, lexer)
        treemanager = TreeManager()
        treemanager.option_autolbox_insert = True
        treemanager.add_parser(parser, lexer, "")
        p = """x = 1,2
y = 2"""
        for c in p:
            treemanager.key_normal(c)
        assert len(treemanager.parsers) == 1
        assert parser.last_status == True

        treemanager.key_cursors(UP)
        treemanager.key_end()
        treemanager.key_cursors(LEFT)
        treemanager.key_cursors(LEFT)
        treemanager.key_backspace()
        p2 = "SELECT a FROM t1;"
        for c in p2:
            treemanager.key_normal(c)

        assert len(treemanager.parsers) == 2
        assert parser.last_status == True
