from typing import Any
from typing import Optional

from pydantic import Field

from at_ontology_parser.base import Instance
from at_ontology_parser.exceptions import Context
from at_ontology_parser.parsing.models.base import OntologyEntityModel
from at_ontology_parser.parsing.models.ontology.assignments.artifact_assignment import ArtifactAssigments
from at_ontology_parser.parsing.models.ontology.assignments.property_assignment import PropertyAssignments


class InstanceModel(OntologyEntityModel):
    type: str
    metadata: Optional[Any] = Field(default=None)
    properties: Optional[PropertyAssignments] = Field(default_factory=lambda: PropertyAssignments([]))
    artifacts: Optional[ArtifactAssigments] = Field(default_factory=lambda: ArtifactAssigments([]))

    def on_loaded(self, result: Instance, *, context: Context, **kwargs) -> Instance:
        if context.parser:
            context.parser.register_instance(result, context)
        return super().on_loaded(result, context=context, **kwargs)

    def insert_dependent_data(self, result: Instance, context: Context):
        if result.properties:
            result.properties = self.properties.to_internal(
                context=context.create_child("properties", self.properties, result), owner=result
            )
        if result.artifacts:
            result.artifacts = self.artifacts.to_internal(
                context=context.create_child("artifacts", self.artifacts, result), owner=result
            )
        return super().insert_dependent_data(result, context)
