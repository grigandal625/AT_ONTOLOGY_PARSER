from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import TYPE_CHECKING

from at_ontology_parser.base import OntologyEntity

if TYPE_CHECKING:
    from at_ontology_parser.model import ImportDefinition
    from at_ontology_parser.ontology.instances.vertex import Vertex
    from at_ontology_parser.ontology.instances.relationship import Relationship


@dataclass(kw_only=True)
class Ontology(OntologyEntity):
    imports: List["ImportDefinition"] = field(default_factory=list, repr=False)
    vertices: Dict[str, "Vertex"] = field(default_factory=dict, repr=False)
    relationships: Dict[str, "Relationship"] = field(default_factory=dict, repr=False)
