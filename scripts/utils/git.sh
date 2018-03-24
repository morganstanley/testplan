#! /usr/bin/env bash
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# util script to find out git related info

GIT_ROOT=$(git rev-parse --show-toplevel)
GIT_REF=$(git rev-parse --verify HEAD)

if git status -s | grep '^ M' &> /dev/null; then
    GIT_REF=$GIT_REF-dirty
fi

GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
