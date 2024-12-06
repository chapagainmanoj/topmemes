#!/usr/bin/env bash

DIRECTORY=.venv
deactivate 2> /dev/null
if [ -d "${DIRECTORY}" ]; then
    source ${DIRECTORY}/bin/activate
else
    python -m venv ${DIRECTORY}
    source ${DIRECTORY}/bin/activate
fi
