from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import TYPE_CHECKING

from at_ontology_parser.base import OntologyEntity

if TYPE_CHECKING:
    from at_ontology_parser.model.types import DataType, VertexType, RelationshipType
    from at_ontology_parser.model.definitions import ImportDefinition


@dataclass(kw_only=True)
class OntologyModel(OntologyEntity):
    imports: List["ImportDefinition"] = field(default_factory=list, repr=False)
    data_types: Dict[str, "DataType"] = field(default_factory=dict, repr=False)
    vertex_types: Dict[str, "VertexType"] = field(default_factory=dict, repr=False)
    relationship_types: Dict[str, "RelationshipType"] = field(default_factory=dict, repr=False)
