"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
import sys
from pathlib import Path
from subprocess import check_output

import requests

import techui_builder

# -- General configuration ------------------------------------------------
sys.path.insert(0, os.path.abspath("../../src"))
# General information about the project.
project = "techui-builder"
copyright = "2025, Diamond Light Source"

# The full version, including alpha/beta/rc tags.
release = techui_builder.__version__

# The short X.Y version.
if "+" in release:
    # Not on a tag, use branch name
    root = Path(__file__).absolute().parent.parent
    git_branch = check_output("git branch --show-current".split(), cwd=root)
    version = git_branch.decode().strip()
else:
    version = release

extensions = [
    # for diagrams
    "sphinxcontrib.mermaid",
    # Used for BaseModel autodoc
    "sphinxcontrib.autodoc_pydantic",
    # Use this for generating API docs
    "sphinx.ext.autodoc",
    # Not sure if this is still used?
    "sphinx.ext.doctest",
    # and making summary tables at the top of API docs
    "sphinx.ext.autosummary",
    # This can parse google style docstrings
    "sphinx.ext.napoleon",
    # For linking to external sphinx documentation
    "sphinx.ext.intersphinx",
    # Add links to source code in API docs
    "sphinx.ext.viewcode",
    # Adds the inheritance-diagram generation directive
    "sphinx.ext.inheritance_diagram",
    # Add a copy button to each code block
    "sphinx_copybutton",
    # For the card element
    "sphinx_design",
    "sphinx.ext.mathjax",
    "sphinx.ext.githubpages",
]

napoleon_google_docstring = False

# If true, Sphinx will warn about all references where the target cannot
# be found.
# nitpicky = True

# A list of (type, target) tuples (by default empty) that should be ignored when
# generating warnings in "nitpicky mode". Note that type should include the
# domain name if present. Example entries would be ('py:func', 'int') or
# ('envvar', 'LD_LIBRARY_PATH').
nitpick_ignore = [
    # builtins
    ("py:class", "NoneType"),
    ("py:class", "'str'"),
    ("py:class", "'float'"),
    ("py:class", "'int'"),
    ("py:class", "'bool'"),
    ("py:class", "'object'"),
    ("py:class", "'id'"),
    # typing
    ("py:class", "typing_extensions.Literal"),
]

# Order the members by the order they appear in the source code
autodoc_member_order = "bysource"

# Don't inherit docstrings from baseclasses
autodoc_inherit_docstrings = False

# Add some more modules to the top level autosummary
techui_builder.__all__ += []

# Document only what is in __all__
autosummary_ignore_module_all = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Output graphviz directive produced images in a scalable format
graphviz_output_format = "svg"

# The name of a reST role (builtin or Sphinx extension) to use as the default
# role, that is, for text marked up `like this`
default_role = "any"

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# These patterns also affect html_static_path and html_extra_path
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# Example configuration for intersphinx: refer to the Python standard library.
# This means you can link things like `str` and `asyncio` to the relevant
# docs in the python documentation.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# A dictionary of graphviz graph attributes for inheritance diagrams.
inheritance_graph_attrs = {"rankdir": "TB"}

# Common links that should be available on every page
rst_epilog = """
.. _NSLS: https://www.bnl.gov/nsls2
.. _black: https://github.com/psf/black
.. _ruff: https://beta.ruff.rs/docs/
.. _mypy: http://mypy-lang.org/
.. _pre-commit: https://pre-commit.com/
"""

# Ignore localhost links for periodic check that links in docs are valid
linkcheck_ignore = [r"http://localhost:\d+/"]

# Set copy-button to ignore python and bash prompts
# https://sphinx-copybutton.readthedocs.io/en/latest/use.html#using-regexp-prompt-identifiers
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
github_repo = "techui-builder"
github_user = "DiamondLightSource"
switcher_json = "https://diamondlightsource.github.io/techui-builder/switcher.json"
switcher_exists = requests.get(switcher_json).ok
if not switcher_exists:
    print(
        "*** Can't read version switcher, is GitHub pages enabled? \n"
        "    Once Docs CI job has successfully run once, set the "
        "Github pages source branch to be 'gh-pages' at:\n"
        f"    https://github.com/{github_user}/{github_repo}/settings/pages",
        file=sys.stderr,
    )

# Theme options for pydata_sphinx_theme
# We don't check switcher because there are 3 possible states for a repo:
# 1. New project, docs are not published so there is no switcher
# 2. Existing project with latest skeleton, switcher exists and works
# 3. Existing project with old skeleton that makes broken switcher,
#    switcher exists but is broken
# Point 3 makes checking switcher difficult, because the updated skeleton
# will fix the switcher at the end of the docs workflow, but never gets a chance
# to complete as the docs build warns and fails.
html_theme_options = {
    "use_edit_page_button": True,
    "github_url": f"https://github.com/{github_user}/{github_repo}",
    "icon_links": [
        {
            "name": "PyPI",
            "url": f"https://pypi.org/project/{project}",
            "icon": "fas fa-cube",
        },
    ],
    "switcher": {
        "json_url": switcher_json,
        "version_match": version,
    },
    "check_switcher": False,
    "navbar_end": ["theme-switcher", "icon-links", "version-switcher"],
    "navigation_with_keys": False,
}

# A dictionary of values to pass into the template engine’s context for all pages
html_context = {
    "github_user": github_user,
    "github_repo": project,
    "github_version": version,
    "doc_path": "docs",
}

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = False

# Logo
# html_logo = "images/techui-builder-logo.svg"
# html_favicon = "images/techui-builder-favicon.svg"

# If False and a module has the __all__ attribute set, autosummary documents
# every member listed in __all__ and no others. Default is True
autosummary_ignore_module_all = False

# Turn on sphinx.ext.autosummary
autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Look for signatures in the first line of the docstring (used for C functions)
autodoc_docstring_signature = True

# Don't show config summary as it's not relevant
autodoc_pydantic_model_show_config_summary = False

# Show the fields in source order
autodoc_pydantic_model_summary_list_order = "bysource"
