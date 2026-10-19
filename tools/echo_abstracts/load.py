"""Readers for the echo.ismrm.org BibTeX export, the echo 'my abstracts' list page,
and the Conference Abstracts section of publications.html."""
import html as H
import re


def bib(path):
    """Entries of the echo BibTeX export as dicts of the fields echo writes."""
    s = open(path, encoding="utf-8").read()
    out = []
    for k, b in re.findall(r"@inproceedings\{([^,]+),(.*?)\n\}", s, re.S):
        d = {"key": k}
        for x in ["title", "author", "booktitle", "year", "month", "address", "note", "url"]:
            m = re.search(r"\n\s*" + x + r"\s*=\s*\{(.*?)\},?\s*\n", b + "\n", re.S)
            d[x] = m.group(1)
        out.append(d)
    return out


def site(path):
    """Existing Conference Abstracts entries of publications.html, with their year group."""
    s = open(path, encoding="utf-8").read()
    i = s.find('id="conference-abstracts"')
    j = s.find('id="theses"')
    sec = s[i:j]
    out = []
    for yr, blk in re.findall(r'<span class="year-label">(\d+)</span><ol class="pub-list" reversed>(.*?)</ol>', sec, re.S):
        for it in re.findall(r'<li class="pub-item">(.*?)</li>', blk, re.S):
            body = re.sub(r'<div class="chips">.*', "", it, flags=re.S)
            txt = H.unescape(re.sub(r"<[^>]+>", "", body))
            out.append({"year": yr, "html": it, "text": txt})
    return out


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def clean_title(t):
    """Collapse whitespace and undo the LaTeX escaping in echo's BibTeX titles."""
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace("\\textasciicircum{}", "^")
    t = re.sub(r"\\([&$_{}%#])", r"\1", t)
    return t


def ptypes(path):
    """uuid -> presentation type shown on the echo list card (None if the card shows only 'ISMRM Abstract')."""
    s = open(path, encoding="utf-8").read()
    firsts = []
    seen = set()
    for m in re.finditer(r'href="/abstracts/view/([0-9a-f-]{36})"', s):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            firsts.append((m.start(), m.group(1)))
    out = {}
    for k, (p, u) in enumerate(firsts):
        seg = s[(firsts[k - 1][0] if k else 0):p]
        seg = seg[seg.rfind("1st Author"):] if "1st Author" in seg else seg
        t = re.findall(r">\s*(Oral|Digital Poster|Traditional Poster|Power Pitch|Poster|Invited[^<]*|Educational[^<]*)\s*<", seg)
        out[u] = t[0].strip() if t else None
    return out
