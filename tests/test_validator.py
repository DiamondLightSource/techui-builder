from pathlib import Path
from unittest.mock import Mock, patch

from lxml.etree import _ElementTree
from lxml.objectify import ObjectifiedElement
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


def test_validator_validate_bob(validator):
    validator._read_bob = Mock(
        return_value=(Mock(), {"motor": Mock(spec=ObjectifiedElement)})
    )
    validator.validate = {"motor-edited": Path("tests/test_files/motor-edited.bob")}
    test_pwidget = EmbeddedDisplay(
        "motor",
        "example/t01-services/synoptic/techui_supportbob/pmac/motor_embed.bob",
        0,
        0,
        205,
        120,
    )

    validator.validate_bob("motor-edited", "motor", [test_pwidget])
