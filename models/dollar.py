import json
from typing import Union

from pydantic import BaseModel


class Dollar(BaseModel):
    value: float

    def __init__(self, value: Union[float, int, str]):
        super().__init__(value=float(value))

    def __str__(self) -> str:
        return f"${self.value:,.0f}"

    def __float__(self) -> float:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()

    def to_json(self) -> float:
        return self.value

    def model_dump_json(self) -> float:
        return self.value

    def __json__(self):
        return float(self.value)

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.value / other
        raise TypeError(f"unsupported operand type(s) for /: 'Dollar' and '{type(other).__name__}'")


class DollarEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Dollar):
            return float(obj.value)
        return super().default(obj)