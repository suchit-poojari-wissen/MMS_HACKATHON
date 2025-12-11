import os
import sys
import asyncio
import httpx
from pathlib import Path

# Ensure workspace root import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from phase1_ocr_service.main import app

async def run_on(path: str):
    # Ensure non-stub mode
    os.environ['PHASE1_USE_STUB_OCR'] = 'false'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://local') as client:
        payload = {
            'source_path': path,
            'language': 'en',
            'dpi_override': 300,
            'fast_mode': False
        }
        r = await client.post('/v1/process', json=payload)
        print('Status:', r.status_code)
        print('Body:', r.text)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/run_phase1_on_file.py <absolute_path_to_pdf>')
        sys.exit(1)
    target = sys.argv[1]
    if not Path(target).exists():
        print(f'File not found: {target}')
        sys.exit(2)
    asyncio.run(run_on(target))
