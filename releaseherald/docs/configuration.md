# Configuration

`releaseherald` needs at least a known git repository to run. It can be provided as a command line
parameter `--git-dir path/to/git/dir`
or just simply running `releaseherlad` somewhere in a git repository. The root of the git repository is considered as
the place of the config files. If no config files exists it will run with defaults, which will be detailed in the
[Configurable Options](#configurable-options) section.

## Config files

`releaseherald` can read its config from either `releaseherald.toml`, or if that does not exist it check for a
`pyproject.toml` where it looks for the `[tool.releaseherald]` section. Of course the path to the config can be passed
from the command line as `--config path/to/config.file`



## [`base`](plugins/stock.md#base) plugin configuration
### `version_tag_pattern`

: The pattern is used to select the versions from the repository, it can have a group named `version` which, if present,
will be used as the version number, if no souch group then the whole label will be used.   
**_Default:_** `"(?P<version>(\d*)\.(\d*)\.(\d*))"`

### `news_fragments_directory`

: The path to the news fragment directory, if relative, it is relative to the repository root.  
**_Default:_** `news_fragment`

### `unreleased`

: If true a version named `Unreleassed` will be generated with the news fragments added since the last release toll the
current state of the repo.  
**_Default:_** `false`

### `last_tag`

: Last tag considered in the history. Only generate news for versions that happened after that version. It must
match [`version_tag_pattern`](#version_tag_pattern).  
**_Default_** `""`


## [`base_output`](plugins/stock.md#base_output) plugin configuration
### `news_file`

: Path of the base news file. This is the file that will be extended with the news for versions that `releaseherald`
generate. It must have an [`insert_marker`](#insert_marker) which is the point where the news will be inserted. The
other parts of the file is not tuched, so it can have a proper header, or even some old frozen version news.  
**_Default:_** `news.rst`

### `insert_marker`

: Regexp in the news file where the news need to be inserted. The generated news will be inserted under the matched line
leaving the line in the file.  
**_Default:_** `"^(\s)*\.\. releaseherald_insert(\s)*$"`

### `template`

: Path to the version template file. This is file should use Jinja syntax, and render the news for a single version. See
the details in [Version template](version_template.md)

### `target`

: Path to the target of the generated news file. If not provided the generated news will be dumped to stdout.  
**_Default:_** `None`

### `update`

: If false it only generates the version news but do not insert it into the news file template. Using `false` together
with [`latest`](#latest) one can generate a simple representation of the latest version, which is great for an
announcement mail/post.  
**_Default:_** `true`

## [`latest`](plugins/stock.md#latest) plugin configuration

### `latest`

: If true only render the latest version. Can be used if one always update the news file and commit that into git
repository.  
**_Default:_** `false`

## [`filename_metadata_extractor`](plugins/stock.md#filename_metadata_extractor) plugin configuration
### `filename_metadata_extractor`

: This setting configure the extraction of metadata from news file names. The extracted information made available 
through the [News][releaseherald.plugins.interface.News] metadata to the template.
::: releaseherald.plugins.metadata_extractor.FilenameMetadataExtractorConfig
    rendering:
        show_source: false 
        show_bases: false
        show_root_toc_entry: false
        members_order: source
        docstring_section_style: list 

## [`submodules`](plugins/stock.md#submodules) plugin configuration

## other configuration
### `plugins`

: The list of plugins enabled for this config. The base and base_ouput plugin that provide the basic behvior of 
releaseherald is always included unless `-base` and/or `-base-output` is added to the list. If not set then some of 
the stock plugins are autoloaded.  
**_Default:_** `[base, base_output, filename_metadata_extractor, latest, submodules]`
