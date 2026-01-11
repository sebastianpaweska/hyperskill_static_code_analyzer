import ast
import os
import re
import argparse
from collections import deque


# TODO temporary solution
class CaseCheckers:
    @staticmethod
    def is_camel_case(name):
        pattern = r"^[A-Z][a-z]+(?:[A-Z][a-z]+)*$"
        return bool(re.fullmatch(pattern, name))

    @staticmethod
    def is_snake_case(name):
        pattern = r'^(__[a-z_][a-z0-9_]+__|__[a-z][a-z0-9_]*|_[a-z][a-z0-9_]*|[a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*)$'
        return bool(re.fullmatch(pattern, name))


#########################

class Analyzer:
    def __init__(self):
        self.errors = []

    # static methods (validators)
    @staticmethod
    def is_line_too_long(line):
        return len(line) > 79

    @staticmethod
    def has_incorrect_indentation(line):
        if line.startswith(" "):
            first_char = len(line) - len(line.lstrip())
            return first_char % 4
        return False

    @staticmethod
    def ends_with_semicolon(line):
        parts = line.split("#")
        if len(parts) > 1:
            return Analyzer.ends_with_semicolon(parts[0])
        else:
            return line.strip().endswith(";")

    @staticmethod
    def has_two_spaces_before_comment(line):
        comment_start = line.find("#")
        if comment_start > 2:
            return line[comment_start - 1] == " " and line[comment_start - 2] == " "
        return True

    @staticmethod
    def has_todo(line):
        parts = line.split("#")
        if len(parts) > 1:
            return parts[1].upper().find("TODO") > -1
        return False

    @staticmethod
    def has_blank_lines(context_lines):
        line_p3, line_p2, line_p1 = context_lines
        return line_p3.strip() == '' and line_p2.strip() == '' and line_p1.strip() == ''

    @staticmethod
    def get_files(filepath):
        files = [f for f in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, f))]
        files.sort()
        paths = [os.path.join(filepath, f) for f in files]
        return paths

    @staticmethod
    def has_too_many_spaces(line):
        line = line.strip()
        is_construction = line.startswith("class") or line.startswith("def")
        if is_construction:
            first_space = line.find(" ")
            return line[first_space + 1] == " "
        return False

    @staticmethod
    def wong_class_name(line):
        line = line.lstrip()
        is_class = line.startswith("class")
        if is_class:
            class_name = Analyzer.get_class_name(line.lstrip())
            return not CaseCheckers.is_camel_case(class_name)
        return False

    @staticmethod
    def get_class_name(line):
        pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|:)'
        match = re.search(pattern, line)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def get_function_name(line):
        pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        match = re.search(pattern, line)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def wrong_function_name(line):
        line = line.lstrip()
        is_function = line.startswith("def")
        if is_function:
            function_name = Analyzer.get_function_name(line)
            return not CaseCheckers.is_snake_case(function_name)
        return False

    ######

    def process_path(self, filepath):
        is_directory = os.path.isdir(filepath)
        if is_directory:
            files = self.get_files(filepath)
            for file in files:
                # TODO ignore nested directories for now
                if os.path.isfile(file):
                    self.process_file(file)
        else:
            self.process_file(filepath)

    def print_errors(self):
        self.errors.sort(
            key=lambda x: (
                x.split(":")[0],  # Filename
                int(x.split("Line ")[1].split(":")[0]),  # Line number
                x.split(":")[2].strip()  # Error code
                )
        )
        for error in self.errors:
            print(error)

    def process_file(self, filepath):
        with open(filepath, "r") as f:
            context_lines = deque(['', '', ''], maxlen=3)
            for i, line in enumerate(f):
                if self.is_line_too_long(line):
                    self.errors.append(f"{filepath}: Line {i + 1}: S001 Too long")
                if self.has_incorrect_indentation(line):
                    self.errors.append(f"{filepath}: Line {i + 1}: S002 Indentation is not a multiple of four")
                if self.ends_with_semicolon(line):
                    self.errors.append(f"{filepath}: Line {i + 1}: S003 Unnecessary semicolon")
                if not self.has_two_spaces_before_comment(line):
                    self.errors.append(f"{filepath}: Line {i + 1}: S004 At least two spaces required before inline comments")
                if self.has_todo(line):
                    self.errors.append(f"{filepath}: Line {i + 1}: S005 TODO found")
                if i >= 3 and self.has_blank_lines(context_lines):
                    self.errors.append(f"{filepath}: Line {i + 1}: S006 More than two blank lines used before this line")
                context_lines.append(line.rstrip('\n'))

                # TODO move to validate_tree
                if self.has_too_many_spaces(line):
                    is_class = line.lstrip().startswith("class")
                    construction_name = is_class and "class" or "def"
                    print(f"{filepath}: Line {i + 1}: S007 Too many spaces after {construction_name}")
                if self.wong_class_name(line):
                    class_name = self.get_class_name(line.lstrip())
                    print(f"{filepath}: Line {i + 1}: S008 Class name {class_name} should be written in CamelCase")
                if self.wrong_function_name(line):
                    function_name = self.get_function_name(line.lstrip())
                    print(f"{filepath}: Line {i + 1}: S009 Function name {function_name} should be written in snake_case")


            tree_analyzer = TreeAnalyzer(filepath, self.errors)
            tree_analyzer.validate_tree()

class TreeAnalyzer:
    def __init__(self, path, errors):
        self.path = path
        self.errors = errors
        self.tree = None

    # static

    # TODO temporary commented -> move S007, S008, S009 here and remove CaseCheckers
    # @staticmethod
    # def is_snake_case(name):
    #     pattern = r'^(__[a-z_][a-z0-9_]+__|__[a-z][a-z0-9_]*|_[a-z][a-z0-9_]*|[a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*)$'
    #     return bool(re.fullmatch(pattern, name))

    # validators
    def validate_function_args(self, args):
        for arg in args.args:
            if not CaseCheckers.is_snake_case(arg.arg):
                self.errors.append(f"{self.path}: Line {arg.lineno}: S010 Argument name {arg.arg} should be written in snake_case")
                break
        for arg in args.defaults:
            if not isinstance(arg, ast.Constant):
                self.errors.append(f"{self.path}: Line {arg.lineno}: S012 The default argument value is mutable")
                break

    def validate_variable(self, variables):
        for var in variables:
            if isinstance(var, ast.Name):
                if not CaseCheckers.is_snake_case(var.id):
                    self.errors.append(
                        f"{self.path}: Line {var.lineno}: S011 Variable '{var.id}' in function should be written in snake_case")

    def validate_function_body(self, body):
        for element in body:
            if isinstance(element, ast.Assign):
                self.validate_variable(element.targets)  # S011

    def validate_tree(self, tree=None):
        if not tree:
            tree = ast.parse(self.path)
        nodes = ast.iter_child_nodes(tree)
        errors = []
        for node in nodes:
            if isinstance(node, ast.FunctionDef):
                self.validate_function_args(node.args)  # S010, S012
                self.validate_function_body(node.body)  # S011
            elif isinstance(node, ast.ClassDef):
                self.validate_tree(node)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepath",
        type=str
    )
    args = parser.parse_args()
    analyzer = Analyzer()
    analyzer.process_path(args.filepath)
    analyzer.print_errors()

if __name__ == "__main__":
    main()

