from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from uuid import uuid4

from pydantic import Field

from at_ontology_parser.base import Instance
from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.definitions import PropertyDefinition
from at_ontology_parser.ontology.assignments import PropertyAssignment
from at_ontology_parser.parsing.models.base import OntoParseModel
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.reference import OwnerFeatureReference


def get_property_definition_from_type(
    owner: Instance, ref: OwnerFeatureReference[PropertyDefinition, Instance]
) -> PropertyDefinition:
    if owner._built and owner.type.fulfilled and owner.type.value._built:
        return owner.type.value.properties.get(ref.alias)


class PreliminaryPropertyAssignmentModel(OntoParseModel):
    id: Optional[str | int] = Field(default_factory=lambda: str(uuid4()))
    value: Any


class PropertyAssignmentModel(PreliminaryPropertyAssignmentModel):
    property: str

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = PropertyAssignment(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: PropertyAssignment, context: Context):
        result.property = OwnerFeatureReference[PropertyDefinition, Instance].create(
            self.property,
            context=context.create_child(
                self.property,
                self.property,
                initiator=result,
            ),
            feature_getter=get_property_definition_from_type,
            owner=result,
        )
        return super().insert_dependent_data(result, context)


class PropertyAssignments(
    OntoRootModel[
        List[Dict[str, Any | PreliminaryPropertyAssignmentModel] | PropertyAssignmentModel]
        | Dict[str, Any | PreliminaryPropertyAssignmentModel]
    ]
):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> List[PropertyAssignment]:
        result = []
        root = self.root
        if isinstance(root, dict):
            root = [{key: value} for key, value in root.items()]
        for i, prop_assignment in enumerate(root):
            prop = prop_assignment
            if not isinstance(prop_assignment, PropertyAssignmentModel):
                property = next(iter(prop_assignment.keys()))
                value = prop_assignment[property]
                id = None
                if isinstance(value, PreliminaryPropertyAssignmentModel):
                    id = value.id
                    value = value.value
                prop = PropertyAssignmentModel(property=property, value=value, id=id)
            result.append(prop.to_internal(context=context.create_child(i, data=prop), owner=owner))
        return result
