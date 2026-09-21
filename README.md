# Reproducibility archive

This archive accompanies the JIIS manuscript. It contains sanitized publication code and derived artifacts only. No API credentials, proxy settings, cookies, raw response caches, benchmark images, or unrestricted copies of web snippets are included.

## Contents

- `analysis/`: aggregate and derived JSON plus statistical reports used by the manuscript.
- `scripts/`: publication analysis, validation, and figure-generation code.
- `tables/`: generated LaTeX table bodies.
- `figures/`: final vector publication figures.
- `protocols/`: frozen protocol documents available in the project record.
- `human_annotation/`: protocol and blank forms; no completed human validation is claimed.

## What can be reproduced locally

The included publication-level JSON files and plotting scripts support inspection and regeneration of the reported figures without new model calls. The table bodies are included exactly as submitted. Full recomputation from raw service responses requires the original licensed benchmark inputs and experiment result tree, which are not redistributed here. Scripts that expect that tree are retained for transparency and will fail with a clear missing-path error in this reduced archive.

## Environment

Recommended: Python 3.11+, NumPy, Matplotlib, pandas, statsmodels, PyMuPDF, Pillow, bibtexparser, beautifulsoup4, pylatexenc, requests, and python-docx. See `requirements.txt`.

## Provenance limits

Gateway-routed endpoints and judge services were logged by requested alias. The archive does not independently authenticate provider checkpoints. The three-family audit is automatic cross-alias agreement, not human semantic validation.

