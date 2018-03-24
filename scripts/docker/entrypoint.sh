#! /usr/bin/env bash
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
# set -euo pipefail

if [[ $@ =~ .py ]]; then
    # User has provided a test_plan.py alternative, use that
    $@
elif [[ $1 == "bash" ]]; then
    bash
else
    ./test_plan.py $@
fi

exit 0
