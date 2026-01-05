from typing import Any
from typing import Dict
from typing import List
from typing import Optional

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
    owner: PropertyAssignment, ref: OwnerFeatureReference[PropertyDefinition, Instance]
) -> PropertyDefinition:
    if owner._built and owner.has_owner and isinstance(owner.owner, Instance) and owner.owner.type.fulfilled:
        return owner.owner.type.value.properties.get(ref.alias)


class PreliminaryPropertyAssignmentModel(OntoParseModel):
    id: Optional[str | int] = Field(default=None)
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
    OntoRootModel[Dict[str, List[PreliminaryPropertyAssignmentModel | Any] | PreliminaryPropertyAssignmentModel | Any]]
):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> List[PropertyAssignment]:
        result = []
        root = self.root
        for property, prop_assignment in root.items():
            if isinstance(prop_assignment, list):
                result += [
                    self._get_prop(property, assignment, context.create_child(i, assignment, self), owner)
                    for i, assignment in enumerate(prop_assignment)
                ]
            else:
                result.append(self._get_prop(property, prop_assignment, context, owner))
        return result

    def _get_prop(
        self,
        property: str,
        prop_assignment: PreliminaryPropertyAssignmentModel | Any,
        context: Context,
        owner: OntologyBase,
    ) -> PropertyAssignment:
        if not isinstance(prop_assignment, PreliminaryPropertyAssignmentModel):
            return PropertyAssignmentModel(property=property, value=prop_assignment).to_internal(
                context=context.create_child(property, prop_assignment, initiator=self),
                owner=owner,
            )
        else:
            return PropertyAssignmentModel(
                property=property, value=prop_assignment.value, id=prop_assignment.id
            ).to_internal(
                context=context.create_child(property, prop_assignment, initiator=self),
                owner=owner,
            )
