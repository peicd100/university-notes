"""Nest Markdown block headings beneath their surrounding document section."""
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


def is_heading(node):
    return node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}


def is_section_block(node):
    classes = node.get("class", "").split()
    return node.tag in {"details", "blockquote"} or "admonition" in classes or "tabbed-block" in classes


def block_heading_levels(node):
    """Read this scope's headings while leaving nested blocks independent."""
    for child in node:
        if is_section_block(child) or child.tag in {"pre", "code"}:
            continue
        if is_heading(child):
            yield int(child.tag[1])
        else:
            yield from block_heading_levels(child)


class BlockHeadingTreeprocessor(Treeprocessor):
    def run(self, root):
        self.walk(root, 0)

    def walk(self, node, current_level, shift=0):
        for child in node:
            if is_heading(child):
                current_level = min(6, int(child.tag[1]) + shift)
                child.tag = f"h{current_level}"
            elif is_section_block(child):
                first_level = min(block_heading_levels(child), default=6)
                block_shift = max(0, current_level + 1 - first_level)
                self.walk(child, current_level, block_shift)
            elif child.tag not in {"pre", "code"}:
                current_level = self.walk(child, current_level, shift)
        return current_level


class BlockHeadingExtension(Extension):
    def extendMarkdown(self, md):
        # TOC runs at priority 5 and must see the adjusted hierarchy.
        md.treeprocessors.register(BlockHeadingTreeprocessor(md), "block_headings", 6)


def makeExtension(**kwargs):
    return BlockHeadingExtension(**kwargs)
