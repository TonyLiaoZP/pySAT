import argparse
import pdb
import time
import multiprocessing as mp
from dataclasses import dataclass, field
from pathlib import Path
from cnf import CNF, Clause
from logic import Formula
from itertools import combinations, product
from dpll import DPLL
from cdcl import CDCL
from utils import set_random_seed

SOLVER_TIME_LIMIT = 60.0
TESTS_DIR = Path(__file__).parent / "tests"


@dataclass
class Sudoku:
    clues: dict[tuple[int, int], int] = field(default_factory=dict)
    size: int = 9
    box_size: int = 3

    def __post_init__(self):
        for (row, col), value in self.clues.items():
            assert 0 < value <= self.size, "Clue must be between 0 and size"
            assert 0 < row <= self.size, "Row must be between 0 and size"
            assert 0 < col <= self.size, "Column must be between 0 and size"
        
        self.box_size = int(self.size ** 0.5)
        assert self.box_size * self.box_size == self.size, "Size must be a perfect square"
    
    def pretty_print(self, solution: dict[tuple[int, int], int] | None = None):
        if solution is None:
            solution = self.clues
        print("+" + "-" * (self.size * 2 + 5) + "+")
        for row in range(self.size):
            print("|", end="")
            for col in range(self.size):
                print(f" {solution.get((row+1, col+1), '.')}", end="")
                if col % 3 == 2:
                    print(" |", end="")
            print()
            if row % 3 == 2:
                print("+" + "-" * (self.size * 2 + 5) + "+")

    def to_cnf(self, with_helper: bool = True) -> CNF:
        variables = {}
        for i, j, k in product(range(1, self.size + 1), repeat=3):
            var = Formula.variable(f"x{i}{j}{k}")
            variables[(i, j, k)] = var

        cnf = CNF()

        # clues
        for (i, j), k in self.clues.items():
            cnf.add_clause(Clause(literals=[variables[(i, j, k)]]))

        # row constraints
        for i, k in product(range(1, self.size + 1), repeat=2):
            cnf.add_clause(Clause(literals=[variables[(i, j, k)] for j in range(1, self.size + 1)]))
            if with_helper:
                for j1, j2 in combinations(range(1, self.size + 1), 2):
                    cnf.add_clause(Clause(literals=[~(variables[(i, j1, k)]), ~(variables[(i, j2, k)])]))

        # column constraints
        for j, k in product(range(1, self.size + 1), repeat=2):
            cnf.add_clause(Clause(literals=[variables[(i, j, k)] for i in range(1, self.size + 1)]))
            if with_helper:
                for i1, i2 in combinations(range(1, self.size + 1), 2):
                    cnf.add_clause(Clause(literals=[~(variables[(i1, j, k)]), ~(variables[(i2, j, k)])]))

        # box constraints
        for bi, bj in product(range(1, self.size + 1, self.box_size), repeat=2):
            for k in range(1, self.size + 1):
                cnf.add_clause(Clause(literals=[variables[(bi + i, bj + j, k)] for i in range(self.box_size) for j in range(self.box_size)]))
                if with_helper:
                    for i1, i2 in combinations(range(self.box_size), 2):
                        for j1, j2 in combinations(range(self.box_size), 2):
                            cnf.add_clause(Clause(literals=[~(variables[(bi + i1, bj + j1, k)]), ~(variables[(bi + i2, bj + j2, k)])]))

        # cell constraints
        for i, j in product(range(1, self.size + 1), repeat=2):
            cnf.add_clause(Clause(literals=[variables[(i, j, k)] for k in range(1, self.size + 1)]))
            for k1, k2 in combinations(range(1, self.size + 1), 2):
                cnf.add_clause(Clause(literals=[~(variables[(i, j, k1)]), ~(variables[(i, j, k2)])]))

        return cnf


def load_sudoku(path: Path | str) -> Sudoku:
    lines: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = line.replace(" ", "").replace("|", "")
        lines.append(row)

    if not lines:
        raise ValueError(f"No puzzle grid found in {path}")

    size = len(lines)
    if any(len(row) != size for row in lines):
        raise ValueError(f"Puzzle in {path} must be a square grid")

    clues: dict[tuple[int, int], int] = {}
    for row, line in enumerate(lines, start=1):
        for col, ch in enumerate(line, start=1):
            if ch in ".0":
                continue
            if not ch.isdigit():
                raise ValueError(f"Invalid cell '{ch}' in {path}")
            clues[(row, col)] = int(ch)

    return Sudoku(clues=clues, size=size)


