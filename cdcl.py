from cnf import CNF, Clause
from logic import Formula, Operator
from utils import cnf_from_int_clauses, set_random_seed

import random
import heapq
import pdb

class CDCL:
    def __init__(self, cnf: CNF):
        self.cnf = cnf
        self.assignments = {}
        self.level = 0
        self.decisions: list[str] = [] # decision variables
        self.propagations: list[tuple[int, dict[str, tuple[Clause, int]]]] = [] # level, propagations[var] = (clause, order)
        
        self.remains = {c: len(c.variables) for c in self.cnf.clauses}
        self.variable_levels = {}
        self.name2var = {name: self.cnf.get_variable(name) for name in self.cnf.variables.keys()}

    def solve(self) -> tuple[bool, dict[str, bool] | None]:
        while True:
            self.propagate()
            sat, conflict = self.check_sat()
            if sat:
                return True, self.assignments
            elif sat is not None:
                # pdb.set_trace()
                # if len(self.cnf.clauses) % 1000 == 0:
                #     print(len(self.cnf.clauses), self.level, len(self.propagations[0][1]))
                if self.level == 0:
                    return False, None
                clause, uip = self.learn_clause(conflict)
                self.backtrack(clause, uip)
                self.cnf.add_clause(clause)
                self.remains[clause] = len(clause.variables - set(self.assignments.keys()))
            else:
                self.decide()

    def check_sat(self) -> tuple[bool | None, Clause | None]:
        """
        return sat, conflict if unsat
        sat: all clauses are satisfied, None if unsure
        conflict: a clause is unsatisfied, None if not unsat
        """
        unsure = False
        for clause in self.cnf.clauses:
            sat = clause.eval(self.assignments)
            if sat is False:
                return False, clause
            elif sat is None:
                unsure = True
        return None if unsure else True, None

    def propagate(self) -> None:
        unit_clauses = [c for c in self.cnf.clauses if self.remains[c] == 1]
        propagates = {}
        order = 1
        while len(unit_clauses) > 0:
            clause = unit_clauses.pop(0)
            if self.remains[clause] == 0 or clause.eval(self.assignments) is not None:
                continue
            var = (set(clause.variables) - set(self.assignments.keys())).pop()
            val = clause.polarity(var)
            self.assignments[var] = val
            propagates[var] = (clause, order)
            self.variable_levels[var] = self.level
            order += 1
            for c in self.cnf.variables[var]:
                if c in self.remains:
                    self.remains[c] -= 1
                    if self.remains[c] == 1:
                        unit_clauses.append(c)
        if len(self.propagations) > 0 and self.propagations[-1][0] == self.level:
            self.propagations[-1][1].update(propagates)
        else:
            self.propagations.append((self.level, propagates))
    
    def decide(self) -> None:
        self.level += 1
        self.decisions.append(self.select_variable())
        self.assignments[self.decisions[-1]] = True
        self.variable_levels[self.decisions[-1]] = self.level
        for c in self.cnf.variables[self.decisions[-1]]:
            if c in self.remains:
                self.remains[c] -= 1
    
    def select_variable(self) -> str:
        
        if len(set(self.cnf.variables.keys()) - set(self.assignments.keys())) == 0:
            raise ValueError("No variables to decide")
        return random.choice(sorted(set(self.cnf.variables.keys()) - set(self.assignments.keys())))
        # return sorted(set(self.cnf.variables.keys()) - set(self.assignments.keys()))[0]

    def learn_clause(self, conflict: Clause) -> tuple[Clause, str]:
        _, propagations = self.propagations[-1]
        decision = self.decisions[-1]

        # find 1-UIP
        U = set(conflict.variables) & set(propagations.keys())
        queue = [(-propagations[var][1], var) for var in U]
        heapq.heapify(queue)
        visited = set()
        while len(queue) > 1:
            _, var = heapq.heappop(queue)
            if var in visited:
                continue
            visited.add(var)
            if var not in propagations:
                continue
            U.remove(var)
            clause = propagations[var][0]
            for v in clause.variables:
                if v == var:
                    continue
                if v in propagations and v not in visited:
                    heapq.heappush(queue, (-propagations[v][1] if v != decision else 0, v))
                U.add(v)
        
        _, uip = heapq.heappop(queue)
        
        # learn clause
        level0_vars = set() if self.propagations[0][0] != 0 else set(self.propagations[0][1].keys())
        cut_edges = U - level0_vars
        
        literals = [~self.name2var[var] if self.assignments[var] else self.name2var[var] for var in sorted(cut_edges)]
        return Clause(literals=tuple(literals)), uip

    def backtrack(self, clause: Clause, uip: str):
        target_level = 0
        for var in clause.variables:
            if var == uip:
                continue
            target_level = max(target_level, self.variable_levels[var] - 1)

        while len(self.decisions) > target_level:
            var = self.decisions.pop()
            del self.assignments[var]
            del self.variable_levels[var]
            for c in self.cnf.variables[var]:
                if c in self.remains:
                    self.remains[c] += 1
        
        while len(self.propagations) and self.propagations[-1][0] > target_level:
            _, props = self.propagations.pop()
            for var, (clause, order) in props.items():
                del self.assignments[var]
                del self.variable_levels[var]
                for c in self.cnf.variables[var]:
                    if c in self.remains:
                        self.remains[c] += 1
        
        self.level = target_level

