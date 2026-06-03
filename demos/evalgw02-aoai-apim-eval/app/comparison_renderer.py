from IPython.display import HTML, display
import html
import json
import re

try:
    import markdown as markdown_lib
    HAS_MARKDOWN_LIB = True
except Exception:
    markdown_lib = None
    HAS_MARKDOWN_LIB = False


STYLE = """
<style>
.compare-wrap {
  font-family: Segoe UI, Tahoma, Arial, sans-serif;
  color: #e6edf3;
  font-size: 15px;
    text-align: left;
    margin: 0;
}
.compare-wrap h2,
.compare-wrap h3,
.compare-wrap p,
.compare-wrap li,
.compare-wrap strong,
.compare-wrap em {
  color: #f5f8fc;
    text-align: left;
}
.compare-wrap .category {
  margin: 24px 0 10px;
  padding-bottom: 6px;
  border-bottom: 2px solid #86c7ff;
  color: #9cd1ff;
}
.compare-wrap .card {
  margin: 12px 0;
  padding: 12px;
  background: #161b22;
  border: 1px solid #566273;
  border-radius: 8px;
}
.compare-wrap .title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.compare-wrap .title-row h3 {
    margin: 0;
}
.compare-wrap .badge-group {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
.compare-wrap .badge {
    background: #2d3f56;
    color: #eaf3ff;
    border: 1px solid #566273;
    border-radius: 999px;
    padding: 2px 9px;
    font-size: 12px;
    line-height: 1.4;
}
.compare-wrap .meta {
  margin: 0 0 8px;
  color: #d6e0eb;
  line-height: 1.5;
}
.compare-wrap table {
  width: 100%;
  border-collapse: collapse;
    margin: 0;
}
.compare-wrap th {
  padding: 10px 12px;
  text-align: left;
  background: #243142;
  color: #f0f7ff;
  border: 1px solid #566273;
}
.compare-wrap td {
  padding: 12px;
  vertical-align: top;
  border: 1px solid #566273;
    text-align: left;
}
.compare-wrap .primary,
.compare-wrap .secondary {
  background: #1e3a2a;
}
.compare-wrap .error {
  background: #4a2328;
}
.compare-wrap .note {
  margin-top: 10px;
  padding: 10px 12px;
  background: #1d2530;
  border-left: 3px solid #86c7ff;
  border-radius: 6px;
  color: #f5f8fc;
    line-height: 1.55;
}
.compare-wrap .markdown-body {
  line-height: 1.6;
    text-align: left;
}
.compare-wrap .markdown-body ul,
.compare-wrap .markdown-body ol {
  margin: 0.35rem 0 0.6rem 1.1rem;
  padding-left: 1rem;
}
.compare-wrap .markdown-body pre {
  background: #0f1720;
  border: 1px solid #566273;
  border-radius: 6px;
  padding: 10px;
  overflow-x: auto;
  white-space: pre-wrap;
  color: #f5f8fc;
}
.compare-wrap .markdown-body code,
.compare-wrap .pill {
  background: #314155;
  color: #f0f7ff;
  padding: 2px 5px;
  border-radius: 4px;
}
</style>
"""


def html_escape(text):
    return (
        str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('\n', '<br>')
    )


def render_inline_markdown(text):
    value = html.escape(text)
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)
    value = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', value)
    return value


def fallback_markdown_to_html(text):
    value = str(text or '')
    code_blocks = []

    def capture_code(match):
        code = html.escape(match.group(1).strip())
        token = f'__CODE_BLOCK_{len(code_blocks)}__'
        code_blocks.append((token, f'<pre><code>{code}</code></pre>'))
        return token

    value = re.sub(r'```(?:[a-zA-Z0-9_+-]+)?\n(.*?)```', capture_code, value, flags=re.S)

    lines = value.split('\n')
    rendered = []
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            rendered.append('</ul>')
            in_ul = False
        if in_ol:
            rendered.append('</ol>')
            in_ol = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('__CODE_BLOCK_') and stripped.endswith('__'):
            close_lists()
            rendered.append(stripped)
            continue
        if not stripped:
            close_lists()
            rendered.append('<br>')
            continue

        heading_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if heading_match:
            close_lists()
            level = len(heading_match.group(1))
            rendered.append(f'<h{level}>{render_inline_markdown(heading_match.group(2))}</h{level}>')
            continue

        unordered_match = re.match(r'^[-*]\s+(.*)$', stripped)
        if unordered_match:
            if in_ol:
                rendered.append('</ol>')
                in_ol = False
            if not in_ul:
                rendered.append('<ul>')
                in_ul = True
            rendered.append(f'<li>{render_inline_markdown(unordered_match.group(1))}</li>')
            continue

        ordered_match = re.match(r'^\d+\.\s+(.*)$', stripped)
        if ordered_match:
            if in_ul:
                rendered.append('</ul>')
                in_ul = False
            if not in_ol:
                rendered.append('<ol>')
                in_ol = True
            rendered.append(f'<li>{render_inline_markdown(ordered_match.group(1))}</li>')
            continue

        close_lists()
        rendered.append(f'<p>{render_inline_markdown(stripped)}</p>')

    close_lists()
    html_text = '\n'.join(rendered)
    for token, block in code_blocks:
        html_text = html_text.replace(token, block)
    return html_text


