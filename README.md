# veleslabs.ai

The VelesLabs investor one-pager, as a web page. Static HTML, no build step,
served by GitHub Pages at <https://veleslabs.ai>.

```
index.html                     the whole page: copy, CSS, and the figure inline
assets/                        logo, favicon, headshots, standalone copy of the figure
tools/make_schematic.py        draws the JENNIFER cross-section
veleslabs-onepager.pdf         print of the page, linked in the footer
CNAME                          custom domain for GitHub Pages
```

## Editing

Text, links and layout all live in `index.html`. Open it in a browser to see a
change; there is nothing to compile.

The cross-section is generated. Edit the geometry or colours in
`tools/make_schematic.py`, then:

```sh
uv run tools/make_schematic.py
```

That rewrites `assets/jennifer-schematic.svg` and the inline `<svg>` block in
`index.html`. The page uses the inline copy, so the page fonts reach the labels
inside the figure.

To rebuild the PDF after any change:

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --virtual-time-budget=8000 --no-pdf-header-footer \
  --print-to-pdf="$PWD/veleslabs-onepager.pdf" "$PWD/index.html"
```

It must come out as one A4 page. If it spills to two, lower the root font size
in the `@media print` block.

## Hosting

In the repo, Settings → Pages → Source: Deploy from a branch, `main`, `/ (root)`.
Set the custom domain to `veleslabs.ai` and tick Enforce HTTPS once the
certificate is issued.

At the registrar for `veleslabs.ai`, four A records and four AAAA records on the
apex, and one CNAME for www:

```
A     @     185.199.108.153
A     @     185.199.109.153
A     @     185.199.110.153
A     @     185.199.111.153
AAAA  @     2606:50c0:8000::153
AAAA  @     2606:50c0:8001::153
AAAA  @     2606:50c0:8002::153
AAAA  @     2606:50c0:8003::153
CNAME www   mnky9800n.github.io.
```

Propagation takes minutes to a day. The certificate is issued after the DNS
resolves, so Enforce HTTPS may be greyed out at first.
