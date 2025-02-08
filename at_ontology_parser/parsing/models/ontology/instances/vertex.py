from typing import Dict

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import VertexType
from at_ontology_parser.ontology.instances import Vertex
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.instance import InstanceModel
from at_ontology_parser.reference import OntologyReference


class VertexModel(InstanceModel):
    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = Vertex(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: Vertex, context: Context):
        result.type = OntologyReference[VertexType](
            alias=self.type, context=context.create_child("type", self.type, result)
        )
        result.type.owner = result

        return super().insert_dependent_data(result, context)


class Vertices(OntoRootModel[Dict[str, VertexModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, Vertex]:
        return {
            key: value.to_internal(context=context.create_child(key, data=value), owner=owner, name=key)
            for key, value in self.root.items()
        }
