import logging
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from phoebusgen.widget import ActionButton, Group
from softioc.builder import ClearRecords, records


@pytest.mark.parametrize(
    "attr, expected",
    [
        ("location", "t01"),
        ("domain", "bl01t"),
        ("desc", "Test Beamline"),
    ],
)
def test_beamline_attributes(builder, attr, expected):
    assert getattr(builder.conf.beamline, attr) == expected


@pytest.mark.parametrize(
    "index, name, label, P, R, attribute, file, extras, child_labels",
    [
        (0, "fshtr", "Fast Shutter", "BL01T-EA-FSHTR-01", None, None, None, None, None),
        (1, "d1", "Diode 1", "BL01T-DI-PHDGN-01", None, None, "test.bob", None, None),
        (
            2,
            "motor",
            "Motor Stage",
            "BL01T-MO-MOTOR-01",
            None,
            None,
            None,
            None,
            {"X": "X1", "Y": "Y1", "Z": "Z1"},
        ),
    ],
)
def test_component_attributes(
    builder,
    index,
    name,
    label,
    P,  # noqa: N803
    R,  # noqa: N803
    attribute,
    file,
    extras,
    child_labels,
):
    components = list(builder.conf.components.keys())
    component = builder.conf.components[components[index]]
    assert components[index] == name
    assert component.label == label
    assert component.P == P
    assert component.R == R
    assert component.attribute == attribute
    assert component.child_labels == child_labels
    if file is not None:
        assert component.file == file
    if extras is not None:
        assert component.extras == extras


def test_builder_create_status_pv(builder):
    p = "BL01T-MO-MOTOR-01"
    inpa = "BL01T-MO-MOTOR-01:MOTOR1.MOVN"
    builder._create_status_pv(prefix=p, inputs=[inpa])

    status_pv = """
record(calc, "BL01T-MO-MOTOR-01:STA")
{
    field(ACKT, "NO")
    field(CALC, "(A|B|C|D|E|F|G|H|I|J|K|L)>0?1:0")
    field(INPA, "BL01T-MO-MOTOR-01:MOTOR1.MOVN")
    field(INPB, "")
    field(INPC, "")
    field(INPD, "")
    field(INPE, "")
    field(INPF, "")
    field(INPG, "")
    field(INPH, "")
    field(INPI, "")
    field(INPJ, "")
    field(INPK, "")
    field(INPL, "")
    field(SCAN, "1 second")
}
"""

    assert builder.status_pvs != {}

    # Fake file-like object to "print" the record to
    auto_status_pv = StringIO()
    # Get the string representation of the record
    builder.status_pvs[p].Print(auto_status_pv)

    assert auto_status_pv.getvalue() == status_pv

    # Make sure the record is deleted
    ClearRecords()


def test_builder_write_status_pvs(builder):
    # To mock the open() function used in _write_status_pvs
    m = mock_open()

    p = "BL01T-MO-MOTOR-01"
    inpa = "BL01T-MO-MOTOR-01:MOTOR1.MOVN"
    status_pv = records.calc(  # pyright: ignore[reportAttributeAccessIssue]
        f"{p}:STA",
        CALC="(A|B|C|D|E|F|G|H|I|J|K|L)>0?1:0",
        SCAN="1 second",
        ACKT="NO",
        INPA=inpa,
    )
    builder.status_pvs[p] = status_pv

    # Mock the Print() function so we don't actually write a file
    with (
        patch("builtins.open", m),
        patch("techui_builder.builder.Record.Print") as mock_print,
    ):
        builder.write_status_pvs()

        # Check open() was called with the correct args
        m.assert_called_once_with(
            Path(builder._write_directory.joinpath("config/status.db")),
            "w",
        )
        mock_print.assert_called_once()

    # Make sure the record is deleted
    ClearRecords()


def test_missing_service(builder, caplog):
    builder._extract_entities = Mock(side_effect=OSError())
    builder._extract_services()
    for log_output in caplog.records:
        assert "No ioc.yaml or fastcs.yaml found for service:" in log_output.message


