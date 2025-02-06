# Stock plugins

`releaseherald` is coming with some stock plugins, if you do not configure your own list of plugins they are all 
enabled, and can be configured through [Configuration](../configuration.md)

## base
This plugin defines the base functionality of `releaseherald` it is responsible to collect the news fragments based 
on the configuration. Even if someone set their own list of plugins base is added automatically (unless `-base` is 
on the list). Other plugins can depend on this default behaviour and extend,alter it as needed.  
[/configuration/](../configuration.md#base-plugin-configuration)

## base_output
This plugin responsible to render the news into an output based on a jinja2 template. This added automatically to 
the list of plugins even if not mentioned in the config, though if a plugin implement their own rendering this can 
be removed adding `-base_output` to the list of plugins.  
[/configuration/](../configuration.md#base_output-plugin-configuration)

## latest
This is a simple plugin, it adds the `--latest` commandline switch for generate and understand the 
`latest` configuration setting. If it is triggered it will trim down the list of version for just the latest 
in the list. Can be used for generating content for announce mail with just the latest changes.  
[/configuration/](../configuration.md#latest-plugin-configuration)

## filename_metadata_extractor
This plugin can be configured to extract extra data from the file name of the news file and make it available for 
the jinja2 template. It can be configured through the config file, and it supports two parser, the simple [parse 
library](https://github.com/r1chardj0n3s/parse#readme) and 
[regexp](https://docs.python.org/3/library/re.html#regular-expression-syntax). The named fields defined in the parse 
syntax, or named groups from the regexp are injected to the [News][releaseherald.plugins.interface.News] metadata 
dictionary, which is available for the template during render time and can be referred like the following example.

``` toml title="configuration with parse"
[filename_metadata_extractor]
type = "parse"
pattern = '{id}_{description}.rst'
```
cr the same with regexp

``` toml title="configuration with regexp"
[filename_metadata_extractor]
type = "re"
pattern = '(?P<id>[^_]*)_(?P<desc>.*)\.rst'
```

``` jinja2 title="template"
{% for news_item in version.news %}
{{ news_item.content }}
Fixed isse #{{ news_item.metadata.id}}
{% endfor %}
```

``` title="rendered result"
...content of the news file...
Fixed issue #12
```

it assume that the news file has filenames like this `12_fix_the_bug.rst`.  
[/configuration/](../configuration.md#filename_metadata_extractor-plugin-configuration)

## submodules

If there are submodules in the git repo, with this plugin it is possible to collect news fragments from the 
submodules as well and integrate it into the main repos release notes. The plugin collect the news fragments between 
the submodule commits, that is referenced from the main repo's commits representing a version. The plugin can 
collect fragments from more than one repo.

``` toml title="example configuration with two submodules"
[[submodules]]
name="herald_example_submodule"
display_name="Example"

[[submodules]]
name="submodule2"
display_name="The Secret sauce"
news_fragments_directory="the_news"

```

[/configuration/](../configuration.md#submodules-plugin-configuration)