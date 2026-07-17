"""Sphinx configuration for behave-data documentation."""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath(".."))

project = "behave-data"
author = "Mathias Paulenko"
copyright = f"{datetime.now().year}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "behave-data"
html_short_title = "behave-data"

html_theme_options = {
    "source_repository": "https://github.com/MathiasPaulenko/behave-data",
    "source_branch": "main",
    "source_directory": "docs/",
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autodoc_typehints = "description"
autodoc_class_signature = "separated"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "behave": ("https://behave.readthedocs.io/en/stable/", None),
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
]

rst_prolog = """
.. role:: python(code)
   :language: python
   :class: highlight
"""
