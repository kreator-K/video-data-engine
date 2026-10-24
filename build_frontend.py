"""Validate and package the dependency-free frontend. Requires Node for JS checks."""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / 'frontend'


def build():
    subprocess.run(['node', 'frontend/analytics.test.mjs'], cwd=ROOT, check=True)
    subprocess.run(['node', '--input-type=module', '--check'], input=(FRONTEND / 'app.js').read_bytes(), check=True)
    fixture = json.loads((FRONTEND / 'data/design-preview.json').read_text())
    for path in FRONTEND.rglob('*'):
        if not path.is_file() or 'dist' in path.relative_to(FRONTEND).parts or path.name.endswith('.test.mjs') or path.suffix not in {'.html', '.js', '.mjs', '.css'}:
            continue
        name = str(path.relative_to(FRONTEND))
        if chr(0x2014) in (FRONTEND / name).read_text():
            raise ValueError(f'Em dashes are forbidden in frontend copy: {name}')
    if chr(0x2014) in json.dumps(fixture, ensure_ascii=False):
        raise ValueError('Em dashes are forbidden in preview content')
    destination = FRONTEND / 'dist'
    for name in ['index.html', 'app.js', 'analytics.mjs', 'styles.css', 'data/design-preview.json']:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FRONTEND / name, target)
    print('Frontend build validated:', destination)


if __name__ == '__main__':
    build()
