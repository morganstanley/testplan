From now on Jinja2 is the template engine used for context values resolution. If a template does not conform to
Jinja2 then Tempita is used for fallback for a transition period, and a warning is displayed.
Tempita is considered deprecated, and it's support will be removed in an upcoming release. Please review your runs
for the warnings, if no warning then your templates are Jinja2 compatible and no work is needed,
else please update your templates