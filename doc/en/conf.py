import sys
import os
from subprocess import check_output

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.path.join("..", "..")
    ),
)

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx_click"]

project = "Testplan"
copyright = "2018, Morgan Stanley"
author = ""

master_doc = "index"

pygments_style = "sphinx"
html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]

NEWS_FILE = "news.rst"
GENERATE_NEWS_COMMAND = "releaseherald generate "


def generate_news():
    news_content = check_output(GENERATE_NEWS_COMMAND, shell=True)

    with open(NEWS_FILE, "wb") as news_file:
        news_file.write(news_content)


def setup(app):
    app.add_stylesheet("icon.css")
    generate_news()
