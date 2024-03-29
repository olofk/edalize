# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../tests/"))
sys.path.insert(0, os.path.abspath("../tests/test_vunit/vunit_mock/"))


# -- Project information -----------------------------------------------------

project = "Edalize"
copyright = "2019-{}, Olof Kindgren".format(datetime.now().year)
author = "Olof Kindgren"

# The short X.Y version
version = ""
# The full version, including alpha/beta/rc tags
release = "0.1.3"


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = "3.0"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.graphviz",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "vunit": ("https://vunit.github.io/", None),
}

# -- Options for HTML output -------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# The Read the Docs theme is available from
# https://github.com/snide/sphinx_rtd_theme
#
# Install with
# - pip install sphinx_rtd_theme
# or
# - apt-get install python-sphinx-rtd-theme

try:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
except ImportError:
    sys.stderr.write(
        "Warning: The Sphinx 'sphinx_rtd_theme' HTML theme was "
        + "not found. Make sure you have the theme installed to produce pretty "
        + "HTML output. Falling back to the default theme.\n"
    )

    html_theme = "alabaster"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "Edalizedoc"


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, "Edalize.tex", "Edalize Documentation", "Olof Kindgren", "manual"),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [(master_doc, "edalize", "Edalize Documentation", [author], 1)]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "Edalize",
        "Edalize Documentation",
        author,
        "Edalize",
        "Edalize is a Python Library for interacting with EDA tools.",
        "Miscellaneous",
    ),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ["search.html"]


# -- Extension configuration -------------------------------------------------

# Take class documentation from both __init__(), and the class docstring.
autoclass_content = "both"

from edalize.edatool import gen_tool_docs

s = gen_tool_docs()
with open(os.path.join(os.path.abspath("."), "edam/legacytools.rst"), "w") as f:
    f.write(s)

from importlib import import_module
from pkgutil import iter_modules

import edalize.flows


def make_rst_table(options):
    s = ""
    lines = []
    name_len = 10
    type_len = 4
    for name, item in options.items():
        _type = item["type"]
        if item.get("list"):
            _type = "List of " + _type
        name_len = max(name_len, len(name))
        type_len = max(type_len, len(_type))
        lines.append((name, _type, item["desc"]))

    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    s += "Field Name".ljust(name_len + 1) + "Type".ljust(type_len + 1) + "Description\n"
    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    for line in lines:
        s += line[0].ljust(name_len + 1)
        s += line[1].ljust(type_len + 1)
        s += line[2]
        s += "\n"
    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    return s


def iter_namespace(ns_pkg):
    # Specifying the second argument (prefix) to iter_modules makes the
    # returned name an absolute name instead of a relative one. This allows
    # import_module to work without having to do additional modification to
    # the name.
    return iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


discovered_plugins = {
    name: import_module(name) for finder, name, ispkg in iter_namespace(edalize.flows)
}

s = ""
table = {}
for k, v in discovered_plugins.items():
    name = k.split(".")[-1]
    if name == "edaflow":
        continue

    table[name] = {
        "type": f"`{name.capitalize()} flow`_",
        "desc": name + "-specific options",
    }
    _class = getattr(v, name.capitalize())
    s += "\n{} flow\n{}\n\n".format(name.capitalize(), "~" * (len(name) + 5))
    s += _class.__doc__ + "\n\n"
    s += f".. graphviz:: {name}.gv\n\n"
    s += make_rst_table(_class.get_flow_options())

with open(os.path.join(os.path.abspath("."), "edam/flows.rst"), "w") as f:
    f.write(s)  # make_rst_table(table)+s)

import edalize.tools

discovered_plugins = {
    name: import_module(name) for finder, name, ispkg in iter_namespace(edalize.tools)
}

s = ""
table = {}
for k, v in discovered_plugins.items():
    name = k.split(".")[-1]
    if name == "edatool":
        continue

    table[name] = {
        "type": f"`{name.capitalize()} tool`_",
        "desc": name + "-specific options",
    }
    _class = getattr(v, name.capitalize())
    s += "\n{} tool\n{}\n\n".format(name.capitalize(), "~" * (len(name) + 5))
    s += (_class.__doc__ or _class.description) + "\n\n"
    s += make_rst_table(_class.get_tool_options())

with open(os.path.join(os.path.abspath("."), "edam/tools.rst"), "w") as f:
    f.write(s)  # make_rst_table(table)+s)
