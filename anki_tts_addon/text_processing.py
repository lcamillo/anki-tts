"""
Text processing utilities for Anki TTS.
Extracts speakable text from Anki card HTML.
"""

import re
import html as html_module


# Greek letters and math symbols -> spoken forms
SYMBOL_REPLACEMENTS = {
    "\u03c0": "pi",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u03b3": "gamma",
    "\u03b4": "delta",
    "\u03b5": "epsilon",
    "\u03b8": "theta",
    "\u03bb": "lambda",
    "\u03bc": "mu",
    "\u03c3": "sigma",
    "\u03c4": "tau",
    "\u03c6": "phi",
    "\u03c9": "omega",
    "\u00b1": "plus or minus",
    "\u2192": "arrow",
    "\u221e": "infinity",
    "\u2248": "approximately",
    "\u2260": "not equal",
    "\u2264": "less than or equal to",
    "\u2265": "greater than or equal to",
    "\u2211": "sum",
    "\u220f": "product",
    "\u222b": "integral",
    "\u0394": "delta",
    "\u2207": "nabla",
}

_SYMBOL_PATTERN = re.compile(
    "|".join(map(re.escape, SYMBOL_REPLACEMENTS.keys()))
)


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = html_module.unescape(text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _replace_symbols(text: str) -> str:
    """Replace Greek letters and math symbols with spoken forms."""
    return _SYMBOL_PATTERN.sub(
        lambda m: SYMBOL_REPLACEMENTS[m.group()], text
    )


def extract_speakable_text(
    html_str: str, strip_question: bool = False
) -> str:
    """
    Extract speakable text from Anki card HTML.

    Args:
        html_str: Raw HTML from card.question() or card.answer()
        strip_question: If True, strip the question portion from an answer.
            Answer HTML includes question + <hr id=answer> + answer content.
    """
    if not html_str:
        return ""

    content = html_str

    # If processing answer, strip everything before the answer separator
    if strip_question:
        match = re.search(
            r'<hr\s+id\s*=\s*["\']?answer["\']?\s*/?\s*>',
            content,
            re.IGNORECASE,
        )
        if match:
            content = content[match.end():]

    # Try to extract from a #text div (common card template pattern)
    text_match = re.search(
        r'<div[^>]*id="text"[^>]*>(.*?)</div>', content, re.DOTALL
    )
    if text_match:
        content = text_match.group(1)

    # Replace [...] cloze placeholders with spoken form
    content = re.sub(r"\[\s*\.\.\.\s*\]", "blank", content)

    # Strip non-content elements
    content = re.sub(r"<script.*?</script>", "", content, flags=re.DOTALL)
    content = re.sub(r"<style.*?</style>", "", content, flags=re.DOTALL)
    content = re.sub(
        r'<div class="timer".*?</div>', "", content, flags=re.DOTALL
    )
    content = re.sub(
        r'<div id="tags-container".*?</div>', "", content, flags=re.DOTALL
    )

    # Clean to plain text
    clean = _strip_html(content)
    clean = _replace_symbols(clean)
    clean = re.sub(r"\s+", " ", clean)

    return clean.strip()
