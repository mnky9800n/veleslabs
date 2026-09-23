# veleslabs.ai

The Veles Labs website. Static HTML, no build step, served by GitHub Pages at
<https://veleslabs.ai>.

```
index.html                     the website: hero, three tabs, contact
onepager.html                  the investor one-pager, not linked from the site
veleslabs-onepager.pdf         print of onepager.html, one A4 page
assets/storm.mp4               hero background loop
assets/storm-poster.jpg        first frame, shown before the video loads
assets/og.png                  social card, a screenshot of the hero
assets/logo.png, favicon.png   marks
assets/expert-analytics.png    partner logo, on the market tab
assets/*.jpg                   headshots
assets/jennifer-schematic.svg  cross-section, used by onepager.html only
tools/make_schematic.py        draws that cross-section
```

## The website

Everything lives in `index.html`: copy, CSS, the rig drawing, and the tab
script. Open it in a browser to see a change.

The four tabs are real tab panels, not separate pages. Each one has a hash
(`#company`, `#what-we-do`, `#market`, `#who-we-are`) so you can link straight to
it. The
hashes deliberately do not match the panel element ids, otherwise the browser
jumps down the page on load and draws a focus ring around the whole panel.

The hero video is greyscaled in CSS and then tinted by a teal-to-purple layer
in `mix-blend-mode: color`. That layer and the scrim below it must stay
`position: absolute`. An earlier `.hero > *` rule reset them to `relative` at
equal specificity and flattened the whole effect, so be careful adding any
descendant selector there.

Under `prefers-reduced-motion` the video is hidden and the poster shows
instead, so the poster needs to stay a frame that works as a still.

The market numbers are headline figures, so they are stat tiles rather than a
chart, and each one keeps a link to its source. The big numbers stay in ink;
teal and purple only appear as the rule above each tile.

`assets/expert-analytics.png` came from the Expert Analytics site, downscaled
from their full-resolution logo with its transparency intact. Worth confirming
with them that they are happy to be named and shown as a partner.

### Replacing the background video

Source clip is [Storm at Sea](https://www.pexels.com/video/storm-at-sea-1879456/)
from Pexels, free for commercial use with no attribution required. It is cut to
a seamless loop: the tail is crossfaded over the head so there is no visible
jump at the wrap.

```sh
ffmpeg -i source.mp4 -filter_complex "\
[0:v]trim=1.5:20.5,setpts=PTS-STARTPTS,scale=1600:900:force_original_aspect_ratio=increase,crop=1600:900[body];\
[0:v]trim=20.5:22,setpts=PTS-STARTPTS,scale=1600:900:force_original_aspect_ratio=increase,crop=1600:900[tail];\
[0:v]trim=0:1.5,setpts=PTS-STARTPTS,scale=1600:900:force_original_aspect_ratio=increase,crop=1600:900[head];\
[tail][head]xfade=transition=fade:duration=1.5:offset=0[blend];\
[body][blend]concat=n=2:v=1:a=0[out]" \
  -map "[out]" -an -c:v libx264 -preset slow -crf 31 -pix_fmt yuv420p \
  -movflags +faststart -r 25 assets/storm.mp4

ffmpeg -ss 0 -i assets/storm.mp4 -frames:v 1 -vf scale=1280:-1 -q:v 6 assets/storm-poster.jpg
```

Keep it under about 4MB. It is the heaviest thing on the page.

The rig silhouette is hand-drawn SVG inside `index.html`, positioned so its
legs meet the horizon in the footage. Change the clip and you will need to move
`.rig { top }` to match the new horizon.

### Rebuilding the social card

`assets/og.png` is just a screenshot of the hero at card size:

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --virtual-time-budget=9000 --hide-scrollbars \
  --window-size=1200,630 --force-device-scale-factor=1 \
  --screenshot="$PWD/assets/og.png" "file://$PWD/index.html"
```

## The one-pager

`onepager.html` is the investor sheet. Nothing on the website links to it, but
it is still served, so treat the URL as shareable rather than private.

To rebuild the PDF after editing it:

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --virtual-time-budget=8000 --no-pdf-header-footer \
  --print-to-pdf="$PWD/veleslabs-onepager.pdf" "$PWD/onepager.html"
```

It must come out as one A4 page. If it spills to two, lower the root font size
in the `@media print` block. It currently sits at 14px with the figure at 84%
width, which leaves very little slack, so adding a bullet or a person will push
it over.

The cross-section on that page is generated. Edit the geometry or colours in
`tools/make_schematic.py`, then `uv run tools/make_schematic.py`. That rewrites
`assets/jennifer-schematic.svg` and the inline `<svg>` in `onepager.html`.

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
