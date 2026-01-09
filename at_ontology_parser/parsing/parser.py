import io
import os
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from typing import Callable
from typing import Dict
from typing import ForwardRef
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from uuid import uuid4

import yaml
from pydantic import ValidationError

from at_ontology_parser.base import Derivable
from at_ontology_parser.base import Instance
from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import ImportException
from at_ontology_parser.exceptions import LoadException
from at_ontology_parser.exceptions import OntologyException
from at_ontology_parser.model import OntologyModel
from at_ontology_parser.model.definitions import ImportDefinition
from at_ontology_parser.model.types import ONTOLOGY_TYPES
from at_ontology_parser.ontology.handler import Ontology
from at_ontology_parser.ontology.instances import ONTOLOGY_INSTANCES
from at_ontology_parser.parsing.models.model.handler import OntologyModelModel
from at_ontology_parser.parsing.models.ontology.handler import OntologyHandlerModel
from at_ontology_parser.reference import BaseReference
from at_ontology_parser.reference import OntologyReference
from at_ontology_parser.reference import OwnerFeatureReference


@dataclass(kw_only=True)
class ModelModule(OntologyBase):
    model: OntologyModel = field(repr=False)
    full_path: Path
    orig_name: str
    parser: "Parser"
    artifacts: Dict[Path, io.IOBase] = field(init=False, repr=False, default_factory=dict)
    context: Context = field(repr=False)

    def resolve_imports(self, context: Context, import_loaders: List["ImportLoader"]):
        self.model.owner = self
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
        self.model._resolved_imports = resolved_imports


@dataclass(kw_only=True)
class OntologyModule(OntologyBase):
    ontology: Ontology = field(repr=False)
    full_path: Path
    orig_name: str
    parser: "Parser"
    artifacts: Dict[Path, io.IOBase] = field(init=False, repr=False, default_factory=dict)
    context: Context = field(repr=False)

    def resolve_imports(self, context: Context, import_loaders: List["ImportLoader"]):
        self.ontology.owner = self
        resolved_imports: List[Tuple["ImportDefinition", "OntologyModel", "ModelModule"]] = []
        errors = []
        for i, import_def in enumerate(self.ontology.imports):
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
        self.ontology._resolved_imports = resolved_imports


