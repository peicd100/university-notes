"""Build-time UX regressions; fixtures only, no original note mutations."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as Obj
import json
import unittest
from bs4 import BeautifulSoup
from PIL import Image
from tools import site_ux_hook, image_lazy_loading_hook, optimized_images


class SiteUXTests(unittest.TestCase):
    def setUp(self):
        site_ux_hook._PAGES = []
        site_ux_hook._EAGER_PAGES = None
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.docs = self.root / 'docs'
        self.docs.mkdir()
        self.config = {'config_file_path': str(self.root / 'mkdocs.yml'), 'docs_dir': str(self.docs),
                       'site_dir': str(self.root / 'site'), 'theme': {'logo': 'logo.png'}}
        self.page = Obj(url='md/115-1/course/a.html', file=Obj(src_uri='md/115-1/course/a.md'), meta={})

    def tearDown(self):
        self.temp.cleanup()

    def test_server_pathbar_reserves_geometry_and_escapes_untrusted_labels(self):
        page = Obj(title='A <script>bad</script>', url=self.page.url, is_page=True, active=True)
        other = Obj(title='B', url='md/115-1/course/b.html', is_page=True, active=False)
        top = Obj(title='Course', active=True, children=[page, other])
        context = site_ux_hook.on_page_context({}, page=self.page, config=self.config, nav=Obj(items=[top]))
        soup = BeautifulSoup(context['peicd_pathbar'], 'html.parser')
        self.assertEqual(len(soup.select('nav button')), 2)
        self.assertFalse(soup.select('script'))
        self.assertFalse(soup.select('a'))  # Lists are populated only on demand.
        self.assertEqual(soup.select_one('button')['aria-expanded'], 'false')
        options = json.loads(soup.select('.peicd-folder-pathbar__item')[1]['data-peicd-options'])
        self.assertEqual(options[1]['href'], 'b.html')
        self.assertIn('115-1', soup.get_text())
        self.assertTrue(soup.select_one('.peicd-folder-pathbar__menu').has_attr('hidden'))

    def test_toc_shell_reserves_real_toolbar_geometry_without_parsing_article(self):
        toc = '<div class="md-sidebar md-sidebar--secondary"><div><nav class="md-nav md-nav--secondary"><label class="md-nav__title">目錄</label><ul data-md-component="toc"><li class="md-nav__item"><a class="md-nav__link" href="#a">A</a><nav class="md-nav"><ul><li class="md-nav__item">B</li></ul></nav></li></ul></nav></div></div>'
        article = '<div class="md-content"><pre>&lt;script&gt; untouched code\n</pre></div>'
        output = site_ux_hook._stable_toc(toc + article)
        self.assertTrue(output.endswith(article))
        soup = BeautifulSoup(output, 'html.parser')
        self.assertEqual(len(soup.select('[data-peicd-toc-shell="server"] button[disabled]')), 6)
        self.assertEqual(len(soup.select('.peicd-toc-item--nested.peicd-toc-item--collapsed')), 1)
        self.assertEqual(len(soup.select('.md-nav__title')), 1)
        self.assertTrue(soup.select_one('.md-sidebar--secondary').has_attr('data-peicd-toc-mode'))

    def test_top_level_page_with_none_children_builds_without_error(self):
        top = Obj(title='Standalone', url=self.page.url, is_page=True, active=True, children=None)
        context = site_ux_hook.on_page_context({}, page=self.page, config=self.config, nav=Obj(items=[top]))
        self.assertIn('Standalone', context['peicd_pathbar'])

    def test_annotation_routes_are_known_before_rendering_navigation(self):
        annotated = Obj(url='annotated.html', content='<div class="highlight annotate">code</div>')
        plain = Obj(url='plain.html', content='<div class="highlight">code</div>')
        files = Obj(documentation_pages=lambda: [Obj(page=annotated), Obj(page=plain)])
        nav = Obj(items=[])
        self.assertIs(site_ux_hook.on_nav(nav, config=self.config, files=files), nav)
        context = site_ux_hook.on_page_context({}, page=self.page, config=self.config, nav=nav)
        links = json.loads(context['peicd_eager_links'])
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].endswith('annotated.html'))

    def test_avatar_uses_small_derivative_without_changing_original(self):
        src = self.docs / 'logo.png'
        Image.new('RGB', (720, 720), 'cyan').save(src)
        before = src.read_bytes()
        self.page.url = 'blog/index.html'
        output = site_ux_hook.on_post_page('<a class="md-author"><img src="../logo.png" alt="Author"></a>', page=self.page, config=self.config)
        img = BeautifulSoup(output, 'html.parser').img
        self.assertIn('optimized-images', img['src'])
        self.assertEqual((img['width'], img['height']), ('32', '32'))
        self.assertEqual(src.read_bytes(), before)

    def test_remote_avatar_is_not_fetched(self):
        html = '<span class="md-author"><img src="https://example.test/avatar.png"></span>'
        self.assertEqual(site_ux_hook.on_post_page(html, page=self.page, config=self.config), html)

    def test_root_redirect_preserves_shared_query_and_hash_without_source_edit(self):
        self.page.file.src_uri = 'index.md'
        html = 'window.location.replace(new URL("blog/index.html", window.location.href).toString());'
        output = site_ux_hook.on_post_page(html, page=self.page, config=self.config)
        self.assertIn('next.search = window.location.search', output)
        self.assertIn('next.hash = window.location.hash', output)

    def test_responsive_derivatives_preserve_full_size_target_and_alpha(self):
        src = self.docs / 'large.png'
        Image.new('RGBA', (1200, 800), (20, 40, 60, 140)).save(src)
        before = src.read_bytes()
        self.page.url = 'a.html'; self.page.file.src_uri = 'a.md'
        output = image_lazy_loading_hook.on_page_content('<img src="large.png">', page=self.page, config=self.config, files=None)
        img = BeautifulSoup(output, 'html.parser').img
        self.assertIn('480w', img['srcset']); self.assertIn('960w', img['srcset']); self.assertIn('1200w', img['srcset'])
        self.assertEqual(img['data-peicd-full-src'], img['src'])
        self.assertEqual(img['data-peicd-original-src'], 'large.png')
        small = optimized_images.derive_image(src, self.config, max_width=480)
        with Image.open(Path(self.config['site_dir']) / small['url']) as image:
            self.assertEqual(image.size, (480, 320))
            self.assertEqual(image.convert('RGBA').getpixel((0, 0))[3], 140)
        self.assertEqual(src.read_bytes(), before)

    def test_author_srcset_and_dimensions_are_preserved(self):
        Image.new('RGB', (1200, 800), 'green').save(self.docs / 'large.png')
        self.page.url = 'a.html'; self.page.file.src_uri = 'a.md'
        output = image_lazy_loading_hook.on_page_content('<img src="large.png" width="60" srcset="custom.png 60w">', page=self.page, config=self.config, files=None)
        img = BeautifulSoup(output, 'html.parser').img
        self.assertEqual(img['width'], '60'); self.assertEqual(img['srcset'], 'custom.png 60w')


if __name__ == '__main__':
    unittest.main()
