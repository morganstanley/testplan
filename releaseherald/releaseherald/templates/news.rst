
{% for version in news %}
{# ================ version header ================ #}
{{ version.version }} ({{ version.date.strftime("%Y-%m-%d") }})
{{ "=" * ((version.version+version.date.strftime("%Y-%m-%d"))|length+3)}}

{# ================ version content ================ #}
{% for news_item in version.news %}
{{ news_item.content }}
{% endfor %}

{% endfor %}