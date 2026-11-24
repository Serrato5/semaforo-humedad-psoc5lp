import asyncio,sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':3024,'height':6048})
        await pg.goto('file:///home/claude/p6/poster.html'); await pg.wait_for_timeout(800)
        m=await pg.evaluate('''()=>{const r={};document.querySelectorAll('section,footer,header,main').forEach(e=>{const b=e.getBoundingClientRect();r[e.id||e.tagName]=[Math.round(b.top),Math.round(b.bottom)]});r.scroll=document.documentElement.scrollHeight;
        const w={};document.querySelectorAll('section').forEach(s=>{w[s.id]=s.innerText.split(/\\s+/).filter(x=>x).length});r.words=w;return r}''')
        print(m)
        await pg.screenshot(path='poster.png',full_page=False)
        if 'pdf' in sys.argv: await pg.emulate_media(media='screen'); await pg.pdf(path='Poster_Semaforo_PSoC_P6.pdf',prefer_css_page_size=True,print_background=True,page_ranges='1')
        await b.close()
asyncio.run(main())
