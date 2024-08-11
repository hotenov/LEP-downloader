"""Sphinx configuration."""

from datetime import datetime


project = "LEP Downloader"
author = "Artem Hotenov"
copyright = f"{datetime.now().year}, {author}"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
]
autodoc_typehints = "description"
language = "en"
html_logo = "_static/logo.png"
html_theme = "furo"
