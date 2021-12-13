# Introduction

`releseherald` is a utility that can generate release notes for your project. The only help it needs from you is to
collect meaningful news fragments in a directory, and apply consistent labels on your git repo.

> -- Wait a bit I have already heard this somewhere.  
> -- Yes we were really inspired by [towncrier](https://github.com/twisted/towncrier), but we had a bit different opinions

## Philosophy

We very much agree [towncrier's philosophy](https://github.com/twisted/towncrier#Philosophy):
that release notes should be convenient to read. But still release notes should be easy to work with. And that is where
`towncrier's` news fragments shines. Ideally every pull request should come with an update of the release notes, if this
is a single file then one always run into merge conflicts, if each pr has its own news fragments, then this is easily
avoidable. `towncrier` has a couple of opinions which work very good on github, but might not so great on other
environments. `releaseherald` try to be less opinionated yet easy to extend. We try to have just three opinions:

- your stuff is in a git repo
- the release notes for a version is fabricated from the news fragments created/modified between that two release
- the releases number can be worked out from git labels

## Basics

`releaseherald` is a command line tool it needs python 3.7+ to run, but it can be used in any git project. It needs a
config file in the root of the git repo it should be called `releaseherald.toml`. If it is used in a python project it
can read it's configuration from `pyproject.toml` from `[tool.releaseherald]`. It is possible to start without any
configuration, then one need to create a `news_fragment` directory in the root of the git repo and a `news.rst` file
which should contain a news file something like this:

```rst
Release Notes
=============

  .. releaseherald_insert
```

As `releaseherald` working with diffs between labels so if you do not have labels yet just create one
named `RELEASEHERALD_ROOT` you should start collecting news fragments into the `nesw_fragment` directory, commit them
and label your releases with following [semantic versioning](https://semver.org/) principles. Once you have some commits
and news fragments you can generate your release notes as `releaseherald generate` this will result something like this:

```rst
Release Notes
=============

.. releaseherald_insert

1.0.0 (2021-10-15)
------------------

* 1, before first release
* 2, before first release
```

Here it is, you can start to integrate it into your CI. As I said this tool try not to have many opinions, so all the 
above default can be tweaked through configuration or command line. You do not even need to remove new_fragments between releases,
or commit the generated release notes, as `releaseherald` works that out from git history, though if you want you
can do that as well.