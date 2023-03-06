{% macro render_news_item(news_item) -%}
* {% if not news_item.metadata.get('type') is none %}:{{news_item.metadata.type}}:`{{news_item.metadata.type|capitalize}}` {%endif%}{{ news_item.content | indent(width=2) }}
{%- endmacro %}

{% for version in news %}
{# ================ version header ================ #}
.. _rev_{{version.version}}:


{{ version.version }} ({{ version.date.strftime("%Y-%m-%d") }})
{{ "-" * ((version.version+version.date.strftime("%Y-%m-%d"))|length+3)}}

{# ================ version content ================ #}
{% for news_item in version.news %}
{{render_news_item(news_item)}}
{% endfor %}

{% endfor %}