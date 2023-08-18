# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import date

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))


# -- Project information -----------------------------------------------------

project = 'base Portfolio Backend'
copyright = f'base Angewandte | University of Applied Arts Vienna, 2021-{date.today().year}'
author = 'base Dev Team'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'myst_parser',
    'sphinx_copybutton',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Additional configuration

html_show_sourcelink = False

myst_heading_anchors = 4
myst_enable_extensions = [
    'linkify',
]

primary_color = '#ff9800'

html_theme_options = {
    'light_logo': 'portfolio-backend-light.svg',
    'dark_logo': 'portfolio-backend-dark.svg',
    'light_css_variables': {
        'color-brand-primary': primary_color,
        'color-brand-content': primary_color,
    },
    'dark_css_variables': {
        'color-brand-primary': primary_color,
        'color-brand-content': primary_color,
    },
    'sidebar_hide_name': True,
    'navigation_with_keys': True,
    # 'announcement': 'Important announcement!',
}

pygments_style = 'default'
pygments_dark_style = 'github-dark'

html_css_files = [
    'css/styles.css'
]
