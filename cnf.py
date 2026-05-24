from logic import Formula, Operator
from dataclasses import dataclass, field
from collections import defaultdict


def _literal_polarity(literal: Formula) -> tuple[str, bool]:
    if literal.op == Operator.VAR:
        return literal.var, True
    return literal.operands[0].var, False


@dataclass(frozen=True, slots=True)
class Clause:
    literals: tuple[Formula, ...] = field(default_factory=tuple)
    variables: frozenset[str] = field(default_factory=frozenset, init=False)
    _polarities: dict[str, bool] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self):
        assert all(lit.is_literal for lit in self.literals), "All literals must be variables or negated variables"
        object.__setattr__(self, "literals", tuple(self.literals))
        polarities = dict(_literal_polarity(lit) for lit in self.literals)
        object.__setattr__(self, "_polarities", polarities)
        object.__setattr__(self, "variables", frozenset(polarities))

    def polarity(self, var: str) -> bool:
        """Return True if var appears positively, False if negated."""
        return self._polarities[var]

    def eval(self, assignment: dict[str, bool]) -> bool:
        vals = [lit.eval(assignment) for lit in self.literals]
        if True in vals:
            return True
        return None if None in vals else False

    def to_string(self) -> str:
        return " ".join(f"{lit}" for lit in self.literals)

def _variable_index() ->defaultdict[str, list[Clause]]:
    return defaultdict(list)

@dataclass
class CNF:
    clauses: list[Clause] = field(default_factory=list)
    variables: dict[str, list[Clause]] = field(default_factory=_variable_index)
    clause_set: set[Clause] = field(default_factory=set)

    def __post_init__(self):
        self.clause_set = set(self.clauses)
        assert len(self.clause_set) == len(self.clauses), "Clauses must be unique"
        for clause in self.clauses:
            for var in clause.variables:
                self.variables[var].append(clause)

    def add_clause(self, clause: Clause):
        assert clause not in self.clause_set, "Clause already exists"
        self.clauses.append(clause)
        for var in clause.variables:
            self.variables[var].append(clause)
    
    def eval(self, assignment: dict[str, bool]) -> bool:
        vals = [clause.eval(assignment) for clause in self.clauses]
        if False in vals:
            return False
        return None if None in vals else True

    def get_variable(self, name: str) -> Formula:
        assert name in self.variables, "Variable not found"
        clause = self.variables[name][0]
        for lit in clause.literals:
            var = lit.operands[0] if lit.op == Operator.NOT else lit
            if var.var == name:
                return var
        raise ValueError(f"Variable {name} not found in clause {clause.to_string()}")

