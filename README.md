# SAT Sudoku Solver

A small learning project that encodes Sudoku as CNF and solves it with **DPLL** and **CDCL**. Not heavily optimized.

## Requirements

- Python 3.10+

## Sudoku solver (`sudoku.py`)

Run puzzles from `tests/` with both solvers:

```bash
python sudoku.py
```

### Choose tests

```bash
# one puzzle by name
python sudoku.py hard1

# multiple puzzles
python sudoku.py hard1 hard3

# by file path
python sudoku.py tests/hard2.txt
```

With no positional arguments, all `tests/*.txt` files are run in sorted order.

### Options

```bash
python sudoku.py hard1 --seed 42 --time-limit 30
```

| Option | Default | Description |
|--------|---------|-------------|
| `tests` | all | Puzzle name(s) (`hard1`) or path(s) |
| `--seed` | `123` | Random seed for variable selection |
| `--time-limit` | `60` | Per-solver time limit in seconds |

Each puzzle prints the grid, then DPLL and CDCL results. On timeout, the solver prints `Timeout` and moves on.

### Puzzle file format

Place `.txt` files in `tests/`. Example:

```
# 9x9 sudoku (digits 1-9, . for empty)
.......1.
4........
.2.......
...5..4..
..8..3...
.1..9....
3..4.....
.5.1.....
...8.6...
```

- One row per line, square grid (9 lines for standard Sudoku)
- `.` or `0` for empty cells
- Lines starting with `#` are comments
- Spaces and `|` are ignored

## Other entry points

```bash
python dpll.py    # small CNF examples
python cdcl.py    # CDCL unit tests
```
