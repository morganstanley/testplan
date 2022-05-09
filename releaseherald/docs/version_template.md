# Version template

`releaseherald` comes with a template based output generator in the [`base_output`](plugins/stock.md#base_output) 
plugin. It's using jinja2 as the template engine, see the template documentation on their 
[Template Designer](https://jinja.palletsprojects.com/en/3.1.x/templates/) page. There is a single stock template at 
the moment which more like serve as a demonstration purpose, but it is capable of generating a simple rst to be used 
out of the box. 

The template is fed with a context having a single `news` attribute, which is a list of 
[VersionNews][releaseherald.plugins.interface.VersionNews] that are collected and massaged by the various plugins 
during `generate` run. The template used can be configured from the [config file](configuration.md#template)

```rst title="stock rst news version template"
--8<-- "releaseherald/templates/news.rst"
```
The above template is iterating through the news and using the `version`, `date` attribute to form the version 
header. Then it's iterating through the news_items (representing the news files for a given version) to put their 
content into the result. It also has support for submodules as well.

``` rst title="an example output"
Unreleased (2021-12-15)
-----------------------

* 4th fragment (edited)

1.0.1 (2021-12-15)
------------------

* 3 after first release

Submodule herald_example_submodul
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* S2, for second release
* S3 some more newsp
* S1 first news
* S2, for first release

1.0.0 (2021-10-15)
------------------

* 1, before first release
* 2, before first release 
```

