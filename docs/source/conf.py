import sys
from pathlib import Path

sys.path.insert(0, str(Path('..', 'src').resolve()))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ay'
copyright = '2024, Emre Özcan'
author = 'Emre Özcan'
version = __import__('ay').__version__

# -- General configuration
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ['_static']

# -- Options for autodoc
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'show-inheritance': True,
}
autodoc_type_aliases: {
    'Multires': 'ay.operations.Multires',
    'Py2LuaAccepts': 'ay.py2lua.Py2LuPy2LuaAccepts',
    'PyLuaRet': 'ay.py2lua.PyLuaRet',
    'PyLuaWrapRet': 'ay.py2lua.PyLuaWrapRet',
    'PyLuaFunction': 'ay.py2lua.PyLuaFunction',
    'LuaDecorator': 'ay.py2lua.LuaDecorator',
}
autodoc_typehints = 'both'

# -- Options for intersphinx
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