def from_cnf_solution(solution: dict[str, bool], size: int = 9) -> dict[tuple[int, int], int]:
    clues = {}
    for i, j in product(range(1, size + 1), repeat=2):
        for k in range(1, size + 1):
            if solution[f"x{i}{j}{k}"]:
                clues[(i, j)] = k
                break
    return clues


def _solve_dpll(clues: dict[tuple[int, int], int], size: int, seed: int | float) -> tuple[bool, dict[str, bool] | None]:
    set_random_seed(seed)
    sudoku = Sudoku(clues=clues, size=size)
    return DPLL.solve(sudoku.to_cnf())


def _solve_cdcl(clues: dict[tuple[int, int], int], size: int, seed: int | float) -> tuple[bool, dict[str, bool] | None]:
    set_random_seed(seed)
    sudoku = Sudoku(clues=clues, size=size)
    return CDCL(sudoku.to_cnf()).solve()


def _solver_worker(fn, args: tuple, queue: mp.Queue) -> None:
    try:
        queue.put(("ok", fn(*args)))
    except Exception as exc:
        queue.put(("err", exc))


def _run_with_timeout(fn, /, *args, timeout: float):
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    process = ctx.Process(target=_solver_worker, args=(fn, args, queue), daemon=True)
    process.start()
    process.join(timeout)
    timed_out = process.is_alive()
    if timed_out:
        process.terminate()
        process.join()
    try:
        if timed_out or queue.empty():
            return None, timed_out
        status, result = queue.get_nowait()
        if status == "err":
            raise result
        return result, False
    finally:
        queue.close()
        queue.join_thread()

def test_dpll(sudoku: Sudoku, time_limit: float = SOLVER_TIME_LIMIT, seed: int | float | None = None):
    print("--------------------------------")
    print("DPLL:")
    seed = seed if seed is not None else time.time()
    start = time.time()
    result, timed_out = _run_with_timeout(
        _solve_dpll, sudoku.clues, sudoku.size, seed, timeout=time_limit
    )
    elapsed = time.time() - start
    if timed_out:
        print(f"Timeout (limit: {time_limit}s, elapsed: {elapsed:.3f}s)")
        return
    sat, solution = result
    print(f"Time taken: {elapsed:.3f} seconds")
    if sat:
        clues = from_cnf_solution(solution)
        sudoku.pretty_print(clues)
    else:
        print("No solution found")


def test_cdcl(sudoku: Sudoku, time_limit: float = SOLVER_TIME_LIMIT, seed: int | float | None = None):
    print("--------------------------------")
    print("CDCL:")
    seed = seed if seed is not None else time.time()
    start = time.time()
    result, timed_out = _run_with_timeout(
        _solve_cdcl, sudoku.clues, sudoku.size, seed, timeout=time_limit
    )
    elapsed = time.time() - start
    if timed_out:
        print(f"Timeout (limit: {time_limit}s, elapsed: {elapsed:.3f}s)")
        return
    sat, solution = result
    print(f"Time taken: {elapsed:.3f} seconds")
    if sat:
        clues = from_cnf_solution(solution)
        sudoku.pretty_print(clues)
    else:
        print("No solution found")


def resolve_test_paths(names: list[str]) -> list[Path]:
    if not names:
        return sorted(TESTS_DIR.glob("*.txt"))

    paths: list[Path] = []
    for name in names:
        path = Path(name)
        if path.is_file():
            paths.append(path)
            continue
        stem = name.removesuffix(".txt")
        candidate = TESTS_DIR / f"{stem}.txt"
        if candidate.is_file():
            paths.append(candidate)
            continue
        raise SystemExit(f"Test not found: {name} (looked in {TESTS_DIR})")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve sudoku puzzles with DPLL and CDCL")
    parser.add_argument(
        "tests",
        nargs="*",
        help="test name(s) such as hard1, or path(s); default: all tests in tests/",
    )
    parser.add_argument("--seed", type=float, default=123, help="random seed for solvers")
    parser.add_argument(
        "--time-limit",
        type=float,
        default=SOLVER_TIME_LIMIT,
        help="solver time limit in seconds",
    )
    args = parser.parse_args()

    seed = set_random_seed(args.seed)
    print(f"Random seed: {seed}")

    test_files = resolve_test_paths(args.tests)
    if not test_files:
        raise SystemExit(f"No test files found in {TESTS_DIR}")

    for path in test_files:
        print(f"\n=== {path.name} ===")
        sudoku = load_sudoku(path)
        sudoku.pretty_print()
        test_dpll(sudoku, time_limit=args.time_limit, seed=seed)
        test_cdcl(sudoku, time_limit=args.time_limit, seed=seed)


if __name__ == "__main__":
    main()