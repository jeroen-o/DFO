# DFO

Nieuwe website voor Bureau DFO (integratie van www2.dfobv.nl en dfo-opleidingen.nl), gehost via GitHub Pages.

- Statische HTML in de root, stijl in `assets/site.css`, geen build-step nodig voor hosting.
- Pagina's worden gegenereerd met `python3 _bron/build.py` uit de data in `_bron/` (opleidingen, documenten, columns).
- Opleidingen/agenda zijn een momentopname; aanmelden loopt via het opleidingsportaal.
