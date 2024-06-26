# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import sphinx_rtd_theme
from sphinx_markdown_builder.builder import MarkdownBuilder
sys.path.insert(0, os.path.abspath('../../home_security_surveillance'))

project = 'home_security_surveillance'
copyright = '2024, 07xiaohei、youyou、Chai.h、Captain'
author = '07xiaohei、youyou、Chai.h、Captain'
release = '1.5'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'recommonmark',
    'sphinx_markdown_tables'
]

builders = [
    'html',
    'markdown',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'zh_CN'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ['_static']
