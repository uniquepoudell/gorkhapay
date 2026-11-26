# GorkhaPay

A free guide to sending money between Australia and Nepal: provider comparison with an estimate calculator,
how-to guides, a "send money" page that links to licensed providers, ad slots and affiliate links.

**GorkhaPay never takes, holds or moves money.** Doing that needs AUSTRAC registration in Australia and a
Nepal Rastra Bank licence in Nepal. The site informs and refers people to licensed providers only.

- `config.json`: providers (fees, speed, links), guides list, money settings, fallback exchange rate.
- `content/guides/*.html`: the body of each guide. Add a file and an entry in `guides` to publish a new one.
- `scripts/build.py`: writes the static site to `public/`, fetching today's AUD/NPR mid-market rate. Python standard library only.
- `.github/workflows/build.yml`: rebuilds daily and on every push, and publishes to GitHub Pages.
- `tests/test_build.py`: offline test.

Setup, domains, affiliate signups and income plan: **[GUIDE.md](GUIDE.md)**.

```bash
python scripts/build.py                          # writes ./public
SHOW_AD_PLACEHOLDERS=1 python scripts/build.py   # also shows ad and featured-agent spots
python -m http.server -d public 8000             # open http://localhost:8000
python tests/test_build.py
```
