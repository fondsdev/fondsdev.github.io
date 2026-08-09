# fondsdev.github.io

The landing page for [`fonds`](https://github.com/fondsdev/fonds), served at
**[fonds.dev](https://fonds.dev)**.

One hand-written `index.html` with inline CSS. No build step, no dependencies,
no generator. GitHub Pages serves this repository's root directly, so pushing
to `main` is publishing.

Preview locally:

```bash
python3 -m http.server 8000
```

`tools/check_links.py` checks the page against a checkout of `fonds` — every
`blob/main/...` link resolves, every `pip install` extra exists. Run it against
a local clone:

```bash
python3 tools/check_links.py ../fonds
```

CI runs it on every push and weekly. The design is specified in
[`docs/superpowers/specs/2026-08-07-landing-page-design.md`](https://github.com/fondsdev/fonds/blob/main/docs/superpowers/specs/2026-08-07-landing-page-design.md)
over in the `fonds` repo.
