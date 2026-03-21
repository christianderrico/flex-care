from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "data" / "fixtures"

@pytest.fixture
def examples_html() -> str:
    return (FIXTURES / "patient-examples.html").read_text(encoding="utf-8")

@pytest.fixture
def definitions_html() -> str:
    return (FIXTURES / "patient-definitions.html").read_text(encoding="utf-8")

@pytest.fixture
def description_html() -> str:
    return (FIXTURES / "patient.html").read_text(encoding="utf-8")