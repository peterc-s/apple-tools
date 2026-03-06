import os
import re
from pathlib import Path
from typing import Optional

import fire

NUMBER_REGEX = re.compile(r"^(\d+)\s")
LABEL_REGEX = re.compile(r"^<([A-Za-z_]\w*)>\s*(.*)")
AT_LABEL_REGEX = re.compile(r"@([A-Za-z_]\w*)")
INCLUDE_REGEX = re.compile(r"^#INCLUDE\s\"([A-Za-z\d_./-]*)\"")
ENTRY_REGEX = re.compile(r":ENTRY:\s*")


def read_file(file: Path) -> list[str]:
    with open(file, "r") as f:
        return f.readlines()


class Preprocess:
    def __init__(self):
        pass

    def _upper(self):
        for line_num, line in enumerate(self.code):
            parts = re.split(r'(".*?")', line)

            for i, part in enumerate(parts):
                if i % 2 == 0:  # outside quotes
                    parts[i] = part.upper()

            self.code[line_num] = "".join(parts)

    def _remove_remarks(self):
        new_code = []

        for _, line in enumerate(self.code):
            parts = re.split(r'(".*?")', line)
            remark_found = False

            for i, part in enumerate(parts):
                if i % 2 == 0 and "REM" in part:  # remark found outside quotes
                    remark_found = True

            if not remark_found:
                new_code.append(line)

        self.code = new_code

    def _mark_entry_point(self):
        entry_count = 0
        entry_line_index = None

        for i, line in enumerate(self.code):
            # only consider executable lines
            if INCLUDE_REGEX.search(line):
                continue
            if len(line.strip()) == 0:
                continue

            if ENTRY_REGEX.search(line):
                entry_count += 1
                entry_line_index = i

        if entry_count > 1:
            raise RuntimeError(
                "Multiple :ENTRY: definitions found in main file.",
            )

        # if entry exists, ensure it's only one and properly marked
        if entry_count == 1:
            # normalize by ensuring marker is present
            self.entry_original_index = entry_line_index
            return

        # otherwise inject entry marker to first executable line
        for i, line in enumerate(self.code):
            if INCLUDE_REGEX.search(line):
                continue
            if len(line.strip()) == 0:
                continue

            self.code[i] = ":ENTRY: " + line
            self.entry_original_index = i
            break

        # isn't python great
        if not hasattr(self, "entry_original_index"):
            raise RuntimeError(
                "Could not find executable entry point to mark :ENTRY:.",
            )

    def _handle_includes(self) -> bool:
        include_found = False
        new_code = []

        for line in self.code:
            if (res := INCLUDE_REGEX.search(line)) is not None:
                include_found = True
                filename = res.group(1)
                included_lines = read_file(os.path.dirname(self.file) / Path(filename))
                new_code.extend(included_lines)
            else:
                new_code.append(line)

        self.code = new_code
        return include_found

    def _strip_lines(self):
        for line_num, line in enumerate(self.code):
            self.code[line_num] = line.strip()

    def _remove_empty_lines(self):
        self.code = list(filter(lambda line: len(line) != 0, self.code))

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

    def _resolve_entry_and_goto(self):
        entry_indices = []

        for i, line in enumerate(self.code):
            if ENTRY_REGEX.search(line):
                entry_indices.append(i)

        if len(entry_indices) > 1:
            raise RuntimeError(
                "Multiple :ENTRY: markers found after preprocessing.",
            )

        if len(entry_indices) == 0:
            raise RuntimeError(
                "No :ENTRY: marker found after preprocessing.",
            )

        entry_line_index = entry_indices[0]

        # remove :ENTRY:
        self.code[entry_line_index] = ENTRY_REGEX.sub(
            "", self.code[entry_line_index]
        ).strip()

        if entry_line_index != 0:
            self.code.insert(0, f"0 GOTO {entry_line_index + 1}")

            # increment label line numbers
            for label, line_num in self.labels.items():
                self.labels[label] = line_num + 1

    def _substitute_labels(self):
        for line_num, line in enumerate(self.code):

            def repl(match, file=self.file):
                label = match.group(1)
                if (label_line_num := self.labels.get(label)) is None:
                    raise RuntimeError(
                        f"Undeclared label '{label}' used at {file}:{line_num + 1}."
                    )
                return str(label_line_num)

            # handling for string literals
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

    def run(
        self,
        file: Path,
        out: Optional[Path] = None,
        verbose: bool = False,
    ):
        """
        Preprocesses a set of files into a single, usable, basic program.

        Allows for usage of <labels> at the start of lines and @labels to sub in
        the correct line number.

        Automatically adds line numbers but supports manual line numbering
        (though I'd recommend against it).

        Has support for including other files, however all files must be in
        a flat directory structure or hack around the project path.

        For example:
        .
        |- main.bas
        |- lib/
           |- lib.bas
           |- lib2.bas

        If `lib.bas` had `#INCLUDE "lib2.bas"`, this would not work if we
        passed `main.bas` to the preprocessor. It would instead need to be
        `#INCLUDE "lib/lib2.bas"`.

        If you get an awful error, you are probably using the preprocessor
        in a way that it shouldn't be.

        Args:
            file: The main file to run the preprocessor on.
            out: The file to write the output too. Defaults to stdout.
            verbose: Print after each pass of preprocessing.
        """
        self.file = file
        self.code = read_file(file)
        self.labels: dict[str, int] = {}

        if verbose:
            print("-- original --")
            self._print()

        ## passes
        # upper ready for REM removal
        self._upper()
        if verbose:
            print("-- after uppercasing --")
            self._print()

        # hacky but remove remarks once first so that the entrypoint is
        # properly marked
        self._remove_remarks()
        if verbose:
            print("-- after removing remarks --")
            self._print()

        # mark the entry point
        self._mark_entry_point()
        if verbose:
            print("-- after marking entry --")
            self._print()

        # include resolving loop
        includes_found = True
        while includes_found:
            # upper
            self._upper()
            if verbose:
                print("-- after uppercasing --")
                self._print()

            # includes
            includes_found = self._handle_includes()
            if verbose:
                print("-- after includes --")
                self._print()

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

        self._remove_remarks()
        if verbose:
            print("-- after removing remarks --")
            self._print()

        # resolve entry + add goto jump
        self._resolve_entry_and_goto()
        if verbose:
            print("-- after resolving entry + goto injection --")
            self._print()

        # label removal (also stores labels)
        self._collect_and_remove_labels()
        if verbose:
            print("-- after label collection and removal --")
            self._print()

        # line numbers (updates labels if needed)
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

        if out is not None:
            if verbose:
                self._print()

            with open(out, "w") as f:
                f.write("\n".join(self.code))
        else:
            self._print()


def main() -> None:
    fire.Fire(Preprocess().run)
