from typing import Dict
from typing import List
from typing import Optional

from pydantic import Field

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import RelationshipType
from at_ontology_parser.model.types import VertexType
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.instancable import InstancableModel
from at_ontology_parser.reference import OntologyReference


class RelationshipTypeModel(InstancableModel):
    valid_source_types: Optional[List[str]] = Field(default_factory=list)
    valid_target_types: Optional[List[str]] = Field(default_factory=list)

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = RelationshipType(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: RelationshipType, context: Context):
        if result.derived_from:
            result.derived_from = OntologyReference[RelationshipType](
                alias=self.derived_from, context=context.create_child("derived_from", self.derived_from, result)
            )
            result.derived_from.owner = result
        if result.valid_source_types:
            valid_source_types = []
            for source_type in self.valid_source_types:
                ref = OntologyReference[VertexType](
                    alias=source_type,
                    context=context.create_child("valid_source_types", self.valid_source_types, result).create_child(
                        source_type, source_type
                    ),
                )
                ref.owner = result
                valid_source_types.append(ref)
            result.valid_source_types = valid_source_types

        if result.valid_target_types:
            valid_target_types = []
            for target_type in self.valid_target_types:
                ref = OntologyReference[VertexType](
                    alias=target_type,
                    context=context.create_child("valid_target_types", self.valid_target_types, result).create_child(
                        target_type, target_type
                    ),
                )
                ref.owner = result
                valid_target_types.append(ref)
            result.valid_target_types = valid_target_types
        return super().insert_dependent_data(result, context)


class RelationshipTypes(OntoRootModel[Dict[str, RelationshipTypeModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, OntologyBase]:
        return {
            key: relationship_type.to_internal(
                context=context.create_child(key, data=relationship_type), owner=owner, name=key
            )
            for key, relationship_type in self.root.items()
        }
