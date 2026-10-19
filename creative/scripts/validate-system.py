#!/usr/bin/env python3
"""Check portable file, provenance and claims invariants; no network or dependencies."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
CREATIVE = ROOT / 'creative'
errors = []
count = 0

def require(condition, message):
    if not condition:
        errors.append(message)

def load_json(path):
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        errors.append(f'{path.relative_to(ROOT)}: {exc}')
        return None

for path in CREATIVE.rglob('*.json'):
    load_json(path)
    count += 1

markdown = list(CREATIVE.rglob('*.md')) + list((ROOT / '.agents/skills').rglob('SKILL.md'))
for path in markdown:
    text = path.read_text()
    # Only Markdown link destinations, not sample output filenames in prose/templates.
    for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', text):
        target = match.group(1).strip('<>')
        if '://' in target or target.startswith(('#', 'mailto:')):
            continue
        target = unquote(target.split('#', 1)[0])
        if target:
            require((path.parent / target).exists(), f'{path.relative_to(ROOT)}: broken link {target}')

skills = list((ROOT / '.agents/skills').glob('*/SKILL.md'))
require(len(skills) == 5, f'Expected five scoped skills; found {len(skills)}')
for path in skills:
    text = path.read_text()
    match = re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
    require(bool(match), f'{path.relative_to(ROOT)}: invalid simple frontmatter')
    if match:
        name, description = match.groups()
        require(name == path.parent.name and len(name) < 64, f'{path}: skill name mismatch')
        require(0 < len(description) <= 1024 and '<' not in description and '>' not in description,
                f'{path}: invalid skill description')
    require('[TODO:' not in text, f'{path}: unfinished scaffold')

for manifest_path in sorted((CREATIVE/'assets').rglob('*manifest.json')):
    manifest = load_json(manifest_path)
    if not manifest:
        continue
    entries = manifest.get('assets', manifest.get('files', []))
    require(bool(entries), f'{manifest_path}: no hash entries')
    for entry in entries:
        path_value = entry.get('path', entry.get('local_path', entry.get('file')))
        require(bool(path_value), f'{manifest_path}: entry missing local path')
        if not path_value:
            continue
        source = ROOT / path_value
        if not source.exists():
            source = manifest_path.parent / path_value
        require(source.exists(), f'{manifest_path}: missing evidence {path_value}')
        if source.exists():
            require(hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256'],
                    f'{manifest_path}: evidence hash mismatch {path_value}')

ledger = load_json(CREATIVE/'claims/ledger.json')
template = load_json(CREATIVE/'claims/template.json')
if ledger and template:
    seen = set()
    for claim in ledger['records']:
        require(set(template) <= set(claim), f'{claim.get("id")}: missing claim fields')
        require(claim['id'] not in seen, f'Duplicate claim ID {claim["id"]}')
        seen.add(claim['id'])
        for key in ['location', 'compensation', 'availability', 'qualifications', 'review']:
            require(set(template[key]) <= set(claim[key]), f'{claim["id"]}: incomplete {key}')
        if claim['status'] == 'editorial_approved':
            require(bool(claim['sources']), f'{claim["id"]}: approval without source')
            for source in claim['sources']:
                require(bool(source['checked_at']) and bool(source['url_or_repo_path']),
                        f'{claim["id"]}: undated source')
            pay = claim['compensation']
            if pay['amount'] is not None:
                for field in ['currency_iso', 'pay_period', 'base_or_total', 'employer_confirmed_or_reported_estimate']:
                    require(bool(pay[field]), f'{claim["id"]}: salary lacks {field}')
                require(bool(claim['programme_year']) and bool(claim['location']['advertised_work_location']),
                        f'{claim["id"]}: salary lacks year/location')

capture = load_json(CREATIVE/'assets/captures/capture-record.json')
if capture:
    states = capture['states']
    require(states[0]['query'] == '' and states[-1]['query'] == 'Microsoft', 'Capture action/result mismatch')
    require(states[-1]['companyNames'] == ['Microsoft'], 'No verified final company match')
    for state in states:
        require((CREATIVE/'assets/captures'/state['file']).exists(), f'Missing capture {state["file"]}')

proof_manifest = load_json(CREATIVE/'examples/proof/render-manifest.json')
if proof_manifest:
    for source in proof_manifest['sources']:
        path = ROOT / source['path']
        require(path.exists(), f'Missing proof source {source["path"]}')
        if path.exists():
            require(hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'],
                    f'Proof source/output changed: {source["path"]}; refresh the render manifest after review')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print(f'PASS: {count} JSON files, {len(markdown)} Markdown files, five skills, evidence hashes, claim context and capture/result invariants.')
print('Not checked: online freshness, runtime discovery, creative quality, rights, real-time playback, phone or platform preview.')
