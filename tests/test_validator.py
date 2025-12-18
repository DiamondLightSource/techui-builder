from pathlib import Path
from unittest.mock import Mock, patch

from lxml.etree import Element, _ElementTree, tostring
from lxml.objectify import fromstring
from phoebusgen.widget import EmbeddedDisplay


def test_validator_check_bobs(validator):
    validator._check_bob = Mock()

    validator.check_bobs()

    validator._check_bob.assert_called()


def test_validator_check_bob(validator):
    validator._check_bob(validator.bobs[0])

    assert len(validator.validate.keys()) > 0
    assert list(validator.validate.keys())[0] == "motor-edited"


def test_validator_read_bob(validator):
    with patch("techui_builder.validator.read_bob") as mock_read_bob:
        # We need to set the spec of the first Mock so it knows
        # it has a getroot() function
        mock_read_bob.return_value = (Mock(spec=_ElementTree), Mock())

        validator._read_bob(validator.bobs[0])


# TODO: Clean up this test... (make fixture for mock xml?)
def test_validator_validate_bob(validator, example_embedded_widget):
    # You cannot set a text tag of an ObjectifiedElement,
    # so we need to make an etree.Element and convert it ...
    mock_root_element = Element("root")
    mock_root_element.append(example_embedded_widget)
    # ... which requires this horror
    mock_element = fromstring(tostring(mock_root_element))
    # mock_element = ObjectifiedElement(mock_widget_element)
    # mock_name_element.text = "motor"
    validator._read_bob = Mock(
        return_value=(
            Mock(),
            {"motor": (mock_element)},
        )
    )
    validator.validate = {"motor-edited": Path("tests/test_files/motor-edited.bob")}
    test_pwidget = EmbeddedDisplay(
        "motor",
        "tests/test-files/motor_embed.bob",
        0,
        0,
        205,
        120,
    )
    test_pwidget.macro("macro1", "test_macro_1")

    validator.validate_bob("motor-edited", "motor", [test_pwidget])
