from typing import Dict
from typing import List
from typing import Optional
from uuid import uuid4

from pydantic import Field

from at_ontology_parser.base import Instance
from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.definitions import ArtifactDefinition
from at_ontology_parser.ontology.assignments import ArtifactAssignment
from at_ontology_parser.parsing.models.base import OntoParseModel
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.reference import OwnerFeatureReference


def get_artifact_definition_from_type(
    owner: ArtifactAssignment, ref: OwnerFeatureReference[ArtifactDefinition, Instance]
) -> ArtifactDefinition:
    if owner._built and owner.has_owner and isinstance(owner.owner, Instance) and owner.owner.type.fulfilled:
        return owner.owner.type.value.artifacts.get(ref.alias)


class PreliminaryArtifactDefinitionModel(OntoParseModel):
    path: str


class ArtifactAssignmentModel(PreliminaryArtifactDefinitionModel):
    artifact: str

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = ArtifactAssignment(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: ArtifactAssignment, context: Context):
        result.artifact = OwnerFeatureReference[ArtifactDefinition, Instance].create(
            alias=self.artifact,
            context=context.create_child("artifact", result.artifact, result),
            feature_getter=get_artifact_definition_from_type,
            owner=result,
        )
        return super().insert_dependent_data(result, context)


class ArtifactAssigments(
    OntoRootModel[Dict[str, List[PreliminaryArtifactDefinitionModel | str] | PreliminaryArtifactDefinitionModel | str]]
):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        result = []
        root = self.root
        for artifact, artifact_assignment in root.items():
            if isinstance(artifact_assignment, list):
                result += [
                    self._get_art(artifact, assignment, context.create_child(i, assignment, self), owner)
                    for i, assignment in enumerate(artifact_assignment)
                ]
            else:
                result.append(self._get_art(artifact, artifact_assignment, context, owner))
        return result

    def _get_art(
        self,
        artifact: str,
        artifact_assignment: PreliminaryArtifactDefinitionModel | str,
        context: Context,
        owner: OntologyBase,
    ):
        if not isinstance(artifact_assignment, PreliminaryArtifactDefinitionModel):
            return ArtifactAssignmentModel(artifact=artifact, path=artifact_assignment).to_internal(
                context=context.create_child("artifact", artifact, self), owner=owner
            )
        else:
            return ArtifactAssignmentModel(
                artifact=artifact, id=artifact_assignment.id, path=artifact_assignment.path
            ).to_internal(context=context.create_child("artifact", artifact, self), owner=owner)
