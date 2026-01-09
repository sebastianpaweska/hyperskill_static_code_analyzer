import ast
import os
import re
import argparse
from collections import deque


def line_too_long(line):
    return len(line) > 79

def has_correct_indentation(line):
    if line.startswith(" "):
        first_char = len(line) - len(line.lstrip())
        return not first_char % 4
    return True

def ends_with_semicolon(line):
    parts = line.split("#")
    if len(parts) > 1:
        return ends_with_semicolon(parts[0])
    else:
        return line.strip().endswith(";")

def has_two_spaces_before_comment(line):
    comment_start = line.find("#")
    if comment_start > 2:
        return line[comment_start-1] == " " and line[comment_start-2] == " "
    return True

def has_todo(line):
    parts = line.split("#")
    if len(parts) > 1:
        return parts[1].upper().find("TODO") > -1
    return False

def blank_lines(context_lines):
    line_p3, line_p2, line_p1 = context_lines
    return line_p3.strip() == '' and line_p2.strip() == '' and line_p1.strip() == ''

def has_too_many_spaces(line):
    line = line.strip()
    is_construction = line.startswith("class") or line.startswith("def")
    if is_construction:
        first_space = line.find(" ")
        return line[first_space+1] == " "
    return False

def is_camel_case(name):
    pattern = r"^[A-Z][a-z]+(?:[A-Z][a-z]+)*$"
    return bool(re.fullmatch(pattern, name))

def is_snake_case(name):
    pattern = r'^(__[a-z_][a-z0-9_]+__|__[a-z][a-z0-9_]*|_[a-z][a-z0-9_]*|[a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*)$'
    return bool(re.fullmatch(pattern, name))

def wong_class_name(line):
    line = line.lstrip()
    is_class = line.startswith("class")
    if is_class:
        class_name = get_class_name(line.lstrip())
        return not is_camel_case(class_name)
    return False

def wrong_function_name(line):
    line = line.lstrip()
    is_function = line.startswith("def")
    if is_function:
        function_name = get_function_name(line)
        return not is_snake_case(function_name)
    return False

def get_class_name(line):
    pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|:)'
    match = re.search(pattern, line)
    if match:
        return match.group(1)
    return None

def get_function_name(line):
    pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    match = re.search(pattern, line)
    if match:
        return match.group(1)
    return None

def validate_function_args(args, errors):
    for arg in args.args:
        if not is_snake_case(arg.arg):
            errors.append(f"Line {arg.lineno}: S010 Argument name {arg.arg} should be written in snake_case")
            break
    for arg in args.defaults:
        if not isinstance(arg, ast.Constant):
            errors.append(f"Line {arg.lineno}: S012 The default argument value is mutable")
            break

def print_tree_errors(errors, filepath):
    errors.sort()
    for error in errors:
        print(f"{filepath}: {error}")

def validate_variable(variables, errors):
    for var in variables:
        if isinstance(var, ast.Name):
            if not is_snake_case(var.id):
                errors.append(f"Line {var.lineno}: S011 Variable '{var.id}' in function should be written in snake_case")

def validate_function_body(body, errors):
    for element in body:
        if isinstance(element, ast.Assign):
            validate_variable(element.targets, errors) # S011

def validate_tree(tree, filepath):
    nodes = ast.iter_child_nodes(tree)
    errors = []
    for node in nodes:
        if isinstance(node, ast.FunctionDef):
            validate_function_args(node.args, errors)  # S010, S012
            validate_function_body(node.body, errors) # S011
        elif isinstance(node, ast.ClassDef):
            validate_tree(node, filepath)

    print_tree_errors(errors, filepath)

def process_file(filepath):
    with open(filepath, "r") as f:
        file_content = f.read()
        tree = ast.parse(file_content)

        f.seek(0)
        context_lines = deque(['', '', ''], maxlen=3)
        for i, line in enumerate(f):
            if line_too_long(line):
                print(f"{filepath}: Line {i + 1}: S001 Too long")
            if not has_correct_indentation(line):
                print(f"{filepath}: Line {i + 1}: S002 Indentation is not a multiple of four")
            if ends_with_semicolon(line):
                print(f"{filepath}: Line {i + 1}: S003 Unnecessary semicolon")
            if not has_two_spaces_before_comment(line):
                print(f"{filepath}: Line {i + 1}: S004 At least two spaces required before inline comments")
            if has_todo(line):
                print(f"{filepath}: Line {i + 1}: S005 TODO found")
            if i >= 3 and blank_lines(context_lines):
                print(f"{filepath}: Line {i + 1}: S006 More than two blank lines used before this line")
            context_lines.append(line.rstrip('\n'))

            # TODO move to validate_tree
            if has_too_many_spaces(line):
                is_class = line.lstrip().startswith("class")
                construction_name = is_class and "class" or "def"
                print(f"{filepath}: Line {i + 1}: S007 Too many spaces after {construction_name}")
            if wong_class_name(line):
                class_name = get_class_name(line.lstrip())
                print(f"{filepath}: Line {i + 1}: S008 Class name {class_name} should be written in CamelCase")
            if wrong_function_name(line):
                function_name = get_function_name(line.lstrip())
                print(f"{filepath}: Line {i + 1}: S009 Function name {function_name} should be written in snake_case")
        validate_tree(tree, filepath)


def get_files(filepath):
    files = [f for f in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, f))]
    files.sort()
    paths = [os.path.join(filepath, f) for f in files]
    return paths

def process_directory(filepath):
    files = get_files(filepath)
    for file in files:
        # TODO ignore nested directories for now
        if os.path.isfile(file):
            process_file(file)

def process_path(filepath):
    is_directory = os.path.isdir(filepath)
    if is_directory:
        process_directory(filepath)
    else:
        process_file(filepath)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filepath",
        type=str
    )
    args = parser.parse_args()
    process_path(args.filepath)

if __name__ == "__main__":
    main()

