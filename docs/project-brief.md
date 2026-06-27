---
layout: literature
title: Projektbrief
permalink: /project-brief/
---

{% capture framework_markdown %}
{% include_relative project-framework.md %}
{% endcapture %}
{{ framework_markdown | markdownify }}
