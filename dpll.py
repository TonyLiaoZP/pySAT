import pdb
from logic import Formula
from cnf import CNF, Clause
from utils import cnf_from_int_clauses, set_random_seed

import random
from itertools import product


class DPLL:
    @staticmethod
    def solve(cnf: CNF, assignment: dict[str, bool] | None = None) -> tuple[bool, dict[str, bool] | None]:
        assignment = assignment or {}
        bakup = assignment.copy()
        if (sat := cnf.eval(assignment)) is not None:
            return sat, assignment
        DPLL.propagate(cnf, assignment)
        if (sat := cnf.eval(assignment)) is not None:
            return sat, assignment

        var = DPLL.select_variable(cnf, assignment)

        assignment[var] = True
        sat, solution = DPLL.solve(cnf, assignment)
        if sat:
            return sat, solution
        assignment = bakup.copy()
        assignment[var] = False
        sat, solution = DPLL.solve(cnf, assignment)
        if sat:
            return sat, solution
        return False, bakup

    @staticmethod
    def propagate(cnf: CNF, assignment: dict[str, bool]):
        remains = {c: len(c.variables - set(assignment.keys())) for c in cnf.clauses}
        unit_clauses = [c for c in remains if remains[c] == 1]
        while len(unit_clauses) > 0:
            clause = unit_clauses.pop(0)
            if remains[clause] == 0 or clause.eval(assignment) is not None:
                continue
            var = (set(clause.variables )- set(assignment.keys())).pop()
            val = clause.polarity(var)
            assignment[var] = val
            for c in cnf.variables[var]:
                if c in remains:
                    remains[c] -= 1
                    if remains[c] == 1:
                        unit_clauses.append(c)

    @staticmethod
    def select_variable(cnf: CNF, assignment: dict[str, bool]) -> str:
        return random.choice(sorted(set(cnf.variables.keys()) - set(assignment.keys())))        





def test(clauses: list[list[int]]):
    cnf = cnf_from_int_clauses(clauses)
    n_vars = max(abs(n) for clause in clauses for n in clause)

    sat, solution = DPLL.solve(cnf)
    print(f"Satisfiable: {sat}")
    if sat:
        for i in range(1, n_vars + 1):
            print(f"  x{i} = {solution.get(f'x{i}')}")
        assert cnf.eval(solution) is True
    else:
        assert not any(
            cnf.eval({f"x{i}": v for i, v in enumerate(vals, 1)})
            for vals in product([False, True], repeat=n_vars)
        )
    print("Result verified")


if __name__ == "__main__":
    seed = set_random_seed()
    print(f"Random seed: {seed}")
    print("Test 1:")
    test([
        [1, 2],
        [-1, 3],
        [-2, -3],
        [3, 4],
        [-3, 5],
        [-4, -5],
        [1, -4],
        [2, -5],
        [-1, 2, 5],
        [-2, 3, 4],
    ])
    print()
    print("Test 2:")
    test([
        [1, 2, 3],
        [-1, 4],
        [-2, 5],
        [-3, -4],
        [-4, 5],
        [1, -5],
        [-2, 4],
    ])
