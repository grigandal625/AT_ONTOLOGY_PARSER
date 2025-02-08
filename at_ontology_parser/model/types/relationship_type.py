from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from at_ontology_parser.base import Instancable


if TYPE_CHECKING:
    from at_ontology_parser.reference import OntologyReference
    from at_ontology_parser.model.types.vertex_type import VertexType


@dataclass(kw_only=True)
class RelationshipType(Instancable):
    valid_source_types: Optional[List["OntologyReference[VertexType]"]] = field(default_factory=list, repr=False)
    valid_target_types: Optional[List["OntologyReference[VertexType]"]] = field(default_factory=list, repr=False)
