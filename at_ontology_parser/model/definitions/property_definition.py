from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional
from typing import TYPE_CHECKING

from at_ontology_parser.base import Definition

if TYPE_CHECKING:
    from at_ontology_parser.reference import OntologyReference
    from at_ontology_parser.model.types.data_type import DataType


@dataclass(kw_only=True)
class PropertyDefinition(Definition):
    type: Optional["OntologyReference[DataType]"] = field(default=None)
    required: Optional[bool] = field(default=False)
    default: Optional[Any] = field(default=None, repr=False)
    allows_multiple: Optional[bool] = field(default=True)
    min_assignments: Optional[int] = field(default=None)
    max_assignments: Optional[int] = field(default=None)

    @property
    def _including_empty_fields(self):
        return ["default"]
