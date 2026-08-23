from dataclasses import dataclass
from operator import eq, ne, lt, le, gt, ge

_OPERATORS={"eq":eq,"ne":ne,"lt":lt,"le":le,"gt":gt,"ge":ge}

@dataclass(frozen=True, slots=True)
class ActionPrecondition:
    variable: str
    expected: object
    operator: str = "eq"

    def evaluate(self, state):
        actual = getattr(state, "get", lambda k,d=None: getattr(state,"values",state).get(k,d))(self.variable)
        try: return _OPERATORS[self.operator](actual,self.expected)
        except KeyError: raise ValueError(f"unsupported operator: {self.operator}")
