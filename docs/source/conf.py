# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyAVControl' # TBD
copyright = '2024 Ryan Snodgrass'
author = 'Ryan Snodgrass'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
#
# NOTE: Use Google Docstring format using the sphinx.ext.napolean
# extension, since Google Docstring is a way more readable format
# than the default Sphinx format.
#
# myst_parser = Markdown support (instead of RST)
#   see  https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
extensions = ['myst_parser', 'sphinx.ext.autodoc', 'sphinx.ext.napoleon']

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
