Feature: Parsers example

    Show how parsers can be used to match sentences and capture parameters

    Scenario: Simple parser

        Simple parser can parse with the "parse" python library,
        - all sentence with _SP will be matched by SimpleParser
        - all sentence with _RP will be matched by RegExParser



        Given _SP explicit match
        Given _RP explicit match

        # with capture
        Given _SP explicit match and log name: Simple John
        Given _RP explicit match and log name: Regular Gil

        Given _RP as default match
        Given _RP as default match and log name: Regular Gil

        Given _SP as override match
        Given _SP as override match and log name: Simple John

        # RP can do regexp tricks easily to match different sentence to the same
        Given _RP to match this
        And   _RP and this too