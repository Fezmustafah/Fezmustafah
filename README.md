<div align="center">

<h3><code>fez@github ~ $ ./contributions.sh</code></h3>

<img src="./contrib-heatmap.svg" width="860" alt="Contribution heatmap" />

<br><br>

<h3><code>fez@github ~ $ whoami</code></h3>

<table>
  <tr>
    <td valign="top"><img src="./avi-ascii.svg" width="370" alt="ASCII portrait" /></td>
    <td valign="top"><img src="./info-card.svg" width="490" alt="Info card" /></td>
  </tr>
</table>

</div>

<!--
  Everything above is self-contained animated SVG (GitHub strips <script> and
  inline CSS from READMEs, but renders SVGs embedded via <img> and runs their
  SMIL / CSS-keyframe animations).

  Regenerate:
    python scripts/prep_photo.py <your-photo.jpg>   # once per photo
    python scripts/make_ascii_svg.py                # -> avi-ascii.svg
    python scripts/make_info_card.py                # -> info-card.svg
    python scripts/fetch_contributions.py           # -> data/contributions.json
    python scripts/render_heatmap_svg.py            # -> contrib-heatmap.svg

  The heatmap refreshes daily via .github/workflows/update-profile-art.yml
-->
