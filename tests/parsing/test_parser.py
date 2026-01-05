from pathlib import Path

import pytest

from at_ontology_parser.parsing.parser import Parser

fixtures_dir = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def normative_types():
    return fixtures_dir / "yaml/normative-types.mdl.yml"


@pytest.fixture
def test_ontology():
    return fixtures_dir / "yaml/test-ontology.ont.yml"


@pytest.fixture
def course_discipline_types():
    return fixtures_dir / "yaml/course-discipline-types.mdl.yml"


def test_parse_models_imperatively(normative_types, course_discipline_types):
    parser = Parser()
    model = parser.load_model_yaml_file(normative_types)
    parser.finalize_references()
    assert model.name == "normative-types"
    assert len(parser._modules) == 1

    model = parser.load_model_yaml_file(course_discipline_types)
    parser.finalize_references()
    assert model.name == "course-discipline-types"
    assert len(parser._modules) == 2


def test_parse_models_simple(course_discipline_types, test_ontology):
    parser = Parser()
    model = parser.load_model_yaml_file(course_discipline_types)
    assert model.name == "course-discipline-types"
    assert len(parser._modules) == 2

    archive_path = parser.build_archive(model)
    assert archive_path.exists()

    parser = Parser()
    model = parser.load_model(archive_path)

    assert model.name == "course-discipline-types"
    assert len(parser._modules) == 2

    parser = Parser()
    ontology = parser.load_ontology_yaml_file(test_ontology)

    assert ontology.name == "test-ontology"
    assert len(parser._modules) == 2 and len(parser._ontology_modules) == 1

    archive_path = parser.build_archive(ontology)
    assert archive_path.exists()

    parser = Parser()
    ontology = parser.load_ontology(archive_path)
    assert ontology.name == "test-ontology"
    assert len(parser._modules) == 2 and len(parser._ontology_modules) == 1
