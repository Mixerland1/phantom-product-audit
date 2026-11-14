#!/usr/bin/env python3
"""Import original MDIS binaries without transcoding; verify and checksum."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = [
  [
    "awards/award-2002-information-technology.pdf",
    "iblock/11f/11ff038dfa7ca4b4b1b3f932b0c3437e.pdf"
  ],
  [
    "awards/award-2004-sea-and-river.pdf",
    "iblock/dff/dff33a58a90211ff68ec95ce6311285f.pdf"
  ],
  [
    "awards/award-2008-euraas.pdf",
    "iblock/f05/f056e3ce7a2e74c594c628670b65586f.pdf"
  ],
  [
    "awards/award-2008-transrussia.pdf",
    "iblock/dbc/dbca74aa76d559bde0e9a9a8cdf137b8.pdf"
  ],
  [
    "awards/award-2011-itenergy.pdf",
    "iblock/e35/e35bfffe9761ec67923cd5e0c8f4876c.pdf"
  ],
  [
    "reviews/mes-centre-2024.png",
    "medialibrary/144/14417d2d091470229766854bd837c760.png"
  ],
  [
    "reviews/mes-south-2024.png",
    "medialibrary/8bf/8bf3436a32badd77b7bed2021af9a38b.png"
  ],
  [
    "reviews/mes-ural-2024.png",
    "medialibrary/a9b/a9b7bcbcd8e78754a00a876a6d44f96a.png"
  ],
  [
    "reviews/mes-northwest-2024.png",
    "medialibrary/e4b/e4b84b04006c93ff290f02fd95ee1640.png"
  ],
  [
    "reviews/mes-siberia-2024.png",
    "medialibrary/6e2/6e238153bd8dcc0efddde2e2efaa25aa.png"
  ],
  [
    "reviews/mes-volga-2024.png",
    "medialibrary/51d/51dd5f7626439b1e0438f82fc1d466c9.png"
  ]
]
PNG_MAGIC = bytes.fromhex('89504e470d0a1a0a')

def main():
    manifest = []
    for name, suffix in ASSETS:
        path = ROOT / 'assets' / name
        if path.exists():
            raise SystemExit(f'Refusing to overwrite: {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        url = 'https://mdis.ru/upload/' + suffix
        subprocess.run(['curl','--fail','--location','--silent','--show-error',
                        '--retry','2','--connect-timeout','15','--max-time','80',
                        '--user-agent','Mozilla/5.0',
                        '--output',str(path),url],check=True)
        data = path.read_bytes()
        magic = b'%PDF-' if name.endswith('.pdf') else PNG_MAGIC
        if not data.startswith(magic) or len(data)<1000:
            path.unlink(missing_ok=True)
            raise SystemExit(f'Invalid source binary: {name}: {len(data)} bytes')
        sha = hashlib.sha256(data).hexdigest()
        manifest.append({'path':'assets/'+name,'source':url,'bytes':len(data),'sha256':sha})
        print('OK',name,len(data),sha,flush=True)
    (ROOT/'assets/original-asset-manifest.json').write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('IMPORTED',len(manifest),flush=True)

if __name__=='__main__':
    main()
