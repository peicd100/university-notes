"""Collapsible code."""
import xml.etree.ElementTree as etree
from markdown import util as mutil
import re
from pymdownx.blocks.block import Block
from pymdownx.blocks import BlocksExtension

# Fenced block placeholder for SuperFences
FENCED_BLOCK_RE = re.compile(
    r'^([\> ]*){}({}){}$'.format(
        mutil.HTML_PLACEHOLDER[0],
        mutil.HTML_PLACEHOLDER[1:-1] % r'([0-9]+)',
        mutil.HTML_PLACEHOLDER[-1]
    )
)


class CollapseCode(Block):
    """Collapse code."""

    NAME = 'collapse-code'

    def on_init(self):
        """Handle initialization."""

        # Track tab group count across the entire page.
        if 'collapse_code_count' not in self.tracker:
            self.tracker['collapse_code_count'] = 0

        self.expand = self.config['expand_text']
        if not isinstance(self.expand, str):
            raise ValueError("'expand_text' must be a string")

        self.collapse = self.config['collapse_text']
        if not isinstance(self.collapse, str):
            raise ValueError("'collapse_text' must be a string")

        self.expand_title = self.config['expand_title']
        if not isinstance(self.expand_title, str):
            raise ValueError("'expand_title' must be a string")

        self.collapse_title = self.config['collapse_title']
        if not isinstance(self.collapse_title, str):
            raise ValueError("'collapse_title' must be a string")

    def on_create(self, parent):
        """Create the element."""

        self.count = self.tracker['collapse_code_count']
        self.tracker['collapse_code_count'] += 1
        el = etree.SubElement(parent, 'div', {'class': 'collapse-code'})
        etree.SubElement(
            el,
            'input',
            {
                "type": "checkbox",
                "id": f"__collapse{self.count}",
                "name": f"__collapse{self.count}",
                'checked': 'checked'
            }
        )
        return el

    def _append_label(self, parent, kind, visible_text, fallback_text):
        """Create expand/collapse label."""

        label_class = kind if visible_text else f"{kind} icon-only"
        label = etree.SubElement(
            parent,
            'label',
            {
                'for': f'__collapse{self.count}',
                'class': label_class,
                'tabindex': '0'
            }
        )

        if visible_text:
            label.text = visible_text
        else:
            sr = etree.SubElement(label, 'span', {'class': 'collapse-code__sr-only'})
            sr.text = fallback_text

        return label

    def on_end(self, block):
        """Convert non list items to details."""

        el = etree.SubElement(block, 'div', {'class': 'code-footer'})
        self._append_label(el, 'expand', self.expand, self.expand_title or 'Expand')
        self._append_label(el, 'collapse', self.collapse, self.collapse_title or 'Collapse')


class CollapseCodeExtension(BlocksExtension):
    """Admonition Blocks Extension."""

    def __init__(self, *args, **kwargs):
        """Initialize."""

        self.config = {
            'expand_text': ['Expand', "Set the text for the expand button."],
            'collapse_text': ['Collapse', "Set the text for the collapse button."],
            'expand_title': ['expand', "Set the text for the expand title."],
            'collapse_title': ['collapse', "Set the text for the collapse title."]
        }

        super().__init__(*args, **kwargs)

    def extendMarkdownBlocks(self, md, blocks):
        """Extend Markdown blocks."""

        blocks.register(CollapseCode, self.getConfigs())


def makeExtension(*args, **kwargs):
    """Return extension."""

    return CollapseCodeExtension(*args, **kwargs)
