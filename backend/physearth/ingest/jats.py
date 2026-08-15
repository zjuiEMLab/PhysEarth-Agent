"""JATS XML to titled sections.

Lifted unchanged out of `scripts/build_corpus.py`, which now imports it, so the bundled
corpus and anything ingested during a conversation go through exactly one parser. The
only behavioural difference is that the reference labels travel as an argument instead of
a module global: one process serves every visitor, so nothing here may keep state between
two calls.

The parser is generic JATS. The publisher-specific parts, which URL an article lives at
and what a journal is called, stay with the caller.
"""

import re
import xml.etree.ElementTree as ET

SECTION_SPLIT_CHARS = 12000
SKIP_TAGS = {"fig", "table-wrap", "graphic", "media", "supplementary-material", "label"}


def _local(tag):
    return str(tag or "").rsplit("}", 1)[-1]


def _href(node):
    for key, value in node.attrib.items():
        if key == "href" or key.endswith("}href") or key.endswith(":href"):
            return value
    return ""


def clean(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def reference_labels(root):
    """Map each reference id to the author-year label the body cites it by."""
    labels = {}
    for ref in root.findall(".//ref-list/ref"):
        label = ref.findtext("label") or ""
        label = re.sub(r"\s*\(\s*", ", ", label.strip()).rstrip(")")
        if ref.get("id") and label:
            labels[ref.get("id")] = label
    return labels


def render_xref(node, labels):
    rids = (node.get("rid") or "").split()
    if node.get("ref-type") == "bibr":
        found = [labels[r] for r in rids if r in labels]
        return "(%s)" % "; ".join(found) if found else ""
    numbers = [m.group(0) for m in (re.search(r"\d+$", r) for r in rids) if m]
    return ", ".join(numbers)


def inline(node, labels):
    parts = []
    if node.tag == "tex-math":
        return "$%s$" % (node.text or "").strip()
    if node.tag == "xref":
        return render_xref(node, labels)
    if node.tag in SKIP_TAGS:
        return ""
    if node.text:
        parts.append(node.text)
    for child in node:
        parts.append(inline(child, labels))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def text_of(node, labels):
    return clean(inline(node, labels)) if node is not None else ""


def render_block(node, depth, labels):
    out = []
    for child in node:
        tag = child.tag
        if tag in SKIP_TAGS or tag == "title":
            continue
        if tag == "sec":
            title = child.find("title")
            if title is not None:
                out.append("%s %s" % ("#" * min(depth + 1, 6), clean(inline(title, labels))))
            out.append(render_block(child, depth + 1, labels))
        elif tag == "p":
            out.append(clean(inline(child, labels)))
        elif tag == "disp-formula":
            math = child.find(".//tex-math")
            if math is not None and math.text:
                out.append("$$%s$$" % math.text.strip())
        elif tag == "list":
            for item in child.findall("list-item"):
                out.append("- %s" % clean(inline(item, labels)))
        else:
            text = clean(inline(child, labels))
            if text:
                out.append(text)
    return "\n\n".join(p for p in out if p)


def render_block_without_subs(sec, labels):
    out = []
    for child in sec:
        if child.tag in ("sec", "title") or child.tag in SKIP_TAGS:
            continue
        if child.tag == "p":
            out.append(clean(inline(child, labels)))
    return "\n\n".join(p for p in out if p)


def build_sections(root, labels):
    """Titled sections, splitting a long one at its subsections rather than mid-sentence."""
    sections = []
    for sec in root.findall("body/sec"):
        title = text_of(sec.find("title"), labels) or "Section"
        body = render_block(sec, 1, labels)
        subs = sec.findall("sec")
        if len(body) > SECTION_SPLIT_CHARS and subs:
            lead = render_block_without_subs(sec, labels)
            if lead:
                sections.append((title, lead))
            for sub in subs:
                sub_title = text_of(sub.find("title"), labels) or "Subsection"
                sections.append(("%s - %s" % (title, sub_title), render_block(sub, 1, labels)))
        else:
            sections.append((title, body))
    return sections


def front_matter(root, labels, journal=""):
    meta = root.find("front/article-meta")
    if meta is None:
        return {}
    authors = []
    for contrib in meta.findall("contrib-group/contrib"):
        given = text_of(contrib.find("name/given-names"), labels)
        surname = text_of(contrib.find("name/surname"), labels)
        name = " ".join(x for x in (given, surname) if x)
        if name:
            authors.append(name)
    permissions = text_of(meta.find("permissions"), labels)
    license_url = ""
    match = re.search(r"https://creativecommons\.org/licenses/by(?:-sa)?/[\d.]+/", permissions)
    if match:
        license_url = match.group(0)
    license_id = "CC-BY-4.0" if "/by/4.0" in license_url else "CC-BY-3.0"
    return {
        "title": text_of(meta.find("title-group/article-title"), labels),
        "authors": authors,
        "journal": journal,
        "volume": text_of(meta.find("volume"), labels),
        "pages": "%s-%s" % (text_of(meta.find("fpage"), labels), text_of(meta.find("lpage"), labels)),
        "doi": text_of(meta.find("article-id[@pub-id-type='doi']"), labels),
        "license": license_id,
        "license_url": license_url,
        "abstract": text_of(meta.find("abstract"), labels),
    }


def _caption(node, labels):
    caption = next((child for child in node if _local(child.tag) == "caption"), None)
    return text_of(caption, labels)


def _label_text(node):
    return clean("".join(node.itertext())) if node is not None else ""


def _table_rows(node, labels):
    rows = []
    for row in node.iter():
        if _local(row.tag) != "tr":
            continue
        cells = []
        for cell in row:
            if _local(cell.tag) in ("td", "th"):
                cells.append(text_of(cell, labels))
        if cells:
            rows.append(cells)
    return rows


def extract_assets(root, labels):
    """Extract figure/table metadata while keeping them out of section prose."""
    figures, tables = [], []

    def visit(node, section_id="", section_title=""):
        tag = _local(node.tag)
        if tag == "sec":
            section_id = node.get("id") or section_id
            title_node = next((child for child in node if _local(child.tag) == "title"), None)
            section_title = text_of(title_node, labels) or section_title
        if tag == "fig":
            label_node = next((child for child in node if _local(child.tag) == "label"), None)
            graphics = [child for child in node.iter() if _local(child.tag) in ("graphic", "media")]
            figures.append(
                {
                    "id": node.get("id") or "fig-%d" % (len(figures) + 1),
                    "label": _label_text(label_node) or "Figure %d" % (len(figures) + 1),
                    "caption": _caption(node, labels),
                    "section_id": section_id,
                    "section_title": section_title,
                    "source_uri": _href(graphics[0]) if graphics else "",
                    "asset_status": "source_uri_only" if graphics else "caption_only",
                }
            )
            return
        if tag == "table-wrap":
            label_node = next((child for child in node if _local(child.tag) == "label"), None)
            tables.append(
                {
                    "id": node.get("id") or "table-%d" % (len(tables) + 1),
                    "label": _label_text(label_node) or "Table %d" % (len(tables) + 1),
                    "caption": _caption(node, labels),
                    "section_id": section_id,
                    "section_title": section_title,
                    "rows": _table_rows(node, labels),
                    "asset_status": "structured" if _table_rows(node, labels) else "caption_only",
                }
            )
            return
        for child in node:
            visit(child, section_id, section_title)

    visit(root)
    return figures, tables


def parse(xml_text, journal=""):
    """Return text plus paper assets.

    Figures and tables are metadata/artifacts, not prose.  Keeping them in separate lists
    preserves the old section text contract while making source assets available to the paper
    artifact store.
    """
    root = ET.fromstring(xml_text)
    labels = reference_labels(root)
    front = front_matter(root, labels, journal)
    figures, tables = extract_assets(root, labels)
    pieces = []
    if front.get("abstract"):
        pieces.append(("Abstract", front["abstract"]))
    pieces.extend((title, body) for title, body in build_sections(root, labels) if body)
    return {"front": front, "sections": pieces, "figures": figures, "tables": tables}


def slugify(text, limit=48):
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text or "").strip("-").lower()
    return text[:limit] or "section"
