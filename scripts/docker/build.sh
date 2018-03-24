#! /usr/bin/env bash
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

function usage {
    cat << EOF
    Build the docker image for testplan.

    usage:
        $0

    args:
        -i VERSION      Python version to build for. For example: 3, 3.6, 2.7
        -p

    examples:
        To build a container for python 3.6 and push the images back to dockerhub.io:

        $0 -i 3.6 -p
EOF
}

PUSH=0
DOCKER_IMAGE=mhristof/testplan

while getopts "i:ph" OPTION
do
     case $OPTION in
         i) PY_VERSION="$OPTARG";;
         p) PUSH=1;;
         h) usage; exit 1 ;;
     esac
done


PY_VERSION=${PY_VERSION:-2}
source $(dirname "$0")/../utils/git.sh

# Dockerfile is generated at git root folder as `docker` cannot `ADD` file that
# are not under the folder its in.
sed -e "s/%{PYTHON_VERSION}/$PY_VERSION-jessie/g" "$(dirname "$0")/Dockerfile.template" > "$GIT_ROOT/Dockerfile"

if [[ $GIT_BRANCH != "master" ]]; then
    DOCKER_TAG="$PY_VERSION-$GIT_BRANCH"
fi

docker build -t "$DOCKER_IMAGE:$DOCKER_TAG" "$GIT_ROOT"
docker tag "$DOCKER_IMAGE:$DOCKER_TAG" "$DOCKER_IMAGE:$DOCKER_TAG-$GIT_REF"

if [[ $PUSH -eq 1 ]]; then
	docker push "$DOCKER_IMAGE:$DOCKER_TAG"
	docker push "$DOCKER_IMAGE:$DOCKER_TAG-$GIT_REF"
fi

exit 0
