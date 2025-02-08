import re
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import Literal
from typing import TYPE_CHECKING

from at_ontology_parser.base import Definition

if TYPE_CHECKING:
    from at_ontology_parser.exceptions import Context, CheckConstrainException


@dataclass(kw_only=True)
class ConstraintDefinition(Definition):
    name: str = field(init=False)
    args: Any

    def check(self, value: Any, context: "Context") -> bool:
        if self.check(value):
            return True
        raise CheckConstrainException(f"Bad value {value} for constraint {self.name} ({self.args})", context=context)

    def _check(self, value: Any) -> bool:
        raise NotImplementedError("Not implemented")

    def _to_repr(self, context: "Context", minify: bool = True, exclude_name: bool = True):
        return {self.name: self.args}


@dataclass(kw_only=True)
class LESS(ConstraintDefinition):
    name: Literal["less"] = field(init=False, default="less")
    args: int | float

    def _check(self, value: Any) -> bool:
        return value < self.args


@dataclass(kw_only=True)
class GRATER(ConstraintDefinition):
    name: Literal["grater"] = field(init=False, default="grater")
    args: int | float

    def _check(self, value: Any) -> bool:
        return value > self.args


@dataclass(kw_only=True)
class LESS_OR_EQUALS(ConstraintDefinition):
    name: Literal["less_or_equals"] = field(init=False, default="less_or_equals")
    args: int | float

    def _check(self, value: Any) -> bool:
        return value <= self.args


@dataclass(kw_only=True)
class GRATER_OR_EQUALS(ConstraintDefinition):
    name: Literal["grater_or_equals"] = field(init=False, default="grater_or_equals")
    args: int | float

    def _check(self, value: Any) -> bool:
        return value >= self.args


@dataclass(kw_only=True)
class EQUALS(ConstraintDefinition):
    name: Literal["not_equals"] = field(init=False, default="not_equals")
    args: Any

    def _check(self, value: Any) -> bool:
        return value == self.args


@dataclass(kw_only=True)
class NOT_EQUALS(ConstraintDefinition):
    name: Literal["not_equals"] = field(init=False, default="not_equals")
    args: Any

    def _check(self, value: Any) -> bool:
        return value != self.args


@dataclass(kw_only=True)
class INCLUDED(ConstraintDefinition):
    name: Literal["included"] = field(init=False, default="included")
    args: list | tuple | set | frozenset

    def _check(self, value: Any) -> bool:
        return value in self.args


@dataclass(kw_only=True)
class NOT_INCLUDED(ConstraintDefinition):
    name: Literal["not_included"] = field(init=False, default="not_included")
    args: list | tuple | set | frozenset

    def _check(self, value: Any) -> bool:
        return value not in self.args


@dataclass(kw_only=True)
class IN_RANGE(ConstraintDefinition):
    name: Literal["in_range"] = field(init=False, default="in_range")
    args: tuple[int | float, int | float]

    def _check(self, value: Any) -> bool:
        return self.args[0] <= value <= self.args[1]


@dataclass(kw_only=True)
class NOT_IN_RANGE(ConstraintDefinition):
    name: Literal["not_in_range"] = field(init=False, default="not_in_range")
    args: tuple[int | float, int | float]

    def _check(self, value: Any) -> bool:
        return not (self.args[0] <= value <= self.args[1])


@dataclass(kw_only=True)
class CONTAINS(ConstraintDefinition):
    name: Literal["contains"] = field(init=False, default="contains")
    args: Any

    def _check(self, value: Any) -> bool:
        return self.args in value


@dataclass(kw_only=True)
class NOT_CONTAINS(ConstraintDefinition):
    name: Literal["not_contains"] = field(init=False, default="not_contains")
    args: Any

    def _check(self, value: Any) -> bool:
        return self.args not in value


@dataclass(kw_only=True)
class STARTS_WITH(ConstraintDefinition):
    name: Literal["starts_with"] = field(init=False, default="starts_with")
    args: str

    def _check(self, value: str) -> bool:
        return value.startswith(self.args)


@dataclass(kw_only=True)
class ENDS_WITH(ConstraintDefinition):
    name: Literal["ends_with"] = field(init=False, default="ends_with")
    args: str

    def _check(self, value: str) -> bool:
        return value.endswith(self.args)


@dataclass(kw_only=True)
class MATCHES(ConstraintDefinition):
    name: Literal["matches"] = field(init=False, default="matches")
    args: str

    def _check(self, value: str) -> bool:
        return re.match(self.args, value) is not None


@dataclass(kw_only=True)
class NOT_MATCHES(ConstraintDefinition):
    name: Literal["not_matches"] = field(init=False, default="not_matches")
    args: str

    def _check(self, value: str) -> bool:
        return re.match(self.args, value) is None


@dataclass(kw_only=True)
class LENGTH(ConstraintDefinition):
    name: Literal["length"] = field(init=False, default="length")
    args: int

    def _check(self, value: Any) -> bool:
        return len(value) == self.args


@dataclass(kw_only=True)
class MIN_LENGTH(ConstraintDefinition):
    name: Literal["min_length"] = field(init=False, default="min_length")
    args: int

    def _check(self, value: Any) -> bool:
        return len(value) >= self.args


@dataclass(kw_only=True)
class MAX_LENGTH(ConstraintDefinition):
    name: Literal["max_length"] = field(init=False, default="max_length")
    args: int

    def _check(self, value: Any) -> bool:
        return len(value) <= self.args


class ONTOLOGY_CONSTRAINTS(Enum):
    less = LESS
    grater = GRATER
    less_or_equals = LESS_OR_EQUALS
    grater_or_equals = GRATER_OR_EQUALS
    equals = EQUALS
    not_equals = NOT_EQUALS
    included = INCLUDED
    not_included = NOT_INCLUDED
    in_range = IN_RANGE
    not_in_range = NOT_IN_RANGE
    contains = CONTAINS
    not_contains = NOT_CONTAINS
    starts_with = STARTS_WITH
    ends_with = ENDS_WITH
    matches = MATCHES
    not_matches = NOT_MATCHES
    length = LENGTH
    min_length = MIN_LENGTH
    max_length = MAX_LENGTH

    @classmethod
    def mapping(cls):
        return {constraint.name: constraint.value for constraint in cls}