class ImportLoader:
    def __init__(self, *args, **kwargs):
        pass

    def resolve_import(
        self, source_module: ModelModule | OntologyModule, import_def: ImportDefinition, context: Context
    ) -> ModelModule:
        if isinstance(source_module, ModelModule):
            orig_module = source_module.parser.get_module_by_orig_name(import_def.file)
            if orig_module:
                return orig_module
        import_path = Path(import_def.file)

        orig_name = import_path

        dir_path = source_module.full_path.parent
        if not import_path.is_absolute():
            import_path = dir_path / import_path
            orig_name = None

        if isinstance(source_module, ModelModule) and str(import_path) in source_module.parser._modules:
            return source_module.parser.modules[str(import_path)]

        if not import_path.exists():
            raise ImportException(
                f'Error while loading ontology or ontology model: File not found "{import_def.file}"',
                context=context,
            )

        model = source_module.parser.load_model_yaml_file(
            full_path=import_path, orig_name=orig_name, context=context, finalize=False
        )

        module = source_module.parser.get_module_by_model(model)
        self.load_artifacts(module)
        model._built = True
        module._built = True

        return module

    def load_artifacts(self, module: ModelModule):
        if module.full_path.exists():
            all_imports = (
                [Path(m.full_path) for m in module.parser.ontology_modules.values()]
                + [Path(m.full_path) for m in module.parser.modules.values()]
                + module.parser._bypass_imports(model=module.model, parent_path=module.full_path)
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
    root_context: Context = field(init=False, repr=False)
    import_loaders: List[ImportLoader] = field(init=False, repr=False)
    ontology_model_model_class: Type[OntologyModelModel] = field(init=False, repr=False)
    ontology_handler_model_class: Type[OntologyHandlerModel] = field(init=False, repr=False)
    _temp_dir: str = field(init=False, repr=False)

    _registered_types: Dict[str, Dict[str, Derivable]] = field(init=False, repr=False)
    _registered_instances: Dict[str, Dict[str, Instance]] = field(init=False, repr=False)
    _requested_references: List[BaseReference] = field(init=False, repr=False)

    _modules: Dict[str, ModelModule] = field(init=False, repr=False)
    _ontology_modules: Dict[str, OntologyModule] = field(init=False, repr=False)

    def __post_init__(self):
        self.root_context = Context(name="parser", data=None, initiator=self, parser=self)
        self._modules = {}
        self._ontology_modules = {}
        self.ontology_model_model_class = OntologyModelModel
        self.ontology_handler_model_class = OntologyHandlerModel
        self.import_loaders = [ImportLoader(self)]
        self._registered_types = {section: {} for section in ONTOLOGY_TYPES.sections()}
        self._registered_instances = {section: {} for section in ONTOLOGY_INSTANCES.sections()}
        self._requested_references = []

        with TemporaryDirectory() as temp_dir:
            self._temp_dir = temp_dir

    @property
    def temp_dir(self) -> Path:
        return Path(self._temp_dir)

    @property
    def modules(self) -> Dict[str, ModelModule]:
        return self._modules

    @property
    def ontology_modules(self) -> Dict[str, OntologyModule]:
        return self._ontology_modules

    def get_module_by_orig_name(self, orig_name: str) -> Optional[ModelModule]:
        return next(iter([m for m in self.modules.values() if m.orig_name == orig_name]), None)

    def get_ontology_module_by_orig_name(self, orig_name: str) -> Optional[OntologyModule]:
        return next(iter([m for m in self.ontology_modules.values() if m.orig_name == orig_name]), None)

    def get_module_by_model(self, model: OntologyModel) -> Optional[ModelModule]:
        return next(iter([m for m in self.modules.values() if m.model is model]), None)

    def get_module_by_ontology(self, ontology: Ontology) -> Optional[OntologyModule]:
        return next(iter([m for m in self.ontology_modules.values() if m.ontology is ontology]), None)

    def register_type(self, type: Derivable, context: Context):
        section = ONTOLOGY_TYPES.class_to_section_mapping().get(type.__class__)
        self._registered_types[section][type.name] = type

    def register_instance(self, instance: Instance, context: Context):
        section = ONTOLOGY_INSTANCES.class_to_section_mapping().get(instance.__class__)
        self._registered_instances[section][instance.name] = instance

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
                "Error while loading ontology model: Invalid data",
                context=context,
                errors=e.errors(),
            ) from e

        module = ModelModule(
            model=None,
            orig_name=str(orig_name),
            full_path=full_path,
            parser=self,
            context=context,
        )

        ontology_model = ontology_model_model.to_internal(context=context, owner=module)
        module.model = ontology_model

        self._modules[str(full_path)] = module

        module.resolve_imports(context=context, import_loaders=self.import_loaders)

        return ontology_model

    def load_model_yaml_file(
        self,
        full_path: str | bytes | Path | io.IOBase,
        orig_name: Optional[str] = None,
        context: Context = None,
        finalize: bool = True,
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
            result = self.load_ontology_model_data(data, orig_name, full_path, context=context)
            if finalize:
                self.finalize_references()
            return result
        except yaml.YAMLError as e:
            raise LoadException(
                "Error while loading YAML file",
                context=context,
                errors=[str(e)],
            ) from e

    def load_ontology_data(
        self,
        data: Dict[str, Any],
        orig_name: str,
        full_path: str,
        context: Context = None,
    ) -> Ontology:
        context = context or self.root_context

        full_path = Path(full_path)

        try:
            ontology_handler_model = self.ontology_handler_model_class(**data)
        except ValidationError as e:
            raise LoadException(
                "Error while loading ontology: Invalid data",
                context=context,
                errors=e.errors(),
            ) from e

        module = OntologyModule(
            ontology=None,
            orig_name=str(orig_name),
            full_path=full_path,
            parser=self,
            context=context,
        )

        ontology = ontology_handler_model.to_internal(context=context, owner=module)
        module.ontology = ontology

        module.resolve_imports(context=context, import_loaders=self.import_loaders)
        self._ontology_modules[str(full_path)] = module

        return ontology

    def load_ontology_yaml_file(
        self,
        full_path: str | bytes | Path | io.IOBase,
        orig_name: Optional[str] = None,
        context: Context = None,
    ) -> Ontology:
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
            result = self.load_ontology_data(data, orig_name, full_path, context=context)
            self.finalize_references()
            return result
        except yaml.YAMLError as e:
            raise LoadException(
                "Error while loading YAML file",
                context=context,
                errors=[str(e)],
            ) from e

    def _extract_archive(self, full_path: str | bytes | Path) -> Path:
        full_path = Path(full_path)
        extract_to = self.temp_dir / "load" / str(uuid4()) / full_path.stem
        os.makedirs(extract_to)

        if zipfile.is_zipfile(full_path):
            with zipfile.ZipFile(full_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
        elif tarfile.is_tarfile(full_path):
            # 'r:*' поддерживает tar, tar.gz, tar.bz2
            with tarfile.open(full_path, "r:*") as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            raise ValueError(f"Archive type {full_path.suffix} is not supported for archive {full_path}")
        return extract_to

    def load_model(self, full_path: str | bytes | Path) -> OntologyModel:
        full_path = Path(full_path)

        if zipfile.is_zipfile(full_path) or tarfile.is_tarfile(full_path):
            return self.load_model_archive(full_path)
        if full_path.suffix.lower() in [".yml", ".yaml"]:
            return self.load_model_yaml_file(full_path)

        raise LoadException(
            "Error while loading service template",
            context=self.root_context,
            errors=[f"Unsupported file format: {full_path}"],
        )

    def load_model_archive(self, full_path: str | bytes | Path) -> OntologyModel:
        extracted_dir = self._extract_archive(full_path)
        root_files = [f for f in os.listdir(str(extracted_dir)) if os.path.isfile(extracted_dir / f)]

        yaml_files = [f for f in root_files if Path(f).suffix in [".yml", ".yaml"]]

        if len(yaml_files) != 1:
            raise LoadException(
                "Error while loading CSAR",
                context=self.root_context,
                errors=["Expected the only one tosca yaml file in the root of the archive"],
            )
        root_yaml = yaml_files[0]

        result = self.load_model_yaml_file(extracted_dir / root_yaml)

        return result

    def load_ontology(self, full_path: str | bytes | Path) -> Ontology:
        full_path = Path(full_path)

        if zipfile.is_zipfile(full_path) or tarfile.is_tarfile(full_path):
            return self.load_ontology_archive(full_path)
        if full_path.suffix.lower() in [".yml", ".yaml"]:
            return self.load_ontology_yaml_file(full_path)

        raise LoadException(
            "Error while loading service template",
            context=self.root_context,
            errors=[f"Unsupported file format: {full_path}"],
        )

    def load_ontology_archive(self, full_path: str | bytes | Path) -> Ontology:
        extracted_dir = self._extract_archive(full_path)
        root_files = [f for f in os.listdir(str(extracted_dir)) if os.path.isfile(extracted_dir / f)]

        yaml_files = [f for f in root_files if Path(f).suffix in [".yml", ".yaml"]]

        if len(yaml_files) != 1:
            raise LoadException(
                "Error while loading CSAR",
                context=self.root_context,
                errors=["Expected the only one tosca yaml file in the root of the archive"],
            )
        root_yaml = yaml_files[0]

        result = self.load_ontology_yaml_file(extracted_dir / root_yaml)

        return result

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

    def request_reference(self, reference: BaseReference):
        if not self.assign_reference(reference):
            self._requested_references.append(reference)

    def assign_reference(self, reference: BaseReference) -> bool:
        if isinstance(reference, OntologyReference):
            for t in reference.types:
                cls = t
                if isinstance(t, ForwardRef) or t.__class__ is ForwardRef:
                    name = cls.__forward_arg__.split(".")[-1]
                    cls = ONTOLOGY_TYPES.class_mapping().get(name)
                section = ONTOLOGY_TYPES.class_to_section_mapping().get(cls)
                if section:
                    registered = self._registered_types.get(section, {})
                    if reference.alias in registered:
                        reference.value = registered[reference.alias]
                        return reference.fulfilled
                cls = t
                if isinstance(t, ForwardRef) or t.__class__ is ForwardRef:
                    name = cls.__forward_arg__.split(".")[-1]
                    cls = ONTOLOGY_INSTANCES.class_mapping().get(name)
                section = ONTOLOGY_INSTANCES.class_to_section_mapping().get(cls)
                if section:
                    registered = self._registered_instances.get(section, {})
                    if reference.alias in registered:
                        reference.value = registered[reference.alias]
                        return reference.fulfilled
        elif isinstance(reference, OwnerFeatureReference):
            if reference.has_owner:
                if not hasattr(reference, "__feature_getter__"):
                    raise OntologyException(
                        f"""Bad reference {reference.alias}. Expected to get __feature_getter__.
Check, that reference is created by classmethod {reference.__class__.__name__}.create(...)""",
                        context=reference.context,
                    )
                try:
                    reference.value = reference.__feature_getter__(reference.owner, reference)
                except Exception:
                    pass
        return reference.fulfilled

    def finalize_references(self, context: "Context" = None) -> bool:
        context = context or self.root_context
        for ref in self._requested_references:
            if not ref.fulfilled:
                self.assign_reference(ref)
        self._requested_references = [ref for ref in self._requested_references if not ref.finalize()]
        errors: List[OntologyException] = []
        for ref in self._requested_references:
            name = ref.types[0]
            if isinstance(name, ForwardRef) or name.__class__ is ForwardRef:
                name = name.__forward_arg__
            if hasattr(name, "__name__"):
                name = name.__name__

            errors.append(
                OntologyException(
                    f'Unknown reference "{ref.alias}" to {name}',
                    context=ref.context,
                )
            )

        if errors:
            raise LoadException(
                "Failed to load service template: Bad references",
                context=context,
                errors=[e.represent() for e in errors],
            )
        return True

    @staticmethod
    def open_file_auto_mode(file_path: str | Path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file.read(1024)
                return open(file_path, "r", encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            return open(file_path, "rb")

    @staticmethod
    def default_module_subpath_generator(module: ModelModule) -> Path:
        name = module.orig_name
        if module.model.name:
            name = module.model.name

        if name.endswith(".yml"):
            name = name[:-4]
        if name.endswith(".yaml"):
            name = name[:-5]

        if name.endswith(".mdl"):
            name = name[:-4]

        return Path("/".join(name.split(".")) + "/types.mdl.yml")

    @staticmethod
    def _bypass_import_definitions(
        handler: Ontology | OntologyModel, _watched: List[OntologyModel | Ontology] = None
    ) -> List[OntologyModel]:
        result = []
        _watched = _watched or []

        def includes_object(iterable: Iterable, obj: Any) -> bool:
            for item in iterable:
                if obj is item:
                    return True
            return False

        if not includes_object(_watched, handler):
            result.append(handler)
            current_watched = _watched + [handler]
            for import_def in handler.imports:
                imported_model = handler.get_resolved_import(import_def)
                result += [
                    t
                    for t in Parser._bypass_import_definitions(imported_model, _watched=current_watched)
                    if not includes_object(result, t)
                ]

        return result

    def build_archive(
        self,
        root_handler: Ontology | OntologyModel,
        skip_modules: List[ModelModule | str] = None,
        export_dir: str | Path = None,
        module_subpath_generator: Callable[[ModelModule], Path] = None,
        clear_after: bool = True,
    ) -> Path:
        module_subpath_generator = module_subpath_generator or self.default_module_subpath_generator
        export_dir = export_dir or self.temp_dir / f"export/{str(uuid4())}/"
        export_dir = Path(export_dir)
        skip_modules = skip_modules or []
        skip_modules = [
            self.get_module_by_orig_name(m, ignore_version=True) if isinstance(m, str) else m
            for m in skip_modules
            if self.get_module_by_orig_name(m, ignore_version=True)
        ]

        root_module = self.get_module_by_model(root_handler) or self.get_module_by_ontology(root_handler)
        if not root_module:
            raise OntologyException(
                "Can't build csar archive for template that is not contained in loaded modules",
                context=self.root_context.create_child(root_handler),
            )
        if root_module in skip_modules:
            raise OntologyException(
                "Can't build csar archive for template."
                " The module containing the template is specified in the skip_modules",
                context=self.root_context.create_child(root_handler),
            )

        imported_models = self._bypass_import_definitions(root_handler)[1:]
        skip_models = [m.model for m in skip_modules]
        imported_modules = [self.get_module_by_model(m) for m in imported_models if m not in skip_models]

        export_uuid = str(uuid4())

        self.export_module(
            root_module,
            "types.yml",
            export_dir / export_uuid,
            skip_modules,
            module_subpath_generator=module_subpath_generator,
        )
        for module in imported_modules:
            self.export_module(
                module,
                module_subpath_generator(module),
                export_dir / export_uuid,
                skip_modules,
                module_subpath_generator,
            )

        archive_name = root_module.orig_name
        if root_handler.name:
            archive_name = root_handler.name

        if archive_name.endswith(".yml"):
            archive_name = archive_name[:-4]

        if archive_name.endswith(".yaml"):
            archive_name = archive_name[:-5]

        csar_path = shutil.make_archive(export_dir / archive_name, "zip", export_dir / export_uuid)

        if clear_after:
            shutil.rmtree(export_dir / export_uuid)

        return Path(csar_path)

    def export_module(
        self,
        module: OntologyModule | ModelModule,
        export_file_subpath: str | Path,
        export_dir: str | Path,
        skip_modules: List[ModelModule | str] = None,
        module_subpath_generator: Callable[[ModelModule], Path] = None,
    ) -> Path:
        module_subpath_generator = module_subpath_generator or self.default_module_subpath_generator
        skip_modules = skip_modules or []
        skip_modules = [self.get_module_by_orig_name(m) if isinstance(m, str) else m for m in skip_modules]
        export_file_subpath = Path(export_file_subpath)
        export_dir = Path(export_dir)

        if isinstance(module, ModelModule):
            handler = module.model
        else:
            handler = module.ontology

        initials: List[Tuple[ImportDefinition, str]] = []

        for import_def, imported_model, _ in handler._resolved_imports:
            sub_module = self.get_module_by_model(imported_model)
            if sub_module in skip_modules:
                continue

            initials.append((import_def, import_def.file))

            generated_submodule_subpath = module_subpath_generator(sub_module)
            relative_path = self.get_relative_path(export_file_subpath.parent, generated_submodule_subpath)
            import_def.file = str(relative_path)

        handler_data = handler.to_representation(context=self.root_context.create_child(module.orig_name))

        for imp, initial_file in initials:
            imp.file = initial_file

        full_export_path = export_dir / export_file_subpath

        os.makedirs(full_export_path.parent, exist_ok=True)

        with open(full_export_path, "w", encoding="utf-8") as write_stream:
            yaml.dump(handler_data, write_stream, default_flow_style=False, allow_unicode=True)

        for artifact_subpath, artifact_stream in module.artifacts.items():
            artifact_stream.seek(0)
            self.write_to_file(artifact_stream, full_export_path.parent / artifact_subpath)

        return full_export_path

    @staticmethod
    def get_relative_path(from_path: str | Path, to_path: str | Path) -> str:
        from_path = Path(from_path).resolve()
        to_path = Path(to_path).resolve()
        relative_path = Path(os.path.relpath(to_path, start=from_path))
        return relative_path

    @staticmethod
    def _determine_mode(source_file: io.IOBase):
        sample = source_file.read(1)
        source_file.seek(0)
        return "wb" if isinstance(sample, bytes) else "w"

    @staticmethod
    def write_to_file(source_file: io.IOBase, destination_path: str | Path):
        mode = Parser._determine_mode(source_file)
        os.makedirs(Path(destination_path).parent, exist_ok=True)
        with open(destination_path, mode) as target_file:
            shutil.copyfileobj(source_file, target_file)
