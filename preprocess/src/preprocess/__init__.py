import fire
from pathlib import Path
import re

NUMBER_REGEX = re.compile(r"^(\d+)\s")
LABEL_REGEX = re.compile(r"^<([A-Za-z_]\w*)>\s*(.*)")
AT_LABEL_REGEX = re.compile(r"@([A-Za-z_]\w*)")


def read_file(file: Path) -> list[str]:
    with open(file, "r") as f:
        return f.readlines()


class Preprocess:

    def __init__(self):
        pass

    def _strip_lines(self):
        for line_num, line in enumerate(self.code):
            self.code[line_num] = line.strip()

    def _remove_empty_lines(self):
        self.code = list(filter(lambda line: len(line) != 0, self.code))

    def _upper(self):
        for idx, line in enumerate(self.code):
            parts = re.split(r'(".*?")', line)

            for i, part in enumerate(parts):
                if i % 2 == 0:  # outside quotes
                    parts[i] = part.upper()

            self.code[idx] = "".join(parts)

    def _collect_and_remove_labels(self):
        for line_num, line in enumerate(self.code):
            if (res := LABEL_REGEX.search(line)) is not None:
                label = res.group(1)

                if (orig_line_num := self.labels.get(label)) is not None:
                    raise RuntimeError(
                        f"Found duplicate label '{label}' at {self.file}:{line_num + 1} "
                        f"(originally declared at {self.file}:{orig_line_num + 1})"
                    )

                self.labels[label] = line_num
                self.code[line_num] = res.group(2)

    def _add_line_numbers(self):
        new_line_num = 0

        for line_num, line in enumerate(self.code):
            if (res := NUMBER_REGEX.search(line)) is not None:
                given_line_num = int(res.group(1))
                if given_line_num < new_line_num:
                    raise RuntimeError(
                        f"Found impossible line number '{given_line_num}' at "
                        f"{self.file}:{line_num + 1}: Current renumbering at "
                        f"{new_line_num} which is greater than {given_line_num}."
                    )
                new_line_num = given_line_num + 1
                continue

            self.code[line_num] = f"{new_line_num} {line}"
            new_line_num += 1

        for label, orig_idx in list(self.labels.items()):
            if (res := NUMBER_REGEX.search(self.code[orig_idx])) is None:
                raise RuntimeError(
                    f"No line number found at {self.file}:{orig_idx + 1} "
                    "after addition of line numbers"
                )
            self.labels[label] = int(res.group(1))

    def _substitute_labels(self):
        for line_num, line in enumerate(self.code):

            def repl(match, file=self.file):
                label = match.group(1)
                if (label_line_num := self.labels.get(label)) is None:
                    raise RuntimeError(
                        f"Undeclared label '{label}' used at {file}:{line_num + 1}."
                    )
                return str(label_line_num)

            # split on quoted strings so we don't accidentally replace inside
            # a string literal the split keeps the quotes in the odd-indexed
            # parts
            line_parts = re.split(r'(".*?")', line)
            changed = False
            for i, part in enumerate(line_parts):
                # not in quotes
                if i % 2 == 0:
                    new_part, n = AT_LABEL_REGEX.subn(repl, part)
                    if n:
                        changed = True
                        line_parts[i] = new_part
            if changed:
                self.code[line_num] = "".join(line_parts)

    def _print(self):
        for line in self.code:
            print(line.strip())
        print()

    def run(self, file: Path, verbose: bool = False):
        """
        Preprocesses a set of files into a single, usable, basic program.

        Allows for usage of <labels> at the start of lines and @labels to sub in
        the correct line number.

        Automatically adds line numbers but supports manual line numbering.
        """
        self.file = file
        self.code = read_file(file)
        self.labels: dict[str, int] = {}

        if verbose:
            print("-- original --")
            self._print()

        ## passes
        # strip
        self._strip_lines()
        if verbose:
            print("-- after stripping lines --")
            self._print()

        # remove empty
        self._remove_empty_lines()
        if verbose:
            print("-- after removing empty lines --")
            self._print()

        # upper
        self._upper()
        if verbose:
            print("-- after uppercasing --")
            self._print()

        # label removal
        self._collect_and_remove_labels()
        if verbose:
            print("-- after label collection and removal --")
            self._print()

        # line numbers
        self._add_line_numbers()
        if verbose:
            print("-- after adding line numbers --")
            self._print()

        # substitute labels anywhere @label appears (outside strings)
        self._substitute_labels()
        if verbose:
            print("-- after substituting labels --")
            self._print()

        if verbose:
            print("-- final output --")
        self._print()


def main() -> None:
    fire.Fire(Preprocess().run)
