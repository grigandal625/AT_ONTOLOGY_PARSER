from typing import Dict

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import VertexType
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.instancable import InstancableModel


class VertexTypeModel(InstancableModel):
    def get_preliminary_object(self, data, *, context, owner):
        result = VertexType(**data)
        result.owner = owner
        return result


class VertexTypes(OntoRootModel[Dict[str, VertexTypeModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, OntologyBase]:
        return {
            key: vertex_type.to_internal(context=context.create_child(key, data=vertex_type), owner=owner, name=key)
            for key, vertex_type in self.root.items()
        }