def markdown_to_html(text):
    if HAS_MARKDOWN_LIB:
        return markdown_lib.markdown(
            str(text or ''),
            extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists']
        )
    return fallback_markdown_to_html(text)


def difference_explanation(row):
    explicit_reason = row.get('difference_explanation') or row.get('evaluator_reason')
    if explicit_reason:
        return str(explicit_reason)

    primary_text = row.get('primary_response', '') or ''
    secondary_text = row.get('secondary_response', '') or ''
    category = row.get('category', '')

    if row.get('primary_status') != 'success' or row.get('secondary_status') != 'success':
        return 'At least one response failed, so compare reliability before style.'

    notes = []
    if len(primary_text) > len(secondary_text) * 1.2:
        notes.append('gpt-4o is more verbose')
    elif len(secondary_text) > len(primary_text) * 1.2:
        notes.append('gpt-5.1 is more verbose')
    else:
        notes.append('both are similar in length')

    if category == 'Structured Extraction':
        try:
            json.loads(primary_text)
            primary_json = True
        except Exception:
            primary_json = False
        try:
            json.loads(secondary_text)
            secondary_json = True
        except Exception:
            secondary_json = False

        if primary_json and secondary_json:
            notes.append('both keep the requested JSON shape')
        elif secondary_json and not primary_json:
            notes.append('gpt-5.1 is stricter about JSON formatting')
        elif primary_json and not secondary_json:
            notes.append('gpt-4o is stricter about JSON formatting')

    if category == 'Code Generation':
        primary_typed = any(token in primary_text for token in ['TypeVar', 'ParamSpec', 'Callable[', ': int', ': str'])
        secondary_typed = any(token in secondary_text for token in ['TypeVar', 'ParamSpec', 'Callable[', ': int', ': str'])
        if secondary_typed and not primary_typed:
            notes.append('gpt-5.1 adds more typed and defensive detail')
        elif primary_typed and not secondary_typed:
            notes.append('gpt-4o adds more typed and defensive detail')

    if category == 'Reasoning & Logic':
        notes.append('the main difference is explanation style')
    elif category == 'Creative Writing':
        notes.append('the main difference is voice and imagery')
    elif category == 'Instruction Following':
        notes.append('the main difference is format-vs-nuance balance')
    elif category == 'Ambiguity Handling':
        notes.append('the main difference is proactive disambiguation')

    return '; '.join(notes)


def render_card(row):
    primary_html = markdown_to_html(row.get('primary_response', ''))
    secondary_html = markdown_to_html(row.get('secondary_response', ''))
    primary_class = 'primary' if row['primary_status'] == 'success' else 'error'
    secondary_class = 'secondary' if row['secondary_status'] == 'success' else 'error'
    system_label = row.get('system_label', 'System')
    user_label = row.get('user_label', 'User')
    difference_label = row.get('difference_label', 'Difference explanation')
    badges = row.get('badges', []) or []
    badges_html = ''.join(f'<span class="badge">{html_escape(b)}</span>' for b in badges)

    return f"""
<div class="card">
    <div class="title-row">
        <h3>[{html_escape(row['scenario_id'])}] {html_escape(row['category'])}</h3>
        <div class="badge-group">{badges_html}</div>
    </div>
    <p class="meta"><b>{html_escape(system_label)}:</b> {html_escape(row['system'])}</p>
    <p class="meta"><b>{html_escape(user_label)}:</b> {html_escape(row['user'])}</p>
  <table>
    <thead>
      <tr>
        <th>gpt-4o - <span class="pill">{html_escape(row['primary_deployment'])}</span></th>
        <th>gpt-5.1 - <span class="pill">{html_escape(row['secondary_deployment'])}</span></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="{primary_class}"><div class="markdown-body">{primary_html}</div></td>
        <td class="{secondary_class}"><div class="markdown-body">{secondary_html}</div></td>
      </tr>
    </tbody>
  </table>
    <div class="note"><b>{html_escape(difference_label)}:</b><br>{html_escape(difference_explanation(row))}</div>
</div>
"""


def render_comparison(results):
    current_category = None
    parts = [
        STYLE,
        '<div class="compare-wrap">',
        '<h2 style="margin:0 0 10px 0; color:#f0f6fc;">Model Comparison Results: gpt-4o vs gpt-5.1</h2>'
    ]

    for row in results:
        if row['category'] != current_category:
            current_category = row['category']
            parts.append(f'<h2 class="category">{html_escape(current_category)}</h2>')
        parts.append(render_card(row))

    parts.append('</div>')
    display(HTML(''.join(parts)))