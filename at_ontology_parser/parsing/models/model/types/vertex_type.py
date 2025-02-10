from typing import Dict

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import VertexType
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.instancable import InstancableModel
from at_ontology_parser.reference import OntologyReference


class VertexTypeModel(InstancableModel):
    def get_preliminary_object(self, data, *, context, owner):
        result = VertexType(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: VertexType, context: Context):
        if result.derived_from:
            result.derived_from = OntologyReference[VertexType](
                alias=self.derived_from, context=context.create_child("derived_from", self.derived_from, result)
            )
            result.derived_from.owner = result
        return super().insert_dependent_data(result, context)


class VertexTypes(OntoRootModel[Dict[str, VertexTypeModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, OntologyBase]:
        return {
            key: vertex_type.to_internal(context=context.create_child(key, data=vertex_type), owner=owner, name=key)
            for key, vertex_type in self.root.items()
        }
