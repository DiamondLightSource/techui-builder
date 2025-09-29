# from pathlib import Path

# import pytest

# from techui_builder.builder import Builder

# from techui_builder.generate import Generator


# def test_build_groups(gb: Builder):
#     generator = Generator(
#         gb.entities, gb._gui_map, gb.components[4].name
#     )  # TODO: remove hardcoded index
#     generator.build_groups()
#     with open("./tests/test_files/group.xml") as f:
#         control = f.read()
#     assert str(generator.group) == control
