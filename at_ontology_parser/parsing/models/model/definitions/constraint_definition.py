from typing import Any
from typing import Dict
from typing import List

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import LoadException
from at_ontology_parser.model.definitions.constraint_definition import ConstraintDefinition
from at_ontology_parser.model.definitions.constraint_definition import ONTOLOGY_CONSTRAINTS
from at_ontology_parser.parsing.models.base import OntoRootModel


class ConstraintDefinitionModel(OntoRootModel[Dict[str, Any]]):
    def to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> ConstraintDefinition:
        return super().to_internal(context=context, owner=owner, **kwargs)

    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        first_key = next(iter(self.root.keys()), None)
        if first_key not in ONTOLOGY_CONSTRAINTS.mapping():
            raise LoadException(
                "Failed to load ontology model", context=context, errors=[f'Bad constraint "{first_key}"']
            )
        constraint_type = ONTOLOGY_CONSTRAINTS.mapping()[first_key]
        args = self.root[first_key]
        result = constraint_type(args=args)
        result.owner = owner
        return result


class Constraints(OntoRootModel[List[ConstraintDefinitionModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        return [
            constraint.to_internal(context=context.create_child(i, constraint), owner=owner)
            for i, constraint in enumerate(self.root)
        ]
