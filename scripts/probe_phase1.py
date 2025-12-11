import os, sys, asyncio, httpx
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from phase1_ocr_service.main import app

async def main():
    os.environ['PHASE1_USE_STUB_OCR']='true'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        r = await client.post('/v1/process', json={'source_path':'docs/sample.pdf','language':'en','dpi_override':300,'fast_mode':False})
        print(r.status_code)
        print(r.text)

asyncio.run(main())
