#!/usr/bin/env python3
"""Add echo.ismrm.org abstracts that are missing from the Conference Abstracts section
of publications.html, and write the result to a new file.

Choices (approved 2026-10-18): match the existing entry style, initials + bold-italic
own name, an 'abstract' chip linking to the public echo page, tag oral / power pitch /
invited only (posters untagged), fix obvious echo data-entry slips (every fix is
written to the log), add only abstracts not already on the page. Existing entries
and everything outside the section are left byte-for-byte unchanged.

usage: build_abstracts.py --bib echo_dump/my_abstracts_all.bib --list echo_dump/mine.html \
           publications.html publications_new.html [--log changes.log]
"""
import argparse
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load import bib, ptypes, site, norm, clean_title  # noqa: E402

MONTHS = {m: i for i, m in enumerate("January February March April May June July August September October November December".split(), 1)}

# Surname-level fixes for echo data-entry slips (given-name slips vanish in initials).
SURNAME_FIX = {
    "Setsampop": "Setsompop", "Setsomepop": "Setsompop",
    "Daneshz": "Daneshzand", "Tounetki": "Tounekti",
    "Ramos Llordén": "Ramos-Llordén", "Ramos Llorden": "Ramos-Llordén", "Ramos-Llorden": "Ramos-Llordén",
}
# Whole-name fixes: (surname, given) -> rendered name
NAME_FIX = {
    ("Hyun Kang", "So"): "S.H. Kang",   # echo split So Hyun Kang as surname 'Hyun Kang'
    ("UMR", "ADEPT"): "ADEPT UMR",     # group author entered in name fields
    ("Lee", "Hong Hsi"): "H-H Lee",      # same person also entered as 'Hong-Hsi'
}
# Lost spaces where echo dropped sub/superscript formatting; plus one notation fix.
TITLE_FIX = [
    (r"\bT\*2(?=Mapping)", "T2*"),
    (r"\b([TBM][0-9]\*?)(and|mapping|Mapping|shim\w*|using)\b", r"\1 \2"),
    (r"\btheex vivohuman\b", "the ex vivo human"),
]
TAGS = {"Oral": "oral presentation", "Power Pitch": "power pitch presentation", "Invited": "invited presentation"}

log = []


def initials(given):
    out = []
    for tok in given.replace("‐", "-").split():
        if "-" in tok:
            out.append("-".join(p[0].upper() for p in tok.split("-") if p))
            out.append(" ")
        else:
            out.append(tok[0].upper() + ".")
    return "".join(out).replace(". ", ".").strip()


def fmt_name(a):
    raw = re.sub(r"\s+", " ", a).strip()
    a = raw.replace("*", "").replace("‐", "-")
    last, given = [x.strip() for x in a.split(",", 1)]
    if (last, given) in NAME_FIX:
        out = NAME_FIX[(last, given)]
    else:
        if last.isupper() and len(last) > 1:
            last = last.capitalize()
        last = SURNAME_FIX.get(last, last)
        ini = initials(given)
        out = ini + ("" if ini.endswith(" ") else " ") + last if ini else last
        out = re.sub(r"\s+", " ", out)
    if last == "Bilgic" and given == "Berkin":
        return "<b><i>B. Bilgic</i></b>"
    simple = initials(raw.split(",", 1)[1].strip()) + " " + raw.split(",", 1)[0].strip()
    if re.sub(r"\s+", " ", simple) != out:
        log.append("name: %r -> %r" % (raw, out))
    return html.escape(out, quote=False)


def fmt_title(t):
    t0 = re.sub(r"\s+", " ", clean_title(t))
    t1 = t0.replace("$$$T_{2}^{*}$$$", "T2*").replace("：", ": ").replace("‐", "-").replace(":  ", ": ")
    for pat, rep in TITLE_FIX:
        t1 = re.sub(pat, rep, t1)
    t1 = re.sub(r"\s+", " ", t1).strip().rstrip(".")
    if t1 != t0:
        log.append("title: %r -> %r" % (t0, t1))
    return html.escape(t1, quote=False)


