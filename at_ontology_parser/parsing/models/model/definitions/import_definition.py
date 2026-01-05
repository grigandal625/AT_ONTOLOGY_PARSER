from typing import Dict
from typing import List
from typing import Optional

from pydantic import Field

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import LoadException
from at_ontology_parser.model.definitions import ImportDefinition
from at_ontology_parser.parsing.models.base import OntoParseModel
from at_ontology_parser.parsing.models.base import OntoRootModel


class ImportDefinitionsModel(OntoParseModel):
    file: str
    alias: Optional[str] = Field(default=None)

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = ImportDefinition(**data)
        result.owner = owner
        return result


class Imports(OntoRootModel[List[str | Dict[str, str] | ImportDefinitionsModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        result: List[ImportDefinition] = []
        for i, imp in enumerate(self.root):
            import_def = imp
            if isinstance(import_def, str):
                import_def = ImportDefinitionsModel(file=import_def)
            elif isinstance(import_def, dict):
                alias = next(iter(import_def.keys()))
                file = import_def[alias]
                import_def = ImportDefinitionsModel(file=file, alias=alias)
            result.append(import_def.to_internal(context=context.create_child(i, imp), owner=owner))
        if len(set([imp.alias for imp in result])) != len(result):
            all_aliases = [imp.alias for imp in result]
            duplicates = set([alias for alias in all_aliases if all_aliases.count(alias) > 1])
            raise LoadException(
                "Failed to load ontology or ontology model",
                context=context,
                errors=[f"Duplicate import aliases: {duplicates}"],
            )

        return result
