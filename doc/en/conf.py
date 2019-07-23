import sys
import os

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.path.join('..', '..')))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode'
]

project = 'Testplan'
copyright = '2018, Morgan Stanley'
author = ''

master_doc = 'index'

pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']


# pylint: disable=unused-argument
# def skip(app, what, name, obj, would_skip, options):
#     if name == '__init__':
#         return False
#     return would_skip

def setup(app):
    app.add_stylesheet('icon.css')
    #app.connect('autodoc-skip-member', skip)
