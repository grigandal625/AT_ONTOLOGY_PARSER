from pathlib import Path

import pytest

from at_ontology_parser.parsing.parser import Parser

fixtures_dir = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def normative_types():
    return fixtures_dir / "normative-types.mdl.yml"


def test_parse_file(normative_types):
    parser = Parser()
    model = parser.load_model_yaml_file(normative_types)
    parser.finalize_references()
    assert model.name == "normative-types"
    assert len(parser._modules) == 1
