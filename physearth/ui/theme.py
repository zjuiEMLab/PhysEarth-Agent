"""Stylesheet assembly.

The interface does not use Gradio's theming at all. Gradio's own boxes are switched to
`display: contents` in the stylesheet, so what remains on screen is our markup plus two
native elements, a textarea and a button. Nothing here calls `gr.themes.Base().set()`:
mixing the two systems is what broke the previous attempt.
"""

import base64
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"
FONT_DIR = ASSETS / "fonts"

FONTS = (
    ("Anthropic Serif", "anthropic-serif.ttf", "400"),
    ("Anthropic Mono", "anthropic-mono.ttf", "100 900"),
)


def font_faces():
    """Inline the two bundled faces so the page needs no second request."""
    rules = []
    for family, filename, weight in FONTS:
        path = FONT_DIR / filename
        if not path.is_file():
            continue
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
            "font-display:swap;src:url(data:font/ttf;base64,%s) format('truetype');}"
            % (family, weight, payload)
        )
    return "\n".join(rules)


def css():
    sheet = ASSETS / "ui.css"
    return "%s\n%s" % (font_faces(), sheet.read_text(encoding="utf-8") if sheet.is_file() else "")


def js():
    script = ASSETS / "ui.js"
    return script.read_text(encoding="utf-8") if script.is_file() else ""


def head():
    """Force the light palette; Gradio otherwise follows the system dark preference."""
    return (
        "<script>try{var u=new URL(window.location.href);"
        "if(u.searchParams.get('__theme')!=='light'){u.searchParams.set('__theme','light');"
        "window.location.replace(u.toString());}}catch(e){}</script>"
    )


def fonts_present():
    return [name for _, name, _ in FONTS if (FONT_DIR / name).is_file()]
