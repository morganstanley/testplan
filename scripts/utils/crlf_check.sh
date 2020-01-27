#!/bin/bash
# Look for any CRLF line terminators in source code. Outputs the name of any
# files containing CRLF and returns 1 if any are found, otherwise returns 0
# if no CRLF is found.
find . -path ./testplan/web_ui/testing/node_modules -prune -o -not -type d -exec file "{}" ";" | grep CRLF

if [[ $? == 0 ]]; then
    echo "CRLF found, please run scripts/utils/crlf_convert.py or fix manually"
    exit 1
else
    echo "No CRLF found."
    exit 0
fi
