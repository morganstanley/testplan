"""
Module of utility types and functions that perform matching.
"""
import os


def match_regexps_in_file(logpath, log_extracts, return_unmatched=False):
    """
    Return a boolean, dict pair indicating whether all log extracts matches,
    as well as any named groups they might have matched.
    """
    extracted_values = {}

    if not os.path.exists(logpath):
        if return_unmatched:
            return False, extracted_values, log_extracts
        return False, extracted_values

    extracts_status = [False for _ in log_extracts]

    with open(logpath, 'r') as log:
        for line in log:
            for pos, regexp in enumerate(log_extracts):
                match = regexp.match(line)
                if match:
                    extracted_values.update(match.groupdict())
                    extracts_status[pos] = True

    if return_unmatched:
        unmatched = [
            exc for idx, exc in enumerate(log_extracts)
            if not extracts_status[idx]
        ]
        return all(extracts_status), extracted_values, unmatched
    return all(extracts_status), extracted_values
