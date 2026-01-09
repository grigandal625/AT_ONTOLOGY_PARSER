from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

from at_ontology_parser.base import OntologyEntity

if TYPE_CHECKING:
    from at_ontology_parser.model import ImportDefinition
    from at_ontology_parser.model.handler import OntologyModel
    from at_ontology_parser.parsing.parser import ModelModule
    from at_ontology_parser.ontology.instances.vertex import Vertex
    from at_ontology_parser.ontology.instances.relationship import Relationship


@dataclass(kw_only=True)
class Ontology(OntologyEntity):
    imports: List["ImportDefinition"] = field(default_factory=list, repr=False)
    vertices: Dict[str, "Vertex"] = field(default_factory=dict, repr=False)
    relationships: Dict[str, "Relationship"] = field(default_factory=dict, repr=False)

    _resolved_imports: Optional[List[Tuple["ImportDefinition", "OntologyModel", "ModelModule"]]] = field(
        init=False, default=None, repr=False
    )

    def get_resolved_import(
        self, import_definition: "ImportDefinition", with_module=False
    ) -> Optional["OntologyModel" | Tuple["OntologyModel", "ModelModule"]]:
        for resolved_import in self._resolved_imports:
            if resolved_import[0] is import_definition:
                if with_module:
                    return resolved_import[1], resolved_import[2]
                else:
                    return resolved_import[1]

    def _to_repr(self, context, minify=True, exclude_name=True, with_restricted=False):
        result = super()._to_repr(context, minify, exclude_name, with_restricted=with_restricted)
        result["name"] = self.name

        return result
