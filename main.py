import os
import argparse
from collections import deque

flags = {
    "S001": False,
    "S002": False,
    "S003": False,
    "S004": False,
    "S005": False,
    "S006": False,
}

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

def process_file(filepath):
    with open(filepath, "r") as f:
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
            reset_warnings()
            process_file(file)

def process_path(filepath):
    is_directory = os.path.isdir(filepath)
    if is_directory:
        process_directory(filepath)
    else:
        process_file(filepath)

def reset_warnings():
    for key in flags:
        flags[key] = False


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

