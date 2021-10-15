
{% for version in news %}
{# ================ version header ================ #}
{{ version.version }} ({{ version.date.strftime("%Y-%m-%d") }})
{{ "-" * ((version.version+version.date.strftime("%Y-%m-%d"))|length+3)}}

{# ================ version content ================ #}
{% for news_item in version.news %}
{{ news_item.content }}
{% endfor %}
{% for submodule in version.submodule_news %}
{% if submodule.news %}

Submodule {{ submodule.display_name }}
{{ "^" * (submodule.display_name|length+10)}}

{% for news_item in submodule.news %}
{{ news_item.content }}
{% endfor %}
{% endif %}
{% endfor %}

{% endfor %}