def fmt_venue(b):
    venue = re.sub(r"^\d{4}\s+", "", b["booktitle"].strip())
    addr = b["address"].strip().replace("United States of America", "USA")
    if addr == "Singapore, Singapore":
        addr = "Singapore"
    if addr == "Online, Virtual":
        addr = "" if "Virtual" in venue else "Virtual"
    return html.escape(", ".join(x for x in (venue, addr, b["year"]) if x), quote=False)


def entry(b, num, ptype):
    uid = b["url"].rsplit("/", 1)[1]
    assert re.fullmatch(r"[0-9a-f-]{36}", uid)
    authors = ", ".join(fmt_name(a) for a in re.split(r"\s+and\s+", re.sub(r"\s+", " ", b["author"])))
    tag = ", <i>%s</i>" % TAGS[ptype] if ptype in TAGS else ""
    return ('<li class="pub-item"><span class="pub-num">%d</span><div class="pub-body">%s; %s; %s%s'
            '<div class="chips"><span class="chip"><a href="https://echo.ismrm.org/abstracts/view/%s">abstract</a></span></div></div></li>'
            % (num, authors, fmt_title(b["title"]), fmt_venue(b), tag, uid))


def progkey(note):
    return tuple(int(x) for x in re.findall(r"\d+", note.split(":", 1)[1]))


def main(bib_path, list_page, src, dst, logpath):
    B, P, S = bib(bib_path), ptypes(list_page), site(src)
    s = open(src, encoding="utf-8").read()
    # already on the page: same year and normalized echo title contained in the site entry text
    site_by_year = {}
    for e in S:
        site_by_year.setdefault(e["year"], []).append(norm(e["text"]))
    new = [b for b in B if not any(norm(clean_title(b["title"])) in t for t in site_by_year.get(b["year"], []))]
    print("echo %d, already on page %d, new %d" % (len(B), len(B) - len(new), len(new)))
    by_year = {}
    for b in new:
        by_year.setdefault(b["year"], []).append(b)
    i0 = s.find('id="conference-abstracts"')
    i1 = s.find('id="theses"')
    old_count = int(re.search(r'<span class="section-label">(\d+) entries</span>', s[i0:i1]).group(1))
    sec = s[i0:i1]
    blocks = []
    for y in sorted(by_year, reverse=True):
        # latest meeting first; within a meeting by program number; numbering continues above existing entries
        items = sorted(by_year[y], key=lambda b: (-MONTHS[b["month"]], b["booktitle"], progkey(b["note"])))
        existing = len(site_by_year.get(y, []))
        n = existing + len(items)
        lis = []
        for b in items:
            lis.append(entry(b, n, P.get(b["url"].rsplit("/", 1)[1])))
            n -= 1
        if existing:
            anchor = '<span class="year-label">%s</span><ol class="pub-list" reversed>' % y
            assert sec.count(anchor) == 1
            sec = sec.replace(anchor, anchor + "".join(lis))
        else:
            blocks.append('<span class="year-label">%s</span><ol class="pub-list" reversed>%s</ol>' % (y, "".join(lis)))
    first_year = re.search(r'<span class="year-label">', sec).start()
    sec = sec[:first_year] + "".join(blocks) + sec[first_year:]
    sec = sec.replace('<span class="section-label">%d entries</span>' % old_count,
                      '<span class="section-label">%d entries</span>' % (old_count + len(new)), 1)
    open(dst, "w", encoding="utf-8").write(s[:i0] + sec + s[i1:])
    open(logpath, "w", encoding="utf-8").write("\n".join(sorted(set(log))) + "\n")
    print("wrote", dst, "| section label", old_count, "->", old_count + len(new), "|", len(set(log)), "logged fixes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bib", required=True, help="echo BibTeX export (my_abstracts_all.bib)")
    ap.add_argument("--list", required=True, help="saved echo 'my abstracts' list page (mine.html)")
    ap.add_argument("page_in", help="current publications.html")
    ap.add_argument("page_out", help="where to write the updated page (a new file)")
    ap.add_argument("--log", default="changes.log", help="list of data fixes applied (default: changes.log)")
    a = ap.parse_args()
    if os.path.abspath(a.page_in) == os.path.abspath(a.page_out):
        sys.exit("page_out must differ from page_in; review the result, then replace the page yourself.")
    main(a.bib, a.list, a.page_in, a.page_out, a.log)
