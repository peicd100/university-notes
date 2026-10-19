"""Content-cache and lazy-source regressions; only temporary fixtures are changed."""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from mkdocs.config import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.pages import Page
from tools.serve_site import RenderCache, _stable
from tools import source_jump_hook as jump


class RenderCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'docs').mkdir()
        (self.root/'theme').mkdir()
        (self.root/'tools').mkdir()
        self.config_path = self.root/'mkdocs.yml'
        self.config_path.write_text('site_name: Test\nuse_directory_urls: false\ntheme:\n  name: mkdocs\n  custom_dir: theme\nmarkdown_extensions: [toc]\n',encoding='utf8')
        (self.root/'docs/a.md').write_text('# Title\n\n## Section\n\n[link](b.md#target)\n',encoding='utf8')
        (self.root/'docs/b.md').write_text('# Target\n',encoding='utf8')
        (self.root/'tools/extension.py').write_text('# v1\n',encoding='utf8')
        (self.root/'theme/main.html').write_text('version 1',encoding='utf8')

    def tearDown(self):
        self.temp.cleanup()

    def render(self, cache=None, original=None):
        cache = cache or RenderCache()
        config = load_config(str(self.config_path))
        files = get_files(config)
        page = Page(None,files.get_file_from_path('a.md'),config)
        page.read_source(config)
        cache.begin_build()
        cache.render(original or Page.render,page,config,files)
        return cache,page

    def test_new_process_cache_restores_content_toc_and_current_link_objects(self):
        first,page = self.render()
        with patch.object(Page,'render',side_effect=AssertionError('must restore')):
            second,restored = self.render()
        self.assertEqual((first.misses,second.hits),(1,1))
        self.assertEqual(restored.content,page.content)
        self.assertEqual(restored.title,page.title)
        self.assertEqual(restored.present_anchor_ids,page.present_anchor_ids)
        self.assertEqual(restored.toc.items[0].id,page.toc.items[0].id)
        self.assertEqual([f.src_uri for f in restored.links_to_anchors],['b.md'])
        self.assertIsNot(next(iter(restored.links_to_anchors)),next(iter(page.links_to_anchors)))

    def test_same_size_same_mtime_edit_invalidates(self):
        self.render()
        source = self.root/'docs/a.md'; old = source.stat()
        source.write_text(source.read_text().replace('Title','Other'),encoding='utf8')
        os.utime(source,ns=(old.st_atime_ns,old.st_mtime_ns))
        cache,page = self.render()
        self.assertEqual(cache.misses,1)
        self.assertIn('Other',page.content)

    def test_config_hook_theme_version_and_catalog_invalidate(self):
        for relative in ['mkdocs.yml','tools/extension.py','theme/main.html','docs/new.md']:
            with self.subTest(relative=relative):
                self.render()
                path = self.root/relative
                path.write_text((path.read_text(encoding='utf8') if path.exists() else '')+'\n# changed\n',encoding='utf8')
                cache,_ = self.render()
                self.assertEqual(cache.misses,1)
        self.render()
        cache = RenderCache(); cache.versions.append(('fake-package','2'))
        self.assertEqual(self.render(cache)[0].misses,1)

    def test_other_page_edit_reuses_parent_but_includes_bypass(self):
        self.render()
        (self.root/'docs/b.md').write_text('# Changed\n',encoding='utf8')
        self.assertEqual(self.render()[0].hits,1)
        source = self.root/'docs/a.md'
        for marker in ['--8<-- "b.md"','{!b.md!}']:
            source.write_text(marker,encoding='utf8')
            self.assertEqual(self.render()[0].skipped,1)

    def test_corrupt_or_partial_cache_rebuilds(self):
        for corruption in ['{','{}','sha']:
            self.render()
            slot = next((self.root/'.cache/preview-render').glob('*.json'))
            if corruption == 'sha':
                data=json.loads(slot.read_text(encoding='utf8')); data['payload']['content']='WRONG'
                slot.write_text(json.dumps(data),encoding='utf8')
            else:
                slot.write_text(corruption,encoding='utf8')
            cache,page=self.render()
            self.assertEqual(cache.misses,1)
            self.assertNotIn('WRONG',page.content)

    def test_fresh_strict_and_debug_bypass(self):
        self.assertEqual(self.render(RenderCache(enabled=False))[0].skipped,1)
        self.config_path.write_text(self.config_path.read_text(encoding='utf8')+'strict: true\n',encoding='utf8')
        self.assertEqual(self.render()[0].skipped,1)

    def test_inherited_config_content_invalidates(self):
        base=self.root/'base.yml'; base.write_text('site_name: Parent\n',encoding='utf8')
        self.config_path.write_text('INHERIT: base.yml\n'+self.config_path.read_text(encoding='utf8'),encoding='utf8')
        self.render()
        base.write_text('site_name: Changed\n',encoding='utf8')
        self.assertEqual(self.render()[0].misses,1)

    def test_partial_options_and_real_project_scope_are_stable(self):
        self.assertEqual(_stable(partial(str.replace,'a','b')),
                         _stable(partial(str.replace,'a','b')))
        root=Path(__file__).resolve().parents[1]
        config=load_config(str(root/'mkdocs.yml')); files=get_files(config)
        self.assertEqual(RenderCache()._prepare(config,files),RenderCache()._prepare(config,files))

    def test_raw_html_anchor_without_id_is_preserved(self):
        def render_with_empty_anchor(page,config,files):
            Page.render(page,config,files)
            page.present_anchor_ids.add(None)
        self.render(original=render_with_empty_anchor)
        cache,page=self.render()
        self.assertEqual(cache.hits,1)
        self.assertIn(None,page.present_anchor_ids)


class LazySourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'docs').mkdir()
        (self.root/'mkdocs.yml').write_text('site_name: Test\nuse_directory_urls: false\n',encoding='utf8')
        self.source=self.root/'docs/a.md'; self.source.write_text('# Title\n\noriginal\n',encoding='utf8')
        self.config=load_config(str(self.root/'mkdocs.yml'))
        self.files=get_files(self.config)
        jump.on_startup(command='serve',dirty=True)

    def tearDown(self):
        jump.on_startup(command='serve',dirty=False)
        self.temp.cleanup()

    def test_startup_does_not_read_or_parse_all_sources(self):
        with patch.object(jump,'_build_page_record',side_effect=AssertionError('no eager parse')),patch.object(jump,'_read_markdown_content',side_effect=AssertionError('no eager read')):
            jump.on_files(self.files,config=self.config)
            file=self.files.get_file_from_path('a.md')
            jump.on_page_markdown('transformed',page=type('P',(),{'file':file})(),config=self.config,files=self.files)
        self.assertFalse(jump._PAGE_INDEX)
        self.assertIn('a.html',jump._PAGE_SOURCES)

    def test_lookup_reuses_then_reloads_original_source_after_edit_and_removal(self):
        jump.on_files(self.files,config=self.config)
        first=jump._lookup_page_record('a.html')
        self.assertIs(jump._lookup_page_record('a.html'),first)
        self.source.write_text('\n# Title\n\nchanged\n',encoding='utf8')
        changed=jump._lookup_page_record('a.html')
        self.assertEqual(changed.blocks[0].start_line,2)
        self.assertIn('changed',changed.markdown)
        self.source.unlink()
        jump.on_files(get_files(self.config),config=self.config)
        self.assertIsNone(jump._lookup_page_record('a.html'))
        self.assertFalse(jump._SOURCE_INDEX_CACHE)

    def test_concurrent_first_lookup_parses_once(self):
        jump.on_files(self.files,config=self.config)
        with patch.object(jump,'_build_page_record',wraps=jump._build_page_record) as parser:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results=list(pool.map(lambda _:jump._lookup_page_record('a.html'),range(4)))
            self.assertEqual(parser.call_count,1)
            self.assertTrue(all(record is results[0] for record in results))


if __name__=='__main__':
    unittest.main()
