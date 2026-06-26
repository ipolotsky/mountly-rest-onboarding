# Sample documents

Drop the real source documents here to run the live tests and to regenerate the
golden fixtures. The files are git-ignored on purpose, so the repository never
carries real business documents.

Expected filenames:

- `mock_kbis.pdf` - the company registration (Kbis / SIRENE) PDF.
- `mock_rib.pdf` - the bank account details (RIB) PDF.
- one or more menu images, for example `menu_1.jpg`, `menu_2.png`, ...

With these in place:

- `pytest -m live` runs the parsers against the real Claude API (needs
  `ANTHROPIC_API_KEY`).
- `python tests/scripts/regen_fixtures.py` regenerates the golden fixtures in
  `tests/fixtures/` from the real files and API, then schema-validates them.

Without these files the deterministic suite still runs: it uses the hand-authored
golden fixtures and never calls the API or touches the network.
