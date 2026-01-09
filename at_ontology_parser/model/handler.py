from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

from at_ontology_parser.base import OntologyEntity

if TYPE_CHECKING:
    from at_ontology_parser.model.types import DataType, VertexType, RelationshipType
    from at_ontology_parser.model.definitions import ImportDefinition
    from at_ontology_parser.parsing.parser import ModelModule


@dataclass(kw_only=True)
class OntologyModel(OntologyEntity):
    imports: List["ImportDefinition"] = field(default_factory=list, repr=False)
    data_types: Dict[str, "DataType"] = field(default_factory=dict, repr=False)
    vertex_types: Dict[str, "VertexType"] = field(default_factory=dict, repr=False)
    relationship_types: Dict[str, "RelationshipType"] = field(default_factory=dict, repr=False)
    schema_definitions: Optional[Dict[str, Any]] = field(default_factory=dict, repr=False)

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

    def _to_repr(self, context, minify=True, exclude_name=True):
        result = super()._to_repr(context, minify, exclude_name)
        result["name"] = self.name

        return result