@pytest.mark.parametrize(
    "index, type, desc, pv, macros",
    [
        (0, "pmac.GeoBrick", None, "BL01T-MO-BRICK-01", {"P": "BL01T-MO-BRICK-01"}),
        (
            0,
            "pmac.autohome",
            None,
            "BL01T-MO-MOTOR-01",
            {"P": "BL01T-MO-MOTOR-01"},
        ),
        (
            1,
            "pmac.dls_pmac_asyn_motor",
            None,
            "BL01T-MO-MOTOR-01:X",
            {"P": "BL01T-MO-MOTOR-01", "M": ":X"},
        ),
        (
            2,
            "pmac.dls_pmac_asyn_motor",
            None,
            "BL01T-MO-MOTOR-01:A",
            {"P": "BL01T-MO-MOTOR-01", "M": ":A"},
        ),
    ],
)
def test_gb_extract_entities_ioc_yaml(
    builder, techui_support, index, type, desc, pv, macros
):
    # We don't want to use builder_with_setup as that calls _extract_services()
    # and in turn that calls _extract_entities()
    builder.techui_support = techui_support
    prefix = pv.split(":", maxsplit=1)[0]

    builder._extract_entities(
        "bl01t-mo-ioc-01",
        builder._services_dir.joinpath("bl01t-mo-ioc-01/config/ioc.yaml"),
    )
    entity = builder.entities[prefix][index]
    assert entity.type == type
    assert entity.desc == desc
    assert entity.prefix == pv
    assert entity.macros == macros


@pytest.mark.parametrize(
    "index, type, desc, pv, macros",
    [
        (
            0,
            "fastcs.TemperatureController",
            None,
            "BL01T-EA-TEST-01",
            {"name": "BL01T-EA-TEST-01"},
        ),
    ],
)
def test_gb_extract_entities_fastcs_yaml(
    builder, techui_support, index, type, desc, pv, macros
):
    # We don't want to use builder_with_setup as that calls _extract_services()
    # and in turn that calls _extract_entities()
    builder.techui_support = techui_support

    prefix = pv.split(":", maxsplit=1)[0]

    builder._extract_entities(
        "bl01t-ea-ioc-01",
        builder._services_dir.joinpath("bl01t-ea-ioc-01/config/fastcs.yaml"),
    )
    entity = builder.entities[prefix][index]
    assert entity.type == type
    assert entity.desc == desc
    assert entity.prefix == pv
    assert entity.macros == macros


def test_builder_generate_screen(builder_with_setup):
    # with (
    #     patch("techui_builder.builder.Generator.build_screen") as mock_build_screen,
    #     patch("techui_builder.builder.Generator.write_screen") as mock_write_screen,
    # ):
    builder_with_setup.generator.build_screen = Mock()
    builder_with_setup.generator.write_screen = Mock()

    builder_with_setup._generate_screen("TEST")

    builder_with_setup.generator.build_screen.assert_called_once()
    builder_with_setup.generator.write_screen.assert_called_once()


def test_builder_validate_screen(builder_with_setup):
    builder_with_setup.validator.validate_bob = Mock()
    builder_with_setup.generator.widgets = [Mock(spec=ActionButton)]
    builder_with_setup.generator.group = Mock(spec=Group, name="TEST")

    builder_with_setup._validate_screen("TEST")

    builder_with_setup.validator.validate_bob.assert_called_once()


def test_create_screens(builder_with_setup):
    # We don't want to make a status PV in this test
    builder_with_setup._create_status_pv = Mock()
    # We don't want to access Generator in this test
    builder_with_setup._generate_screen = Mock()
    builder_with_setup._validate_screen = Mock()

    builder_with_setup.create_screens()

    builder_with_setup._generate_screen.assert_called()
    # builder_with_setup._validate_screen.assert_called()


def test_create_screens_no_entities(builder, caplog):
    # We don't want to make a status PV in this test
    builder._create_status_pv = Mock()

    builder.entities = []

    # We only wan't to capture CRITICAL output in this test
    with caplog.at_level(logging.CRITICAL):
        with pytest.raises(SystemExit):
            builder.create_screens()

    for log_output in caplog.records:
        assert (
            "No ioc entities found. This [italic]normally[/italic]"
            " suggests an issue with finding ixx-services."
        ) in log_output.message


def test_create_screens_extra_p_does_not_exist(builder_with_setup, caplog):
    # We don't want to make a status PV in this test
    builder_with_setup._create_status_pv = Mock()
    # We don't want to actually generate a screen
    builder_with_setup._generate_screen = Mock(side_effect=None)

    components = list(builder_with_setup.conf.components.keys())
    builder_with_setup.conf.components[components[2]].extras = ["BAD-PV"]

    # We only want to capture the ERROR output in this test
    with caplog.at_level(logging.ERROR):
        builder_with_setup.create_screens()

    for log_output in caplog.records:
        assert "Extra prefix BAD-PV" in log_output.message
