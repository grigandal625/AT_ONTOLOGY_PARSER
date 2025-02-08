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
    owner: Instance, ref: OwnerFeatureReference[ArtifactDefinition, Instance]
) -> ArtifactDefinition:
    if owner._built and owner.type.fulfilled and owner.type.value._built:
        return owner.type.value.artifacts.get(ref.alias)


class PreliminaryArtifactDefinitionModel(OntoParseModel):
    id: Optional[str | int] = Field(default_factory=lambda: str(uuid4()))
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
    OntoRootModel[
        List[Dict[str, str | PreliminaryArtifactDefinitionModel] | ArtifactAssignmentModel]
        | Dict[str, PreliminaryArtifactDefinitionModel]
    ]
):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        result = []
        root = self.root
        if isinstance(root, dict):
            root = [{key: value} for key, value in root.items()]
        for i, artifact_assignment in enumerate(root):
            artifact_asgm = artifact_assignment
            if not isinstance(artifact_assignment, ArtifactAssignmentModel):
                artifact = next(iter(artifact_assignment.keys()))
                path = artifact_assignment[artifact]
                id = None
                if isinstance(path, PreliminaryArtifactDefinitionModel):
                    id = path.id
                    path = path.path
                artifact_asgm = ArtifactAssignmentModel(artifact=artifact, path=path, id=id)
            result.append(artifact_asgm.to_internal(context=context.create_child(i, artifact_asgm), owner=owner))
        return result
