import io
import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

import yaml
from pydantic import ValidationError

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import ImportException
from at_ontology_parser.exceptions import LoadException
from at_ontology_parser.model import OntologyModel
from at_ontology_parser.model.definitions import ImportDefinition
from at_ontology_parser.parsing.models.model.handler import OntologyModelModel


@dataclass(kw_only=True)
class ModelModule(OntologyBase):
    model: OntologyModel = field(repr=False)
    full_path: Path
    orig_name: str
    parser: "Parser"
    artifacts: Dict[Path, io.IOBase] = field(init=False, repr=False, default_factory=list)

    def __post_init__(self):
        self.model.owner = self

    def resolve_imports(self, context: Context, import_loaders: List["ImportLoader"]):
        resolved_imports: List[Tuple["ImportDefinition", "OntologyModel", "ModelModule"]] = []
        errors = []
        for i, import_def in enumerate(self.model.imports):
            success = False
            for import_loader in import_loaders:
                try:
                    resolved_module = import_loader.resolve_import(
                        source_module=self, import_def=import_def, context=context.create_child(i, import_def, self)
                    )
                    success = True
                    resolved_imports.append((import_def, resolved_module.model, resolved_module))
                    break
                except ImportException as e:
                    errors.append(e.represent())

            if not success:
                raise LoadException(
                    f'Error while loading ontology or ontology model: Bad import "{import_def.file}"',
                    context=context.create_child(i, import_def, self),
                    errors=errors,
                )


class ImportLoader:
    def __init__(self, *args, **kwargs):
        pass

    def resolve_import(self, source_module: ModelModule, import_def: ImportDefinition, context: Context) -> ModelModule:
        orig_module = source_module.parser.get_module_by_orig_name(import_def.file)
        if orig_module:
            return orig_module
        import_path = Path(import_def.file)

        orig_name = import_path

        dir_path = source_module.full_path.parent
        if not import_path.is_absolute():
            import_path = dir_path / import_path
            orig_name = None

        if str(import_path) in source_module.parser._modules:
            return source_module.parser.modules[str(import_path)]

        if not import_path.exists():
            raise ImportException(
                f'Error while loading ontology or ontology model: File not found "{import_def.file}"',
                context=context,
            )

        model = source_module.parser.load_model_yaml_file(full_path=import_path, orig_name=orig_name, context=context)

        module = source_module.parser.get_module_by_model(model)
        self.load_artifacts(module)
        model._built = True
        module._built = True

        return module

    def load_artifacts(self, module: ModelModule):
        if module.full_path.exists():
            all_imports = [Path(m.full_path) for m in module.parser.modules.values()] + module.parser._bypass_imports(
                model=module.model, parent_path=module.full_path
            )
            result = {}
            for directory, _, files in os.walk(module.full_path.parent):
                for file in files:
                    file_path = Path(directory) / file
                    if file_path not in all_imports:
                        result[file_path.relative_to(module.full_path.parent)] = module.parser.open_file_auto_mode(
                            file_path
                        )
            module.artifacts = result


@dataclass(kw_only=True)
class Parser(OntologyBase):
    root_context: Context
    import_loaders: List[ImportLoader]
    ontology_model_model_class: Type[OntologyModelModel]

    _modules: Dict[str, ModelModule]

    def __post_init__(self):
        self.root_context = Context(name="parser", data=None, initiator=self)
        self._modules = {}
        self.ontology_model_model_class = OntologyModelModel
        self.import_loaders = [ImportLoader(self)]

    @property
    def modules(self) -> Dict[str, ModelModule]:
        return self._modules

    def get_module_by_orig_name(self, orig_name: str) -> Optional[ModelModule]:
        return next(iter([m for m in self.modules.values() if m.orig_name == orig_name]), None)

    def get_module_by_model(self, model: OntologyModel) -> Optional[ModelModule]:
        return next(iter([m for m in self.modules.values() if m.model == model]), None)

    def load_ontology_model_data(
        self,
        data: Dict[str, Any],
        orig_name: str,
        full_path: str,
        context: Context = None,
    ) -> "OntologyModel":
        context = context or self.root_context

        full_path = Path(full_path)

        try:
            ontology_model_model = self.ontology_model_model_class(**data)
        except ValidationError as e:
            raise LoadException(
                "Error while loading service template: Invalid data",
                context=context,
                errors=e.errors(),
            ) from e
        ontology_model = ontology_model_model.to_internal(context=context)

        module = ModelModule(
            model=ontology_model,
            orig_name=str(orig_name),
            full_path=full_path,
            parser=self,
        )

        self._modules[str(full_path)] = module

        module.resolve_imports(context=context)

        return ontology_model

    def load_model_yaml_file(
        self,
        full_path: str | bytes | Path | io.IOBase,
        orig_name: Optional[str] = None,
        context: Context = None,
    ) -> OntologyModel:
        try:
            if orig_name is None:
                if isinstance(full_path, str):
                    orig_name = full_path
                elif isinstance(full_path, bytes):
                    orig_name = io.StringIO(full_path.decode()).readline().strip()
                elif isinstance(full_path, Path):
                    orig_name = str(full_path)
                elif isinstance(full_path, io.IOBase) and hasattr(full_path, "name"):
                    orig_name = full_path.name
                else:
                    raise LoadException(
                        "Error while loading YAML file: bad arguments",
                        context=context,
                        errors=["Expected orig_name provided while loading from IOBase"],
                    )
            if not isinstance(full_path, io.IOBase):
                with open(full_path, "r") as file:
                    data = yaml.safe_load(file)
            else:
                full_path.seek(0)
                data = yaml.safe_load(full_path)
            return self.load_ontology_model_data(data, orig_name, full_path, context=context)
        except yaml.YAMLError as e:
            raise LoadException(
                "Error while loading YAML file",
                context=context,
                errors=[str(e)],
            ) from e

    def _bypass_imports(
        self, model: OntologyModel, parent_path: Path, skip_non_path: bool = True, _watched: List[OntologyModel] = None
    ) -> List[Path]:
        result: List[Path] = []
        _watched = _watched or []
        if model not in _watched:
            current_watched = _watched + [model]
            for import_def in model.imports:
                import_path = Path(import_def.file)
                if import_path.is_absolute():
                    result.append(import_path)
                    continue
                full_import_path = parent_path / import_path
                if not full_import_path.exists() and skip_non_path:
                    continue

                if full_import_path not in result:
                    result.append(full_import_path)

                imported_model = model.get_resolved_import(import_def)
                result += [
                    f
                    for f in Parser._bypass_imports(
                        imported_model,
                        parent_path=import_path,
                        _watched=current_watched,
                    )
                    if f not in result
                ]
        return result

    @staticmethod
    def open_file_auto_mode(file_path: str | Path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file.read(1024)
                return open(file_path, "r", encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            return open(file_path, "rb")
