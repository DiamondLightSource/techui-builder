import logging
from unittest.mock import Mock

import pytest
from phoebusgen.widget import ActionButton, Group


@pytest.mark.parametrize(
    "attr, expected",
    [
        ("location", "bl01t"),
        ("domain", "t01"),
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


def test_gb_extract_services_no_yaml_files(builder, caplog, tmp_path):
    # We don't want to use builder_with_setup as that calls _extract_services()
    # and in turn that calls _extract_entities()
    builder._extract_entities = Mock()

    # overwrite to not see the bl01t service dirs
    builder.conf.beamline.location = "bl01z"
    builder._services_dir = tmp_path
    # Temporary files to test against
    (tmp_path / "bl01z-ea-ioc-01").mkdir()
    (tmp_path / "bl01z-ea-ioc-01/config").mkdir()

    with pytest.raises(OSError) and caplog.at_level(logging.ERROR):
        builder._extract_services()

    for log_output in caplog.records:
        assert ("No ioc.yaml or fastcs.yaml found for service:") in log_output.message


def test_gb_extract_services_both_yaml_files(builder, caplog, tmp_path):
    # We don't want to use builder_with_setup as that calls _extract_services()
    # and in turn that calls _extract_entities()
    builder._extract_entities = Mock()

    # overwrite to not see the bl01t service dirs
    builder.conf.beamline.location = "bl01z"
    builder._services_dir = tmp_path
    # Temporary files to test against
    (tmp_path / "bl01z-ea-ioc-01").mkdir()
    (tmp_path / "bl01z-ea-ioc-01/config").mkdir()
    (tmp_path / "bl01z-ea-ioc-01/config/ioc.yaml").write_text("name: test")
    (tmp_path / "bl01z-ea-ioc-01/config/fastcs.yaml").write_text("name: other")

    with caplog.at_level(logging.CRITICAL):
        with pytest.raises(SystemExit):
            builder._extract_services()

    for log_output in caplog.records:
        assert ("Both ioc.yaml and fastcs.yaml found for") in log_output.message


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
    # We don't want to access Generator in this test
    builder_with_setup._generate_screen = Mock()
    builder_with_setup._validate_screen = Mock()

    builder_with_setup.create_screens()

    builder_with_setup._generate_screen.assert_called()
    # builder_with_setup._validate_screen.assert_called()


def test_create_screens_no_entities(builder, caplog):
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
    # We don't want to actually generate a screen
    builder_with_setup._generate_screen = Mock(side_effect=None)

    components = list(builder_with_setup.conf.components.keys())
    builder_with_setup.conf.components[components[2]].extras = ["BAD-PV"]

    # We only want to capture the ERROR output in this test
    with caplog.at_level(logging.ERROR):
        builder_with_setup.create_screens()

    for log_output in caplog.records:
        assert "Extra prefix BAD-PV" in log_output.message
