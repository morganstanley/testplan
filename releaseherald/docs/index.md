# Introduction

`releaseherald` is a Testplan internal utility that can generate release notes for Testplan. The only help it needs from
developers is to collect meaningful news fragments in a directory, and apply consistent labels.

> -- Wait a bit I have already heard this somewhere.  
> -- Yes we were really inspired by [towncrier](https://github.com/twisted/towncrier), but we had a bit different opinions

## Philosophy

We very much agree with [towncrier's philosophy](https://github.com/twisted/towncrier#Philosophy):
that release notes should be convenient to read. But still release notes should be easy to work with. And that is where
`towncrier's` news fragments shines. Ideally every pull request should come with an update of the release notes, if this
is a single file then one always run into merge conflicts, if each pr has its own news fragments, then this is easily
avoidable. `towncrier` has a couple of opinions which work very well on GitHub, but might not work so great in other
environments. `releaseherald` try to be less opinionated yet easy to extend. We try to have just three opinions:

- version control in git
- the release notes for a version is fabricated from the news fragments created/modified between that two release
- the releases number can be worked out from git labels

## Concept

The bellow diagramm try to explain the concept and show off the various data that flows into `releaseherald`.
```mermaid
flowchart LR
    subgraph G[Git Repo]
        subgraph L1[Change since LABEL 0.9.1]
            direction LR

            L1C3[Commit 3 LABEL: 1.0.0]
            L1C2[Commit 2]
            L1C1[Commit 1]

            C3N2[news4.srt]
            C3N1[news3.srt]
            C2N1[news2.srt]
            C1N1[news1.srt]

            L1C3 --- C3N2
            L1C3 --- C3N1            
            L1C2 --- C2N1
            L1C1 --- C1N1

            
        end

        subgraph L2 [Change since LABEL 0.7.0]
            direction LR
            L2C3[Commit 3 LABEL: 0.9.1] 
            L2C2[Commit 2] 
            L2C1[Commit 1] 

            L2C3N1[news3.srt]
            L2C2N1[news2.srt]
            L2C1N1[news1.srt]

            L2C3 --- L2C3N1            
            L2C2 --- L2C2N1
            L2C1 --- L2C1N1
        end
        subgraph L3 [Earlier changes]
            direction LR
            L3C2[Commit N LABEL: 0.7.0 ...]             
        end

    end

    subgraph S[Sourcetree]
        RC[releaseherald.toml\nconfiguration]
        RT["releasenote_template\n\nVersion {version_num}\n{list_of_news ...}"]
        subgraph PRN[Previous releasenotes]
            direction LR
            PRNP[#Placeholder#]
            PRN1[Version 0.7.0 ...]
            PRN2[Version 0.6.3 ...]
            PRN2[Version 0.6.0 ...]
        end
    end


    RH[Releaseherald]
    
    L1 --> RH 
    L2 --> RH

    RC --> RH
    RT ---> RH
    PRN ---> RH

    subgraph N[New releasenotes]
        direction LR
        NRNP[#Placeholder#]
        NRN1[Version 1.0.0\nnews1\nnews2\nnews3\nnews4]        
        NRN2[Version 0.9.1\nnews1\nnews2\nnews3]
        NRN3[Version 0.7.0 ...]
        NRN4[Version 0.6.3 ...]
        NRN5[Version 0.6.0 ...]
    end

    RH --> N

    N --> RE[Send in email]
    N --> RU[Add to GitHub release]
    N --> RS[Update in source and commit to git]

    style L1 fill:#f003
    style NRN1 fill:#f003    
    style L2 fill:#0f03
    style NRN2 fill:#0f03

```

## Basics

`releaseherald` is a command line tool it needs python 3.7+ to run. It needs a config file in the root of the git repo
it should be called `releaseherald.toml`. If it is used in a python project it can read it's configuration
from `pyproject.toml` from `[tool.releaseherald]`. It is possible to start without any configuration, then one needs to
create a `news_fragment` directory in the root of the git repo and a `news.rst` file which should contain a news file
something like this:

``` rst
Release Notes
=============

  .. releaseherald_insert
```

As `releaseherald` working with diffs between labels so if no labels yet in the repo just create one
named `RELEASEHERALD_ROOT`. News fragments should be added to the `nesw_fragment` directory, commiting them, and
merged (preferably with a pull request). When releasing a label need to be created with
following [semantic versioning](https://semver.org/) principles. Once there are some commits and news fragments release
notes can be generated as `releaseherald generate`. This will result something like this:

``` rst
Release Notes
=============

.. releaseherald_insert

1.0.0 (2021-10-15)
------------------

* 1, before first release
* 2, before first release
```

This tool try not to have many opinions, so all the above defaults can be tweaked through configuration or command line.
New fragments do not need to be removed between releases, no need to commit the generated release notes either,
as `releaseherald`
works that out from git history, though if that fits better to the workflow it can be done.
