# echo abstracts → publications.html

These scripts add ISMRM abstracts from [echo.ismrm.org](https://echo.ismrm.org/) to the **Conference Abstracts** section of `publications.html`. They add only abstracts that the page doesn't already list. Existing entries and the rest of the page stay byte-for-byte unchanged. They use only the Python 3 standard library.

## Update the page

1. **Download your abstract list.** Run this yourself in a terminal, because it asks for your echo password:

   ```
   python3 fetch_echo_abstracts.py echo_dump
   ```

   The password is read with `getpass` and is never stored. After login, the script saves two files:
   - `echo_dump/my_abstracts_all.bib`: echo's BibTeX export of all your abstracts.
   - `echo_dump/mine.html`: your abstract list page, which is where the presentation type (oral, power pitch, poster) comes from.

2. **Build the updated page** into a new file. The script refuses to overwrite its input.

   ```
   python3 build_abstracts.py --bib echo_dump/my_abstracts_all.bib --list echo_dump/mine.html \
       publications.html publications_new.html --log changes.log
   ```

   It prints how many abstracts are already on the page and how many it added. `changes.log` lists every correction it made to echo's data.

3. **Review and install.** Open `publications_new.html` in a browser and read `changes.log`. Then save a dated backup of the live page (`publications_YYYY_MM_DD.html`) and replace it.

`echo_dump/`, `publications_new.html` and `changes.log` are git-ignored. Don't commit them.

## What an entry looks like

```
K-S Chan, Y. Jun, A. Bhatt, B. Bilgic, S. Huang, H-H Lee; Beyond resolution limit of …;
ISMRM Workshop on White Matter: MR Imaging and Beyond, Marseille, France, 2026, oral presentation   [abstract]
```

- **Authors:** initials with full surnames; your own name is in bold italics.
- **Title:** plain text.
- **Meeting:** echo's meeting name, then city and year.
- **Tag:** *oral presentation*, *power pitch presentation* or *invited presentation*. Posters get no tag.
- **Link:** an **abstract** chip opens the public echo page for that abstract.

Within a year, the latest meeting comes first, then entries go in program-number order. New entries go above any entries already listed for that year.

## Corrections to echo's data

All of these are applied automatically and listed in the log:

- Line breaks, non-breaking spaces and LaTeX escapes in titles are cleaned up, and trailing periods are removed.
- Spaces echo lost when it dropped subscripts are put back, for example `T2mapping` → `T2 mapping`.
- Equal-contribution `*` markers are removed from names, and ALL-CAPS surnames are put in normal case.
- Known name slips are fixed through `SURNAME_FIX` and `NAME_FIX` in `build_abstracts.py`. Add to those tables when a new slip turns up.

## Limits

- echo only holds ISMRM meetings and workshops from 2018 onward. Abstracts from other venues still have to be added by hand.
- An abstract counts as already listed when its normalized title appears in an entry of the same year. If a title was edited by hand on the page, the abstract will be added a second time, so check the printed count.
- The fetch script depends on echo's current login form and export URL (`/abstracts/mine/export/all/bibtex`). If echo changes either one, the script stops without saving anything.
