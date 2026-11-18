"""Build-only navigation shell and template avatars; never edit note sources."""
from __future__ import annotations

from html import escape, unescape
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from mkdocs.utils import get_relative_url
from bs4 import BeautifulSoup
from tools.optimized_images import derive_image
from tools.preview_stages import transform_text


_PAGES = []
_EAGER_PAGES = None


def on_nav(nav, /, *, config, files):
    global _PAGES, _EAGER_PAGES
    _PAGES = list(files.documentation_pages())  # Keep File refs: orphan Pages are populated later.
    _EAGER_PAGES = None
    return nav


def _label(value):
    return ' '.join(unescape(re.sub(r'<[^>]*>', '', str(value or ''))).split())


def _iter_options(nodes, page_url, parents=()):
    for node in nodes:
        title = _label(node.title)
        if getattr(node, 'is_page', False) or getattr(node, 'is_link', False):
            url = str(getattr(node, 'url', '') or '')
            if url and urlsplit(url).scheme not in ('javascript', 'data'):
                href = url if urlsplit(url).scheme or url.startswith('/') else get_relative_url(url, page_url)
                yield {'label': ' / '.join((*parents, title)), 'href': href,
                       'current': bool(getattr(node, 'active', False))}
        elif getattr(node, 'children', None):
            yield from _iter_options(node.children, page_url, (*parents, title))


def _library_terms(nav, page_url):
    """Group only published navigation entries, including handouts and PDF links."""
    terms = {}
    for item in _iter_options(nav.items, page_url):
        href = item['href'].replace('\\', '/')
        parts = unquote(href).split('/')
        if len(parts) < 3 or parts[0] != 'md':
            continue
        has_term = re.fullmatch(r'\d{3}-[12]', parts[1]) and len(parts) >= 4
        term, course = (parts[1], parts[2]) if has_term else ('專題', parts[1])
        notes = terms.setdefault(term, {}).setdefault(course, [])
        notes.append({'href': href, 'title': item['label'].rsplit(' / ', 1)[-1]})
    return terms


def on_page_context(context, /, *, page, config, nav):
    global _EAGER_PAGES
    if _EAGER_PAGES is None:
        native_features = config['theme'].get('features', [])
        eager_global = any(name in native_features for name in ('content.code.select', 'content.code.annotate'))
        _EAGER_PAGES = [item.url for item in (file.page for file in _PAGES if file.page) if
                        (eager_global and '<pre' in str(item.content or '')) or
                        re.search(r'class=["\x27][^"\x27]*\b(?:annotate|select)\b', str(item.content or ''))]
    context['peicd_eager_links'] = json.dumps([get_relative_url(url, page.url) for url in _EAGER_PAGES], ensure_ascii=False).replace('<', '\\u003c')
    if page.file.src_uri == 'index.md':
        context['library_terms'] = _library_terms(nav, page.url)
    # The shell exists before the first paint. Option lists are built on demand.
    top = next((item for item in nav.items if getattr(item, 'active', False)), None)
    if top is None:
        return context
    pages = list(_iter_options(getattr(top, 'children', None) or [top], page.url))
    current = next((item for item in pages if item['current']), None)
    if current is None:
        return context
    courses = []
    for item in nav.items:
        first = next(_iter_options(getattr(item, 'children', None) or [item], page.url), None)
        if first:
            courses.append({'label': _label(item.title), 'href': first['href'], 'current': item is top})
    groups = [(_label(top.title), courses, '切換課程'), (current['label'], pages, '切換頁面')]
    src = str(getattr(page.file, 'src_uri', ''))
    semester = re.search(r'(?:^|/)(\d{3}-[12])/', src)
    prefix = semester.group(1) if semester else '筆記'
    parts = [f'<nav class="peicd-folder-pathbar" aria-label="目前筆記位置" data-peicd-pathbar="server"><span class="peicd-folder-pathbar__prefix">{escape(prefix)}</span>']
    for index, (title, items, caption) in enumerate(groups):
        identifier = f'peicd-path-menu-{index}'
        options = escape(json.dumps(items, ensure_ascii=False, separators=(',', ':')), quote=True)
        parts.append(f'<span class="peicd-folder-pathbar__separator" aria-hidden="true">/</span><div class="peicd-folder-pathbar__item" data-peicd-options="{options}"><button type="button" class="peicd-folder-pathbar__toggle" aria-expanded="false" aria-controls="{identifier}" aria-label="{caption}：{escape(title, quote=True)}"><span class="peicd-folder-pathbar__label">{escape(title)}</span><span class="peicd-folder-pathbar__caret" aria-hidden="true">▾</span></button><div class="peicd-folder-pathbar__menu" id="{identifier}" hidden data-caption="{caption}"></div></div>')
    parts.append('</nav>')
    context['peicd_pathbar'] = ''.join(parts)
    return context


