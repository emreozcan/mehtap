import dunamai

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'mehtap'
copyright = '2024-2025, Emre Özcan'
author = 'Emre Özcan'
release = dunamai.Version.from_git().serialize()

# -- General configuration
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'myst_parser',
    'sphinx_copybutton',
    'sphinx_inline_tabs',
    'sphinx_tippy',
]

templates_path = ['_templates']
exclude_patterns = []

# -- MystParser

myst_enable_extensions = [
    'attrs_block',
    'colon_fence',
    'fieldlist',
    "tasklist",
]
myst_heading_anchors = 3
myst_enable_checkboxes = True

# -- Internationalization
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-gettext_uuid

gettext_uuid = True
gettext_compact = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

# -- Options for autodoc
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'show-inheritance': True,
}
autodoc_type_aliases: {
    'Multires': 'mehtap.operations.Multires',
    'PyLuaFunction': 'mehtap.py2lua.PyLuaFunction',
    'LuaDecorator': 'mehtap.py2lua.LuaDecorator',

    'PyLuaNative': 'mehtap.py2lua.PyLuaNative',
    'Py2LuaAccepts': 'mehtap.py2lua.Py2LuaAccepts',
    'PyLuaRet': 'mehtap.py2lua.PyLuaRet',
    'PyLuaWrapRet': 'mehtap.py2lua.PyLuaWrapRet',
    'LuaCallback': 'mehtap.py2lua.LuaCallback',
    'LuaScopeCallback': 'mehtap.py2lua.LuaScopeCallback',
    'PyCallback': 'mehtap.py2lua.PyCallback',
    'PyScopeCallback': 'mehtap.py2lua.PyScopeCallback',
}
autodoc_typehints = 'both'

# -- Options for intersphinx
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

