#!/usr/bin/env python3
"""Download your own abstract list from echo.ismrm.org.

Run it yourself in a terminal. The password is read with getpass, kept only in
memory and never written to disk; the session cookie is also memory-only.
After login it makes two read-only requests and saves:
  my_abstracts_all.bib  -- echo's BibTeX export of all your abstracts
  mine.html             -- the 'my abstracts' list page (carries the presentation type)

usage: fetch_echo_abstracts.py [out_dir]     (default: ./echo_dump)
The login email can be given in ECHO_EMAIL; otherwise it is asked for.
"""
import getpass
import http.cookiejar
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://echo.ismrm.org"
DELAY = 0.4  # seconds between requests


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "echo_dump"
    os.makedirs(out_dir, exist_ok=True)
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (personal abstract-list export)")]

    def get(url):
        time.sleep(DELAY)
        with opener.open(url, timeout=120) as r:
            return r.geturl(), r.read()

    email = os.environ.get("ECHO_EMAIL") or input("echo.ismrm.org login email: ").strip()
    password = getpass.getpass("Password (not echoed, not saved): ")
    get(BASE + "/auth/login")  # picks up the visitor cookie
    data = urllib.parse.urlencode({"email": email, "password": password, "remember_me": "on"}).encode()
    del password
    time.sleep(DELAY)
    opener.open(urllib.request.Request(BASE + "/auth/login?next=", data=data, method="POST"), timeout=120).close()

    final, page = get(BASE + "/abstracts/mine")
    if "/auth/login" in final:
        sys.exit("Login failed (redirected back to the login page). Nothing saved.")
    final, bibtex = get(BASE + "/abstracts/mine/export/all/bibtex")
    if "/auth/login" in final or not bibtex.lstrip().startswith(b"@"):
        sys.exit("BibTeX export did not return BibTeX (got %s). Nothing saved." % final)

    open(os.path.join(out_dir, "mine.html"), "wb").write(page)
    open(os.path.join(out_dir, "my_abstracts_all.bib"), "wb").write(bibtex)
    print("Saved %d BibTeX entries and the list page to %s" % (bibtex.count(b"\n@") + 1, os.path.abspath(out_dir)))


if __name__ == "__main__":
    main()
