"""Focused performance regression tests (mkdocs Conda environment)."""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image
from bs4 import BeautifulSoup
from tools import asset_bundle_hook, image_lazy_loading_hook, optimized_images, source_jump_hook


class ImageDerivativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        self.source = self.docs / "image.png"
        image = Image.new("RGBA", (256, 256), (10, 20, 30, 0))
        for x in range(256):
            for y in range(64, 192):
                image.putpixel((x, y), (x, 60, 100, 255))
        image.save(self.source)
        self.config = {"config_file_path":str(self.root / "mkdocs.yml"),
                       "docs_dir":str(self.docs),"site_dir":str(self.root / "site"),
                       "theme":{"logo":"image.png","favicon":"image.png"}}
        self.page = SimpleNamespace(url="folder/test.html", file=SimpleNamespace(src_uri="folder/test.md"), meta={})
        image_lazy_loading_hook.on_config(self.config)

    def tearDown(self):
        self.temp.cleanup()

    def test_lossless_alpha_and_sources_unchanged(self):
        before = self.source.read_bytes()
        derived = optimized_images.derive_image(self.source, self.config)
        self.assertIsNotNone(derived)
        output = Path(self.config["site_dir"]) / derived["url"]
        with Image.open(self.source) as original, Image.open(output) as image:
            self.assertEqual(image.convert("RGBA").tobytes(), original.convert("RGBA").tobytes())
        self.assertLess(output.stat().st_size, self.source.stat().st_size)
        self.assertEqual(self.source.read_bytes(), before)

    def test_hash_cache_reuse_and_corruption_repair(self):
        derived = optimized_images.derive_image(self.source, self.config)
        with patch.object(Image.Image, "save", side_effect=AssertionError("cache should avoid encoding")):
            self.assertEqual(optimized_images.derive_image(self.source, self.config), derived)
        cache = next((self.root / ".cache/site-images").rglob("*.webp"))
        cache.write_bytes(b"corrupt")
        repaired = optimized_images.derive_image(self.source, self.config)
        self.assertEqual(repaired, derived)
        self.assertEqual(hashlib.sha256(cache.read_bytes()).hexdigest(), derived["sha256"])
        Image.new("RGBA",(256,256),(30,40,50,255)).save(self.source)
        self.assertNotEqual(optimized_images.derive_image(self.source,self.config)["url"], derived["url"])

    def test_malformed_cache_metadata_is_recomputed(self):
        derived = optimized_images.derive_image(self.source,self.config)
        meta = next((self.root/".cache/site-images").rglob("*.json"))
        meta.write_text("[]",encoding="utf8")
        self.assertEqual(optimized_images.derive_image(self.source,self.config),derived)
        meta.write_text('{"identity":"'+derived["identity"]+'","sha256":"'+derived["sha256"]+'"}',encoding="utf8")
        self.assertEqual(optimized_images.derive_image(self.source,self.config),derived)

    def test_logo_and_favicon_dimensions(self):
        logo = optimized_images.derive_image(self.source,self.config,logo=True)
        icon = optimized_images.derive_image(self.source,self.config,favicon=True)
        self.assertEqual((logo["width"],logo["height"]),(96,96))
        self.assertEqual((icon["width"],icon["height"]),(32,32))
        self.assertTrue(icon["url"].endswith(".png"))
        ctx = image_lazy_loading_hook.on_page_context({},page=self.page,config=self.config,nav=None)
        self.assertEqual(ctx["peicd_optimized_logo"],logo["url"])
        output = image_lazy_loading_hook.on_post_page('<link rel="icon" href="../image.png">',page=self.page,config=self.config)
        self.assertIn("optimized-images", output)

    def test_html_images_lazy_width_and_remote_handling(self):
        html='<img src="../image.png=50%x"><img src="../image.png"><img src="https://example.com/remote.png">'
        result = image_lazy_loading_hook.on_page_content(html,page=self.page,config=self.config,files=None)
        images = BeautifulSoup(result,"html.parser").select("img")
        self.assertIn("optimized-images",images[0]["src"])
        self.assertNotIn("=50%x",images[0]["src"])
        self.assertIn("width:50%",images[0]["style"])
        self.assertNotIn("loading",images[0].attrs)
        self.assertEqual(images[1]["loading"],"lazy")
        self.assertEqual(images[2]["src"],"https://example.com/remote.png")
        self.assertIsNone(image_lazy_loading_hook._local_image("../../private.png",self.page,self.config))

    def test_animated_png_is_not_converted(self):
        frames = [Image.new("RGBA",(64,64),color) for color in ("red","blue")]
        frames[0].save(self.source,save_all=True,append_images=frames[1:],duration=100,loop=0)
        self.assertIsNone(optimized_images.derive_image(self.source,self.config))


