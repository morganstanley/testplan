`releaseherald` has a pluggable architecture, so it's behaviour can be extended/altered via plugins. In Fact the base 
functionality of `releaseherald` is given by the base plugin. [Pluggy](https://pluggy.readthedocs.io/) the pyunit's 
plugin framework is used to make it easy to write plugins. 

Plugins have access to the config file, so they can load their config from the single `releaseherald.toml` or 
`pyproject.toml`. They can register their own commandline options, so the user can tweak them from the cli if needed.  

The following diagram shows all the calls a plugin can attach to modify `releaseheralds` behavior. All details of 
these callbacks can be found in [Hooks](hooks.md)

``` mermaid
sequenceDiagram
    autonumber
    participant R as Releaseherald
    participant P as Plugin 1..N

    note over R: read config file
    note over R: load plugins

    rect rgba(0,0,255,.1)
    note over R: Plugin initialization phase
    R ->> P: process_config
    note over P: Initialize itself and update config

    loop for command cli commands
    R ->> P: get_command_options for command
    note over P: can register commandline options
    end

    R ->> P: on_start_command
    note over P: do any initialization and/or state management
    end
    
    rect rgba(0,255,0,.1)
    note over R: Command generate flow
    R ->> P: process_tags
    note over P: collect/update the list of tags representing versions
    R ->> P: process_commits
    note over P: turn the list of tags into list of commits

    loop for all commit pairs
        R ->> P: get_news_between_commits
        note over P: collect the news between two commits
        R ->> P: get_version_news
        note over P: assemble the news to a version avare structure
    end

    R ->> P: process_version_news
    note over P:a chanse to the plugin to alter all the news in one go
    R ->> P: generate_output
    note over P: generate output in memory
    R ->> P: write_output
    note over P: write the memory contect to disk/stdio ...
    end
```
