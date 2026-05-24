from dataclasses import dataclass, field
from enum import Enum, auto

class Operator(Enum):
    VAR = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    IMP = auto()
    IFF = auto()


@dataclass(frozen=True, slots=True)
class Formula:
    op: Operator
    operands: tuple["Formula", ...] = field(default_factory=tuple)
    var: str | None = None

    def __post_init__(self):
        if self.op == Operator.VAR:
            if self.var is None:
                raise ValueError("Variable is required for VAR operator")
            if len(self.operands) > 0:
                raise ValueError("VAR operator does not take operands")
        elif self.op == Operator.NOT:
            if len(self.operands) != 1:
                raise ValueError("NOT operator requires exactly one operand")
        elif self.op == Operator.IMP:
            if len(self.operands) != 2:
                raise ValueError("Implication operator requires exactly two operands")
        else:
            if len(self.operands) < 2:
                raise ValueError("Binary operator requires at least two operands")

    @staticmethod
    def variable(name: str) -> "Formula":
        return Formula(Operator.VAR, var=name)

    @property
    def is_literal(self) -> bool:
        return self.op == Operator.VAR or (self.op == Operator.NOT and self.operands[0].is_literal)

    @property
    def is_variable(self) -> bool:
        return self.op == Operator.VAR

    @property
    def variables(self) -> set[str]:
        if self.op == Operator.VAR:
            return {self.var}
        elif self.op == Operator.NOT:
            return self.operands[0].variables
        else:
            return set.union(*[op.variables for op in self.operands])

    def __repr__(self) -> str:
        if self.op == Operator.VAR:
            return self.var
        elif self.op == Operator.NOT:
            return f"NOT({self.operands[0]})"
        elif self.op == Operator.AND:
            return f"AND({', '.join(repr(op) for op in self.operands)})"
        elif self.op == Operator.OR:
            return f"OR({', '.join(repr(op) for op in self.operands)})"
        elif self.op == Operator.XOR:
            return f"XOR({', '.join(repr(op) for op in self.operands)})"
        elif self.op == Operator.IMP:
            return f"IMP({self.operands[0]}, {self.operands[1]})"
        elif self.op == Operator.IFF:
            return f"IFF({', '.join(repr(op) for op in self.operands)})"

    def __invert__(self) -> "Formula":
        return self.operands[0] if self.op == Operator.NOT else Formula(Operator.NOT, (self,))

    def __commutative_binary_operator(self, op: Operator, other: "Formula") -> "Formula":
        left = [self] if self.op == op else [*self.operands]
        right = [other] if other.op == op else [*other.operands]
        return Formula(op, (*left, *right))

    def __and__(self, other: "Formula") -> "Formula":
        return self.__commutative_binary_operator(Operator.AND, other)

    def __or__(self, other: "Formula") -> "Formula":
        return self.__commutative_binary_operator(Operator.OR, other)

    def __xor__(self, other: "Formula") -> "Formula":
        return self.__commutative_binary_operator(Operator.XOR, other)

    def iff(self, other: "Formula") -> "Formula":
        return self.__commutative_binary_operator(Operator.IFF, other)

    def imp(self, other: "Formula") -> "Formula":
        return Formula(Operator.IMP, (self, other))

    def eval(self, assignment: dict[str, bool]) -> bool | None:
        if self.op == Operator.VAR:
            return assignment.get(self.var, None)
        elif self.op == Operator.NOT:
            result = self.operands[0].eval(assignment)
            if result is None:
                return None
            return not result
        elif self.op == Operator.AND:
            results = [op.eval(assignment) for op in self.operands]
            if False in results:
                return False
            elif None in results:
                return None
            return True
        elif self.op == Operator.OR:
            results = [op.eval(assignment) for op in self.operands]
            if True in results:
                return True
            elif None in results:
                return None
            return False
        elif self.op == Operator.XOR:
            results = [op.eval(assignment) for op in self.operands]
            if None in results:
                return None
            return sum(results) % 2 == 1
        elif self.op == Operator.IMP:
            left = self.operands[0].eval(assignment)
            right = self.operands[1].eval(assignment)
            if left is False or right is True:
                return True
            if left is True and right is False:
                return False
            return None
        elif self.op == Operator.IFF:
            results = [op.eval(assignment) for op in self.operands]
            if None in results:
                return None
            return results.count(False) % 2 == 0


def test():
    a = Formula.variable("a")
    b = Formula.variable("b")

    c = a.imp(b)
    assign = {"a": True}
    print(c.eval(assign))
    assign = {"a": False}
    print(c.eval(assign))
    assign = {"b": True}
    print(c.eval(assign))
    assign = {"b": False}
    print(c.eval(assign))
    assign = {"a": True, "b": True}
    print(c.eval(assign))
    assign = {"a": True, "b": False}
    print(c.eval(assign))
    assign = {"a": False, "b": True}
    print(c.eval(assign))
    assign = {"a": False, "b": False}
    print(c.eval(assign))

if __name__ == "__main__":
    test()