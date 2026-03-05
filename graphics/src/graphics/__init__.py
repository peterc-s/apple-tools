from itertools import groupby
from os import stat
from pathlib import Path

import fire


class Graphics:
    def __init__(self):
        pass

    @staticmethod
    def _read_file(file: Path) -> list[str]:
        with open(file, "r") as f:
            return f.readlines()

    @staticmethod
    def _create_blank(
        resolution: tuple[int, int] = (60, 80),
    ) -> list[str]:
        return ["." * resolution[1] for _ in range(resolution[0])]

    @staticmethod
    def print(file: Path):
        """
        Print file to the screen.
        """
        screen = Graphics._read_file(file)
        for row in screen:
            print(row.strip())

    @staticmethod
    def new(
        file: Path,
        resolution: tuple[int, int] = (60, 80),
    ) -> None:
        """
        Create a blank file.
        """
        with open(file, "w") as f:
            f.writelines("\n".join(Graphics._create_blank(resolution)))

    @staticmethod
    def compile(file: Path) -> None:
        """
        Compile a file to Applesoft BASIC.
        """
        screen = Graphics._read_file(file)

        out = [
            "GR",  # enable graphics
            "COLOR=15",  # white
        ]

        row_groups = []
        for row in screen:
            row_groups.append(
                [(char, "".join(group)) for char, group in groupby(row.strip())]
            )

        for row_idx, row in enumerate(row_groups):
            col_idx = 0
            for group in row:
                if group[0] == "#":
                    out.append(
                        f"HLIN {col_idx},{col_idx + len(group[1]) - 1} AT {row_idx}"
                    )
                col_idx += len(group[1])

        print(
            "\n".join(
                [f"{(i + 1) * 10} {line}" for i, line in enumerate(out)],
            ),
        )


def main() -> None:
    fire.Fire(Graphics)
