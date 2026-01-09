from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Self
from typing import TYPE_CHECKING

from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import OntologyException

if TYPE_CHECKING:
    from at_ontology_parser.reference import OntologyReference
    from at_ontology_parser.model.definitions.property_definition import PropertyDefinition
    from at_ontology_parser.model.definitions.artifact_definition import ArtifactDefinition
    from at_ontology_parser.ontology.assignments.property_assignment import PropertyAssignment
    from at_ontology_parser.ontology.assignments.artifact_assignment import ArtifactAssignment


@dataclass(kw_only=True)
class OntologyBase:
    owner: Optional["OntologyBase"] = field(default=None, init=False, repr=False)
    _built: bool = field(default=False, init=False, repr=False)

    @property
    def has_owner(self):
        return self.owner is not None

    @classmethod
    def public_fields(cls):
        return {f.name: f for f in fields(cls) if f.init}

    def create_context(
        self, name: str, data: Optional[Any] = None, parent: Optional[Context] = None, as_initiator: bool = True
    ):
        return Context(name=name, data=data, initiator=self if as_initiator else None, parent=parent)

    @property
    def _including_empty_fields(self):
        return []

    def to_representation(self, context: Context, minify=True, exclude_name=True) -> dict | str:
        return self._to_repr(context=context, minify=minify, exclude_name=exclude_name)

    def _to_repr(self, context: Context, minify=True, exclude_name=True) -> dict | str:
        res = {}
        for f in self.public_fields().values():
            if f.name == "name" and exclude_name:
                continue

            item = getattr(self, f.name)

            data = self._represent(
                item,
                context.create_child(f.name, data=item, initiator=self),
                minify=minify,
                exclude_name=exclude_name,
            )
            if data is not None:
                if (isinstance(data, list) or isinstance(data, dict)) and not data:
                    if f.name in self._including_empty_fields:
                        res[f.name] = data
                else:
                    res[f.name] = data
        return res

    @staticmethod
    def _represent(item: Any, context: "Context", minify: bool = True, exclude_name: bool = True):
        if isinstance(item, OntologyBase):
            return item.to_representation(context=context, minify=minify, exclude_name=exclude_name)
        elif isinstance(item, list):
            return [
                OntologyBase._represent(
                    item_value, context=context.create_child(i, item_value), minify=minify, exclude_name=exclude_name
                )
                for i, item_value in enumerate(item)
            ]
        elif isinstance(item, dict):
            return {
                key: OntologyBase._represent(
                    item_value, context=context.create_child(key, item_value), minify=minify, exclude_name=exclude_name
                )
                for key, item_value in item.items()
            }
        else:
            return item


@dataclass(kw_only=True)
class OntologyEntity(OntologyBase):
    name: str
    label: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)


@dataclass(kw_only=True)
class Derivable(OntologyEntity):
    derived_from: "OntologyReference[Self]" = field(default=None, repr=False)

    @property
    def derivation(self) -> list[Self]:
        result = [self]

        derived_from = self.derived_from

        while derived_from and derived_from.fulfilled:
            result = [derived_from.value] + result
            derived_from = derived_from.value.derived_from
        return result
    
    @property
    def derivation_path(self) -> list[str]:
        return [d.name for d in self.derivation]
    

@dataclass(kw_only=True)
class Instancable(Derivable):
    properties: Optional[Dict[str, "PropertyDefinition"]] = field(default_factory=dict, repr=False)
    artifacts: Optional[Dict[str, "ArtifactDefinition"]] = field(default_factory=dict, repr=False)
    metadata: Optional[dict] = field(default=None, repr=False)


@dataclass(kw_only=True)
class Definition(OntologyEntity):
    pass


@dataclass(kw_only=True)
class Instance(OntologyEntity):
    type: "OntologyReference[Instancable]"
    metadata: Optional[dict] = field(default=None, repr=False)
    properties: Optional[List["PropertyAssignment"]] = field(default=None, repr=False)
    artifacts: Optional[List["ArtifactAssignment"]] = field(default=None, repr=False)

    def _to_repr(self, context: "Context", minify=True, exclude_name=True):
        result = super()._to_repr(context, minify, exclude_name)

        result["properties"] = self._represent_properties(
            context=context.create_child("properties"), minify=minify, exclude_name=exclude_name
        )
        result["artifacts"] = self._represent_artifacts(
            context=context.create_child("artifacts"), minify=minify, exclude_name=exclude_name
        )
        return result

    def _represent_properties(self, context: "Context", minify=True, exclude_name=True):
        if not self.properties:
            return {}
        result = {}

        for prop in self.properties:
            if prop.property.alias in result:
                if not prop.property.value.allows_multiple:
                    raise OntologyException(
                        "Unexpected repeated property assignment", context=context.create_child(prop.property.alias)
                    )
                result[prop.property.alias].append(
                    prop.to_representation(
                        context=context.create_child(prop.property.alias), minify=minify, exclude_name=exclude_name
                    )
                )
            elif prop.property.value.allows_multiple:
                result[prop.property.alias] = [
                    prop.to_representation(
                        context=context.create_child(prop.property.alias), minify=minify, exclude_name=exclude_name
                    )
                ]
            else:
                result[prop.property.alias] = prop.to_representation(
                    context=context.create_child(prop.property.alias), minify=minify, exclude_name=exclude_name
                )
        return result

    def _represent_artifacts(self, context: "Context", minify=True, exclude_name=True):
        if not self.artifacts:
            return {}
        result = {}
        for artifact in self.artifacts:
            if artifact.artifact.alias in result:
                if not artifact.artifact.value.allows_multiple:
                    raise OntologyException(
                        "Unexpected repeated artifact assignment", context=context.create_child(artifact.artifact.alias)
                    )
                result[artifact.artifact.alias].append(
                    artifact.to_representation(
                        context=context.create_child(artifact.artifact.alias), minify=minify, exclude_name=exclude_name
                    )
                )
            elif artifact.artifact.value.allows_multiple:
                result[artifact.artifact.alias] = [
                    artifact.to_representation(
                        context=context.create_child(artifact.artifact.alias), minify=minify, exclude_name=exclude_name
                    )
                ]
            else:
                result[artifact.artifact.alias] = artifact.to_representation(
                    context=context.create_child(artifact.artifact.alias), minify=minify, exclude_name=exclude_name
                )
        return result
