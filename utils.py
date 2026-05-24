from logic import Formula
from cnf import CNF, Clause
import random
import time


def set_random_seed(seed: int | float | None = None) -> int | float:
    if seed is None:
        seed = time.time()
    random.seed(seed)
    return seed


def _int_to_literal(n: int, variables: dict[int, Formula]) -> Formula:
    i = abs(n)
    if i not in variables:
        variables[i] = Formula.variable(f"x{i}")
    lit = variables[i]
    return lit if n > 0 else ~lit


def cnf_from_int_clauses(clauses: list[list[int]]) -> CNF:
    variables: dict[int, Formula] = {}
    cnf = CNF()
    for clause in clauses:
        cnf.add_clause(Clause(literals=[_int_to_literal(n, variables) for n in clause]))
    return cnf