_AUTHOR_IMAGE = re.compile(r'(<(?:a|span)\b[^>]*\bclass="[^"]*\bmd-author\b[^"]*"[^>]*>\s*)(<img\b[^>]*>)', re.I)


def _stable_toc(output, page_key=''):
    # Only parse the sidebar fragment, never the large article/code body.
    start = output.find('<div class="md-sidebar md-sidebar--secondary"')
    end = output.find('<div class="md-content"', start) if start >= 0 else -1
    if end < 0:
        return output
    sidebar = transform_text(_toc_fragment, output[start:end], page_key)
    return output[:start] + sidebar + output[end:]


def _toc_fragment(fragment):
    soup = BeautifulSoup(fragment, 'html.parser')
    sidebar = soup.select_one('.md-sidebar--secondary')
    nav = sidebar.select_one('.md-nav--secondary') if sidebar else None
    if nav is None or nav.select_one('[data-md-component="toc"]') is None:
        return fragment
    sidebar['class'] = list(dict.fromkeys([*sidebar.get('class', []), 'peicd-toc-sidebar']))
    sidebar['data-peicd-toc-mode'] = 'auto'
    sidebar['data-peicd-toc-view'] = 'toc'
    title = nav.select_one('.md-nav__title')
    if title:
        title['class'] = list(dict.fromkeys([*title.get('class', []), 'peicd-toc-title']))
        title.attrs.pop('for', None)
        title.clear()
        title['hidden'] = ''
        title['aria-hidden'] = 'true'
    head = soup.new_tag('div', attrs={'class': 'peicd-toc-head', 'data-peicd-toc-shell': 'server', 'aria-busy': 'true'})
    row = soup.new_tag('div', attrs={'class': 'peicd-toc-head__row peicd-toc-head__row--titleless'})
    if title:
        row.append(title.extract())
    close = soup.new_tag('button', attrs={'type': 'button', 'class': 'peicd-toc-close', 'disabled': '', 'aria-label': '關閉目錄'})
    close.string = '×'
    row.append(close)
    head.append(row)
    toolbar = soup.new_tag('div', attrs={'class': 'peicd-toc-toolbar'})
    for label, names in [('目錄操作', ['展開', '收合']), ('目錄模式', ['自動', '手動'])]:
        group = soup.new_tag('div', attrs={'class': 'peicd-toc-toolbar__group', 'role': 'group', 'aria-label': label})
        for name in names:
            attrs = {'type': 'button', 'class': 'peicd-toc-control', 'disabled': ''}
            if label == '目錄模式':
                attrs.update({'class': 'peicd-toc-control peicd-toc-control--mode', 'aria-pressed': str(name == '自動').lower()})
            button = soup.new_tag('button', attrs=attrs)
            button.string = name
            group.append(button)
        toolbar.append(group)
    danger = soup.new_tag('button', attrs={'type': 'button', 'class': 'peicd-toc-control peicd-toc-control--danger', 'aria-pressed': 'false', 'disabled': ''})
    danger.string = 'Danger'
    toolbar.append(danger)
    head.append(toolbar)
    nav.insert(0, head)
    for item in nav.select('li.md-nav__item'):
        if item.select_one(':scope > nav.md-nav') and item.select_one(':scope > a.md-nav__link'):
            item['class'] = list(dict.fromkeys([*item.get('class', []), 'peicd-toc-item--nested', 'peicd-toc-item--collapsed']))
    # Existing resetSidebar adopts the title and replaces this disabled shell.
    fallback = BeautifulSoup('<noscript><style>.md-sidebar--secondary .peicd-toc-head{display:none}.md-sidebar--secondary .peicd-toc-item--collapsed>nav{display:block!important}</style></noscript>', 'html.parser')
    sidebar.append(fallback)
    return str(soup)


def on_post_page(output, /, *, page, config):
    output = _stable_toc(output, page.file.src_uri)
    docs = Path(config['docs_dir']).resolve()
    def avatar(match):
        image = BeautifulSoup(match[2], 'html.parser').img
        parsed = urlsplit(str(image.get('src') or ''))
        if parsed.scheme or parsed.netloc or not parsed.path:
            return match[0]
        source = (docs / Path(page.url).parent / unquote(parsed.path)).resolve()
        if not source.is_relative_to(docs) or not source.is_file():
            return match[0]
        derived = derive_image(source, config, logo=True)
        if not derived:
            return match[0]
        image['src'] = get_relative_url(derived['url'], page.url)
        image['width'] = image['height'] = '32'
        image['decoding'] = 'async'
        image['loading'] = 'lazy'
        return match[1] + str(image)
    output = _AUTHOR_IMAGE.sub(avatar, output)
    return output
