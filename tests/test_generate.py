# from pathlib import Path

# import pytest

# from techui_builder.builder import Builder

from techui_builder.models import Entity


def test_generator_load_screen(generator):
    entity = Entity(type="test", P="TEST", desc=None, M=None, R=None)
    generator.load_screen("test", [entity])

    assert generator.screen_name == "test"
    assert generator.screen_components == [entity]


def test_generator_get_screen_dimensions(generator):
    test_embedded_screen = "tests/test_files/motor_embed.bob"

    x, y = generator._get_screen_dimensions(test_embedded_screen)

    assert x == 120
    assert y == 205


# def test_build_groups(gb: Builder):
#     generator = Generator(
#         gb.entities, gb._gui_map, gb.components[4].name
#     )  # TODO: remove hardcoded index
#     generator.build_groups()
#     with open("./tests/test_files/group.xml") as f:
#         control = f.read()
#     assert str(generator.group) == control
