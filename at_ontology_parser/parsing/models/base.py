from typing import Any
from typing import Dict
from typing import Generic
from typing import Optional
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel
from pydantic import ValidationError

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import LoadException

T = TypeVar("T")


class OntoParseModel(BaseModel):
    def to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> OntologyBase:
        try:
            result = self._to_internal(context=context, owner=owner, **kwargs)
            return self.on_loaded(result, context=context, **kwargs)
        except ValidationError as e:
            raise LoadException(
                f"Error while loading ontology or ontology model: Invalid data for {self.__class__.__name__}",
                context=context,
                errors=e.errors(),
            ) from e

    def on_loaded(self, result, *, context: Context, **kwargs) -> OntologyBase:
        return result

    def prepare_independent_data(self, *, context: Context, **kwargs) -> Dict[str, Any]:
        data = self.model_dump()
        data.update(kwargs)
        return data

    def get_preliminary_object(self, data: Dict[str, Any], *, context: Context, owner: OntologyBase) -> OntologyBase:
        raise NotImplementedError("Not implemented")

    def insert_dependent_data(self, result: OntologyBase, context: Context) -> OntologyBase:
        result._built = True
        return result

    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> OntologyBase:
        data = self.prepare_independent_data(context=context, **kwargs)
        result = self.get_preliminary_object(data, context=context, owner=owner)
        result = self.insert_dependent_data(result, context=context)
        return result


class OntoRootModel(RootModel[T], Generic[T]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Any:
        raise NotImplementedError("Not implemented")

    def to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, OntologyBase]:
        return self._to_internal(context=context, owner=owner, **kwargs)


class OntologyEntityModel(OntoParseModel):
    label: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


class DerivableModel(OntologyEntityModel):
    derived_from: Optional[str] = Field(default=None)

    def on_loaded(self, result: OntologyBase, *, context: Context, **kwargs) -> OntologyBase:
        if context.parser:
            context.parser.register_type(result, context)
        return super().on_loaded(result, context=context, **kwargs)


class DefinitionModel(OntologyEntityModel):
    pass