class CSSBundleTests(unittest.TestCase):
    def test_safe_compaction_preserves_calc_strings_and_scopes(self):
        css='/*comment*/ .x { width: calc(100% - 2px); content:"a  b"; }\n.x { width: calc(100% - 2px); content:"a  b"; }\n@media (max-width: 400px) { .x { color:red; } } .x { color:blue; }'
        result=asset_bundle_hook.compact_css(css)
        self.assertNotIn("comment",result)
        self.assertEqual(result.count('content:"a  b"'),1)
        self.assertIn("calc(100% - 2px)",result)
        self.assertIn("color:red",result)
        self.assertIn("color:blue",result)
        self.assertIn("@media",result)

    def test_reused_dirty_config_keeps_generated_bundle(self):
        root=Path(__file__).resolve().parents[1]
        config={"config_file_path":str(root/"mkdocs.yml"),"theme":{"custom_dir":str(root/"theme")},
                "extra_css":["assets/pymdownx-extras/extra-8611f6c398.css","assets/pymdownx-extras/自定義.css?v=old"]}
        asset_bundle_hook.on_config(config)
        first=list(config["extra_css"])
        asset_bundle_hook.on_config(config)
        self.assertEqual(config["extra_css"],first)
        self.assertIsNotNone(asset_bundle_hook._BUNDLE)

    def test_actual_stylesheets_parse_and_shrink(self):
        root=Path(__file__).resolve().parents[1] / "theme/assets/pymdownx-extras"
        css=(root/"extra-8611f6c398.css").read_text(encoding="utf8")+'\n'+(root/"自定義.css").read_text(encoding="utf8")
        result=asset_bundle_hook.compact_css(css)
        self.assertLess(len(result.encode()),len(css.encode()))
        self.assertNotIn("fonts.googleapis.com",result)
        self.assertIn("Cascadia Mono",result)


class SourceIndexCacheTests(unittest.TestCase):
    def setUp(self):
        source_jump_hook.on_startup(command="serve",dirty=True)
        source_jump_hook._PAGE_INDEX.clear()
        self.file=SimpleNamespace(src_uri="a.md",dest_uri="a.html",abs_src_path="",content_string="# Title\n\ntext\n")

    def tearDown(self):
        source_jump_hook.on_startup(command="serve",dirty=False)

    def test_hash_reuse_and_line_invalidation(self):
        source=self.file.content_string
        source_jump_hook._index_page_markdown(source,self.file)
        original=source_jump_hook._PAGE_INDEX["a.html"]
        with patch.object(source_jump_hook,"_build_page_record",side_effect=AssertionError("must reuse")):
            source_jump_hook.on_config({})
            source_jump_hook._index_page_markdown(source,self.file)
        self.assertIs(source_jump_hook._PAGE_INDEX["a.html"],original)
        source_jump_hook._index_page_markdown("\n"+source,self.file)
        changed=source_jump_hook._PAGE_INDEX["a.html"]
        self.assertIsNot(changed,original)
        self.assertEqual(changed.blocks[0].start_line,original.blocks[0].start_line+1)

    def test_production_does_not_index_and_removed_files_are_pruned(self):
        source_jump_hook.on_files([self.file],config={})
        self.assertTrue(source_jump_hook._SOURCE_INDEX_CACHE)
        source_jump_hook.on_files([],config={})
        self.assertFalse(source_jump_hook._SOURCE_INDEX_CACHE)
        source_jump_hook.on_startup(command="build",dirty=False)
        with patch.object(source_jump_hook,"_build_page_record",side_effect=AssertionError("build must not index")):
            source_jump_hook.on_files([self.file],config={})
            self.assertEqual(source_jump_hook.on_page_markdown("rendered",page=SimpleNamespace(file=self.file),config={},files=None),"rendered")
        self.assertFalse(source_jump_hook._PAGE_INDEX)


if __name__ == "__main__":
    unittest.main()
