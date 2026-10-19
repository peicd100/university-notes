"""Regressions for streaming image handling and per-page search reuse."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from PIL import Image
from material.plugins.search.plugin import SearchIndex
from mkdocs.config import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.toc import get_toc
from tools import image_lazy_loading_hook as images
from tools.serve_site import RenderCache, SearchCache, _stable


class StreamingImagesTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()
        Image.new('RGB', (120, 80), 'blue').save(self.root / 'docs/image.png')
        self.config = {'docs_dir': str(self.root / 'docs'), 'site_dir': str(self.root / 'site'),
                       'config_file_path': str(self.root / 'mkdocs.yml')}

    def tearDown(self):
        self.temp.cleanup()

    def page(self):
        return SimpleNamespace(meta={}, url='folder/page.html', file=SimpleNamespace(src_uri='folder/page.md'))

    def assert_parity(self, html):
        fast, reference = self.page(), self.page()
        actual = images.on_page_content(html, page=fast, config=self.config, files=None)
        expected = images._soup_page_content(html, page=reference, config=self.config, files=None)
        self.assertEqual(BeautifulSoup(actual, 'html.parser').decode(),
                         BeautifulSoup(expected, 'html.parser').decode())
        self.assertEqual(fast.meta, reference.meta)
        return actual, fast

    def test_rich_html_matches_reference_and_preserves_unrelated_bytes(self):
        html = ('<details open><summary title="x &amp; y">Title</summary>\r\n'
                '<p class="arithmatex">\\(x &lt; y\\)</p><pre class="diagram">A--&gt;B</pre>'
                '<div data-peicd-markdown-embed="x"><table><tr><td>&nbsp;文字</td></tr></table></div>'
                '<img\r\n src="../image.png=50%x" loading="lazy" title="a > b &amp; c">'
                '<img src="https://example.test/a.jpg" loading="eager"></details>')
        output, page = self.assert_parity(html)
        self.assertTrue(output.startswith(html[:html.index('<img')]))
        self.assertTrue(page.meta['peicd_has_math'])
        self.assertTrue(page.meta['peicd_has_mermaid'])
        self.assertTrue(page.meta['peicd_has_markdown_embed'])

    def test_only_article_images_count_and_parent_void_tags_do_not_leak(self):
        html = ('<span class="twemoji"><br><img src="emoji.svg"></span>'
                '<img class="twemoji" src="emoji.svg"><img class="peicd-image-viewer__img" src="x">'
                '<img class="peicd-mermaid-viewer__svg" src="x"><img src=""><img>'
                '<img src="../image.png" loading="lazy"><hr><img src="missing.jpg">')
        output, _ = self.assert_parity(html)
        article = BeautifulSoup(output, 'html.parser').select('img[src="missing.jpg"]')[0]
        self.assertEqual(article['loading'], 'lazy')

    def test_comments_code_scripts_and_style_do_not_create_features(self):
        html = ('<!-- <img src="bad"> <div class="arithmatex"> -->'
                '<script>const x = \'<img src="bad"><pre class="diagram">\';</script>'
                '<style>/* <div data-peicd-markdown-embed> */</style>'
                '<pre><code>&lt;img src="bad"&gt; &lt;b class="arithmatex"&gt;</code></pre>')
        output, page = self.assert_parity(html)
        self.assertFalse(any(page.meta.values()))
        self.assertEqual(output, html)

    def test_no_images_never_constructs_a_full_soup(self):
        html = '<section class="arith&#109;atex"><div class="peicd-mermaid-host"/></section>'
        page = self.page()
        with patch.object(images, 'BeautifulSoup', side_effect=AssertionError('no tree needed')):
            self.assertEqual(images.on_page_content(html, page=page, config=self.config, files=None), html)
        self.assertTrue(page.meta['peicd_has_math'])
        self.assertTrue(page.meta['peicd_has_mermaid'])

    def test_base64_output_flags_and_generated_bytes_match(self):
        raw = (self.root / 'docs/image.png').read_bytes()
        source = 'data:image/png;base64,' + base64.b64encode(raw).decode()
        _, page = self.assert_parity(f'<img src="{source}"><img src="{source}">')
        self.assertEqual(page.meta['peicd_externalized_images'], 2)
        generated = list((self.root / 'site/assets/generated/base64-images').rglob('*.png'))
        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0].read_bytes(), raw)

    def test_malformed_markup_uses_compatibility_fallback(self):
        html = '<p>text<img src="../image.png">'
        with patch.object(images._ArticleImages, 'feed', side_effect=ValueError('unsupported')):
            actual = images.on_page_content(html, page=self.page(), config=self.config, files=None)
        expected = images._soup_page_content(html, page=self.page(), config=self.config, files=None)
        self.assertEqual(actual, expected)

    def test_unclosed_or_mismatched_raw_html_retains_tree_repairs_for_search(self):
        for html in ('<p>A) First choice.<p>B) Second choice.',
                     '<p>#include <stdio.h> int main()</p><p>explanation</p>',
                     '<div><span>text</div>', '<p>text</p></div>'):
            with self.subTest(html=html):
                actual = images.on_page_content(html, page=self.page(), config=self.config, files=None)
                expected = images._soup_page_content(html, page=self.page(), config=self.config, files=None)
                self.assertEqual(actual, expected)


class SearchCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()
        (self.root / 'mkdocs.yml').write_text('site_name: Test\n', encoding='utf8')
        self.config = load_config(str(self.root / 'mkdocs.yml'))
        self.files = get_files(self.config)
        self.page = SimpleNamespace(file=SimpleNamespace(src_uri='a.md'), url='a/', title='Title', meta={},
                                    content='<h1 id="title">Title</h1><p data-search-exclude>hidden</p><h2 id="part">Part</h2><p>body</p>',
                                    toc=get_toc([{'name': 'Title', 'id': 'title', 'level': 1, 'children': [
                                        {'name': 'Part', 'id': 'part', 'level': 2, 'children': []}]}]))
        self.index_config = {'lang': ['en'], 'separator': r'\s+', 'pipeline': [],
                             'fields': {'title': {'boost': 1}}, 'jieba_dict': None, 'jieba_dict_user': None}

    def tearDown(self):
        self.temp.cleanup()

    def cache(self, enabled=True):
        render = RenderCache(enabled)
        render._prepare(self.config, self.files)
        return SearchCache(render, SearchIndex)

    def add(self, cache=None, original=None):
        cache = cache or self.cache()
        index = SearchIndex(**self.index_config)
        cache.add(original or SearchIndex.add_entry_from_context, index, self.page)
        return cache, index

    def test_new_index_reuses_identical_entries_without_segmenting(self):
        first, expected = self.add()
        second, actual = self.add(original=lambda *a: self.fail('must replay entries'))
        self.assertEqual((first.misses, second.hits), (1, 1))
        self.assertEqual(actual.entries, expected.entries)
        self.assertIsNot(actual.entries[0], expected.entries[0])
        self.assertEqual(self.page.content.count('data-search-exclude'), 1)
        actual.entries[0]['title'] = 'mutation'
        self.assertEqual(self.add()[1].entries, expected.entries)

    def test_content_metadata_title_toc_url_and_config_invalidate(self):
        changes = [lambda: setattr(self.page, 'content', self.page.content.replace('body', 'edit')),
                   lambda: self.page.meta.update(tags=['tag'], search={'boost': 2}),
                   lambda: self.page.meta.update(search={'exclude': True}),
                   lambda: self.page.meta.clear(),
                   lambda: setattr(self.page, 'title', 'New'),
                   lambda: setattr(self.page.toc.items[0], 'id', 'new-id'),
                   lambda: setattr(self.page, 'url', 'new/'),
                   lambda: self.index_config.update(separator='-')]
        for change in changes:
            self.add()
            change()
            cache, index = self.add()
            expected = SearchIndex(**self.index_config)
            SearchIndex.add_entry_from_context(expected, self.page)
            self.assertEqual(cache.misses, 1)
            self.assertEqual(index.entries, expected.entries)

    def test_corruption_and_partial_writes_rebuild(self):
        for corruption in ('{', '{}', 'sha'):
            self.add()
            slot = next((self.root / '.cache/preview-search').glob('*.json'))
            if corruption == 'sha':
                value = json.loads(slot.read_text(encoding='utf8'))
                value['payload'][0]['text'] = 'stale'
                slot.write_text(json.dumps(value), encoding='utf8')
            else:
                slot.write_text(corruption, encoding='utf8')
            cache, _ = self.add()
            self.assertEqual(cache.misses, 1)

    def test_fresh_unsupported_version_metadata_and_custom_dictionary_bypass(self):
        self.assertEqual(self.add(self.cache(False))[0].skipped, 1)
        with patch('tools.serve_site.importlib.metadata.version', return_value='future'):
            self.assertEqual(self.add(self.cache())[0].skipped, 1)
        self.page.meta['custom'] = object()
        self.assertEqual(self.add()[0].skipped, 1)
        self.page.meta.clear()
        self.index_config['jieba_dict'] = 'custom.txt'
        # The original would require an actual dictionary; isolate bypass here.
        self.assertEqual(self.add(original=lambda *a: None)[0].skipped, 1)

    def test_global_scope_change_invalidates_and_current_pages_only_are_added(self):
        _, first = self.add()
        (self.root / 'mkdocs.yml').write_text('site_name: Changed\n', encoding='utf8')
        self.assertEqual(self.add()[0].misses, 1)
        self.page.file.src_uri, self.page.url = 'b.md', 'b/'
        _, second = self.add()
        self.assertTrue(all(entry['location'].startswith('b/') for entry in second.entries))
        self.assertNotEqual(second.entries, first.entries)

    def test_installed_material_field_config_has_a_stable_signature(self):
        from material.plugins.search.config import SearchFieldConfig
        self.assertEqual(_stable({'title': SearchFieldConfig()}), {'title': {'boost': 1.0}})

    def test_custom_boost_that_material_stringifies_does_not_break_preview(self):
        self.page.meta['search'] = {'boost': str}
        cache, index = self.add()
        self.assertEqual(cache.misses, 1)
        self.assertIs(index.entries[0]['boost'], str)

    def test_duplicate_distribution_discovery_does_not_invalidate_environment(self):
        first = SimpleNamespace(metadata={'Name': 'local-tools'}, version='1')
        second = SimpleNamespace(metadata={'Name': 'local-tools'}, version='2')
        with patch('tools.serve_site.importlib.metadata.distributions', return_value=[first, second]):
            expected = RenderCache().versions
        with patch('tools.serve_site.importlib.metadata.distributions', return_value=[first, first, second]):
            self.assertEqual(RenderCache().versions, expected)
        self.assertEqual(len(expected), 2)


if __name__ == '__main__':
    unittest.main()
