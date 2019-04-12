#!/usr/bin/env python
import os
import re
import json


def match_regexps_in_file(logpath, log_extracts):
    """
    Return a boolean, dict pair indicating whether all log extracts matches,
    as well as any named groups they might have matched.
    """
    extracted_values = {}
    if not os.path.exists(logpath):
        return False, extracted_values

    extracts_status = [False for _ in log_extracts]

    with open(logpath, 'r') as log:
        for line in log:
            for pos, regexp in enumerate(log_extracts):
                match = regexp.match(line)
                if match:
                    extracted_values.update(match.groupdict())
                    extracts_status[pos] = True

    return all(extracts_status), extracted_values

try:
    config = os.path.join('etc', 'config.yaml')
    regexps = [re.compile(r'.*binary: (?P<binary>.*)'),
               re.compile(r'.*command: (?P<command>.*)'),
               re.compile(r'.*app_path: (?P<app_path>.*)')]
    result, extracts = match_regexps_in_file(config, regexps)
    if result is True:
        print('Config values:')
        print('binary={}'.format(extracts['binary']))
        print('command={}'.format(json.dumps(extracts['command'])))
        print('app_path={}'.format(extracts['app_path']))
except Exception as exc:
    print(exc)

print('Binary started')
print('Binary=started')
