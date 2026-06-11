#!/usr/bin/env python3
"""Validate ICO publication map deliverables."""

from pathlib import Path
import re
from PIL import Image

OUT = Path('/home/ubuntu/ico_publication_maps')
figures = [
    OUT / 'figure1_global_distribution_ico_projects.png',
    OUT / 'figure2_global_fundraising_concentration_bubble_map.png',
    OUT / 'figure3_leading_blockchain_fundraising_hubs.png',
]
report = OUT / 'ico_map_captions_and_interpretations.md'

errors = []
for fig in figures:
    if not fig.exists():
        errors.append(f'Missing figure: {fig}')
        continue
    with Image.open(fig) as im:
        dpi = im.info.get('dpi', (0, 0))
        width, height = im.size
        print(f'{fig.name}: {width}x{height}px, dpi={dpi}')
        if width < 2500 or height < 1400:
            errors.append(f'Figure resolution is unexpectedly low: {fig.name}')
        if dpi[0] < 299 or dpi[1] < 299:
            errors.append(f'Figure DPI metadata below 300: {fig.name} dpi={dpi}')

if not report.exists():
    errors.append(f'Missing report: {report}')
else:
    text = report.read_text(encoding='utf-8')
    for i in [1, 2, 3]:
        m = re.search(rf'## Figure {i}.*?\n\n\*\*Caption\.\*\*.*?\n\n\*\*Interpretation\.\*\* (.*?)(?=\n\n## Figure|\n\n## Output|\Z)', text, re.S)
        if not m:
            errors.append(f'Missing interpretation for Figure {i}')
            continue
        words = re.findall(r"\b[\w’'-]+\b", m.group(1))
        print(f'Figure {i} interpretation word count: {len(words)}')
        if not 100 <= len(words) <= 150:
            errors.append(f'Figure {i} interpretation outside 100-150 words: {len(words)}')

if errors:
    print('Validation failed:')
    for e in errors:
        print('-', e)
    raise SystemExit(1)
print('Validation passed: all figures meet 300 dpi minimum and all interpretations are within 100-150 words.')