def print_propagations(propagations: list[tuple[int, dict[str, tuple[Clause, int]]]]):
    for level, props in propagations:
        print(f"level {level}:")
        for var, (clause, order) in props.items():
            print(f"  {var}: {clause.to_string()} (order: {order})")

def test_learn():
    cnf = cnf_from_int_clauses([
        [-1, -2], [-1, 3], [-3, -4], [2, 4, 5], [-5, 6, -7], [2, 7, 8],
        [-8, -9], [-8, 10], [9, -10, 11], [-10, -12], [-11, 12]
    ])
    xs = {i: cnf.get_variable(f"x{i}") for i in range(1, 13)}

    cdcl = CDCL(cnf)
    cdcl.level += 1
    cdcl.decisions.append(xs[1])
    cdcl.assignments[xs[1].var] = True
    for c in cnf.variables[xs[1].var]:
        if c in cdcl.remains:
            cdcl.remains[c] -= 1
    cdcl.propagate()
    print_propagations(cdcl.propagations)

    cdcl.level += 1
    cdcl.decisions.append(xs[6])
    cdcl.assignments[xs[6].var] = False
    for c in cnf.variables[xs[6].var]:
        if c in cdcl.remains:
            cdcl.remains[c] -= 1
    cdcl.propagate()
    print_propagations(cdcl.propagations)

    sat, conflict = cdcl.check_sat()
    print(f"sat: {sat}")
    if conflict is not None:
        print(f"conflict: {conflict.to_string()}")
    else:
        print("no conflict")

    clause, uip = cdcl.learn_clause(conflict)
    print(f"learned clause: {clause.to_string()}")
    print(f"UIP: {uip}")

def test_solve():
    cnf = cnf_from_int_clauses([
        [-1, -2], [-1, 3], [-3, -4], [2, 4, 5], [-5, 6, -7], [2, 7, 8],
        [-8, -9], [-8, 10], [9, -10, 11], [-10, -12], [-11, 12]
    ])
    cdcl = CDCL(cnf)
    sat, assignments = cdcl.solve()
    print(f"sat: {sat}")
    if sat:
        for var, val in assignments.items():
            print(f"{var}: {val}")
        print(f"solution: {cnf.eval(assignments)}")
    else:
        print("no solution")

if __name__ == "__main__":
    seed = set_random_seed()
    print(f"Random seed: {seed}")
    test_learn()
    test_solve()

                
