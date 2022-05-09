## A very basic example plugin 

This example just show the basics need to be around to build a plugin for releaseherald. The plugin is basicly a 
python package that define one or more entry_points under the group `releaseherald_plugin`. The entry point name is 
the name of the plugin, while the entry point itself should be a module or class instance that implements some of 
the [hooks](hooks.md)

``` toml title="setup.cfg" linenums="1"
--8<-- "example_plugin/setup.cfg"
```

``` toml title="pyproject.toml" linenums="1"
--8<-- "example_plugin/pyproject.toml"
```

``` py title="releaseherald_demo_plugin/__init__.py" linenums="1"
--8<-- "example_plugin/releaseherald_demo_plugin/__init__.py"
```
 
``` py title="releaseherald_demo_plugin/plugin.py" linenums="1"
--8<-- "example_plugin/releaseherald_demo_plugin/plugin.py"
```

## Commandline option example

The internal latest_filter plugin is a good simple example for how to add a commandline option to the `generate` 
command. It add a `--latest` switch the default is coming from 
[Configuration][releaseherald.configuration.Configuration]. If the option provided it remains just latest commit after 
[process_commits][releaseherald.plugins.hookspecs.process_commits]

``` py linenums="1"
--8<-- "releaseherald/plugins/latest_filter.py"
```