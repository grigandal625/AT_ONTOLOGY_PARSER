from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from at_ontology_parser.base import OntologyBase
    from at_ontology_parser.parsing.parser import Parser


@dataclass(kw_only=True)
class Context:
    name: str | int
    data: Optional[Any] = field(default=None, repr=False)
    initiator: Optional["OntologyBase"] = field(default=None, repr=False)
    parent: Optional["Context"] = field(default=None, repr=False)
    parser: Optional["Parser"] = field(default=None, repr=False)

    def __post_init__(self):
        if self.parent is not None:
            self.parser = self.parent.parser

    @property
    def path(self):
        if self.parent:
            return self.parent.path + [self.name]
        return [self.name]

    def create_child(
        self,
        name: str | int,
        data: Optional[Any] = None,
        initiator: Optional["OntologyBase"] = None,
    ):
        return Context(name=name, data=data, initiator=initiator, parent=self)


class OntologyException(Exception):
    context: Context

    def __init__(self, *args, context: Context):
        super().__init__(*args)
        self.context = context

    def represent(self):
        return {
            "msg": str(self),
            "context": [p for p in self.context.path[1:] if isinstance(p, str) or isinstance(p, int)],
        }


class CheckConstrainException(OntologyException):
    pass


class LoadException(OntologyException):
    errors: List[str | Dict[str, Any]]

    def __init__(
        self,
        *args: object,
        context: "Context",
        errors: List[str | Dict[str, Any]],
    ) -> None:
        super().__init__(*args, context=context)
        self.errors = errors

    def __str__(self) -> str:
        result = super().__str__()
        if self.errors:
            result += f"\nErrors: {self.errors}"
        return result

    def represent(self):
        return {
            "msg": super().__str__(),
            "errors": self.errors,
            "context": [p for p in self.context.path[1:] if isinstance(p, str) or isinstance(p, int)],
        }
