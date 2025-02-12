from pathlib import Path

import pytest

from at_ontology_parser.parsing.parser import Parser

fixtures_dir = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def normative_types():
    return fixtures_dir / "normative-types.mdl.yml"


@pytest.fixture
def course_discipline_types():
    return fixtures_dir / "course-discipline-types.mdl.yml"


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


def test_parse_models_simple(course_discipline_types):
    parser = Parser()
    model = parser.load_model_yaml_file(course_discipline_types)
    parser.finalize_references()
    assert model.name == "course-discipline-types"
    assert len(parser._modules) == 2
