from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from at_ontology_parser.base import Derivable

if TYPE_CHECKING:
    from at_ontology_parser.model.definitions.constraint_definition import ConstraintDefinition


@dataclass(kw_only=True)
class DataType(Derivable):
    constraints: Optional[List["ConstraintDefinition"]] = field(default_factory=list)
    object_schema: Optional[dict | str] = field(default=None)
    object_schema_resolved: Optional[str] = field(default=None, init=False, repr=False)

    @property
    def object_schema_ref_used(self) -> bool:
        return self.object_schema_resolved is not self.object_schema
