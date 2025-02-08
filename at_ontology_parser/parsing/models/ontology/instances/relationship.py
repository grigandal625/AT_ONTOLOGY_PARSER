from typing import Dict

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import RelationshipType
from at_ontology_parser.ontology.instances import Relationship
from at_ontology_parser.ontology.instances import Vertex
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.instance import InstanceModel
from at_ontology_parser.reference import OntologyReference


class RelationshipModel(InstanceModel):
    source: str
    target: str

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = Relationship(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: Relationship, context: Context):
        result.type = OntologyReference[RelationshipType](
            alias=self.type, context=context.create_child("type", self.type, result)
        )
        result.type.owner = result

        result.source = OntologyReference[Vertex](
            alias=self.source, context=context.create_child("source", self.source, result)
        )
        result.source.owner = result

        result.target = OntologyReference[Vertex](
            alias=self.target, context=context.create_child("target", self.target, result)
        )
        result.target.owner = result

        return super().insert_dependent_data(result, context)


class Relationships(OntoRootModel[Dict[str, RelationshipModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        return {
            key: value.to_internal(context=context.create_child(key, data=value), owner=owner, name=key)
            for key, value in self.root.items()
        }
