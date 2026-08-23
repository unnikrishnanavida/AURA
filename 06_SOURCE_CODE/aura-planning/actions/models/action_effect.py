from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ActionEffect:
    variable: str
    value: object

    def apply(self, state):
        if hasattr(state, "with_value"):
            return state.with_value(self.variable, self.value)
        values = dict(getattr(state, "values", state))
        values[self.variable] = self.value
        return type(state)(values)
