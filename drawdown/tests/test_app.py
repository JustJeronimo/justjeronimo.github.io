"""drawdown end-to-end checks. Run from the repo root:  python3 drawdown/tests/test_app.py
Needs: python playwright + a Chrome/Chromium (set CHROME=/path if not /usr/bin/google-chrome)."""
import os, sys, json, threading, functools, http.server, socketserver, re, subprocess, tempfile
from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
PORT = 8799
fails = []
def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (f'  ({info})' if info else ''))
    if not ok: fails.append(name)

# 0. script parses
html = open(os.path.join(ROOT, 'coffee', 'index.html')).read()
js = re.search(r'<script>([\s\S]*)</script>', html).group(1)
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f: f.write(js)
check('script parses', subprocess.run(['node', '--check', f.name]).returncode == 0)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
Handler = functools.partial(Quiet, directory=ROOT)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(('127.0.0.1', PORT), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{PORT}/coffee/'

SEED = {
 "setup_a": {"id": "setup_a", "kind": "setup", "created": 1, "name": "V60 at home", "brewer": "Hario V60", "grinderId": "fellow-ode-2", "grinder": "Fellow Ode Gen 2", "kettle": "Fellow Stagg EKG"},
 "bean_a": {"id": "bean_a", "kind": "bean", "created": 2, "name": "Kochere", "roaster": "Example Roasters", "origin": "Ethiopia", "process": "Washed"},
 "brew_a": {"id": "brew_a", "kind": "brew", "date": "2026-11-17T07:30:00Z", "setupId": "setup_a", "beanId": "bean_a", "dose": 15, "water": 250, "grind": "4.1", "temp": 94, "bloomWater": 45, "bloomTime": 45, "time": 172, "rating": 3, "tags": ["sour", "thin"], "notes": "Bright"},
 "prefs": {"id": "prefs", "kind": "prefs", "setupId": "setup_a", "plan": None}}

MOCK_AI = """
window.__calls=[];
window.claude={use:(n)=>Promise.resolve(n==='sample'?(()=>{
  const f=async()=>{throw {code:'x'}};
  f.json=(p,o)=>{const active=navigator.userActivation?navigator.userActivation.isActive:null; window.__calls.push({active,images:(o&&o.images||[]).length});
    if(!active) return Promise.reject({code:'needs_tap'});
    return Promise.resolve({bean:{name:'Kochere',roaster:'Test',origin:'Ethiopia',process:'Washed',roastLevel:'light',roastDate:''},recipe:{dose:15,water:250,grind:'4.1',temp:94,bloomWater:45,bloomTime:45,targetTime:'3:00'}});};
  f.limits=async()=>({images:true}); return f;})():null)};
"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    def page(init=None):
        pg = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, has_touch=True)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        if init: pg.add_init_script(init)
        pg.goto(URL); pg.evaluate(f"localStorage.setItem('brewlog-v1', JSON.stringify({json.dumps(SEED)}))"); pg.reload(); pg.wait_for_timeout(900)
        return pg, errs

    # 1. grinder table: every slider grinder round-trips its pour-over range
    pg, errs = page()
    bad = pg.evaluate("""() => GRINDERS.filter(g => g.kind !== 'text').filter(g => { const z = gZone(g); return !z || gStr(g, gIdx(g, g.po[0])) === '' || gIdx(g, g.po[1]) == null; }).map(g => g.id)""")
    check('grinder table parses', not bad, ','.join(bad))
    check('name matching', pg.evaluate("matchGrinder('Fellow Ode Brew Grinder Gen 2')?.id === 'fellow-ode-2' && matchGrinder('Baratza Encore ESP')?.id === 'baratza-encore-esp' && !matchGrinder('my weird grinder')"))

    # 1b. dial-in engine scenarios (Fellow Ode Gen 2 setup)
    D = pg.evaluate('''() => {
      const st = setupById('setup_a'), base = {id:'x', date:'2026-11-17T08:00:00Z', dose:15, water:250, grind:'4.1', temp:94, bloomWater:45, bloomTime:45, time:180};
      const adv = (b, hist=[]) => ruleAdvice({...base, ...b}, st, hist);
      return {
        sourFast: adv({tags:['sour','thin'], time:140}).next.grind,
        bitter: adv({tags:['bitter','astringent']}).next.grind,
        both: adv({tags:['sour','bitter']}),
        bracket: adv({grind:'5', tags:['sour']}, [{id:'p', date:'2026-11-16T08:00:00Z', grind:'3', tags:['bitter'], time:180}]).next.grind,
        good: adv({tags:['sweet','balanced'], rating:4}),
        tempLever: adv({grind:'3.1', tags:['sour']}, [{id:'p1', date:'2026-11-16T08:00:00Z', grind:'3.2', tags:['sour'], time:180},{id:'p2', date:'2026-11-15T08:00:00Z', grind:'4', tags:['sour'], time:180}]).next,
        lightEth: starterRecipe({roastLevel:'light', process:'Washed', origin:'Guji, Ethiopia', altitude:'2.100 m'}, st),
        darkNat: starterRecipe({roastLevel:'dark', process:'Natural', origin:'Brazil'}, st)
      };
    }''')
    check('dial-in: sour + fast → two steps finer', D['sourFast'] == '3.2', D['sourFast'])
    check('dial-in: bitter → coarser', D['bitter'] == '5', D['bitter'])
    check('dial-in: sour + bitter → coarser, uneven', D['both']['next']['grind'] == '4.2' and 'uneven' in D['both']['summary'], D['both']['summary'])
    check('dial-in: brackets between cups', D['bracket'] == '4', D['bracket'])
    check('dial-in: good cup is kept', D['good']['next']['grind'] == '4.1' and 'Lock it in' in D['good']['summary'])
    check('dial-in: temperature after two grind moves', D['tempLever']['grind'] == '3.1' and D['tempLever']['temp'] == 96, str(D['tempLever']))
    check('starter: light washed Ethiopian, high grown', D['lightEth']['temp'] == 97 and D['lightEth']['grind'] == '3.2' and D['lightEth']['water'] == 240, str(D['lightEth']))
    check('starter: dark natural', D['darkNat']['temp'] == 89 and D['darkNat']['grind'] == '5.1', str(D['darkNat']))
    check('grinder images exist', all(os.path.exists(os.path.join(ROOT, 'coffee', 'assets', 'grinders', i + '.png')) for i in pg.evaluate('GRINDERS.map(g => g.id)')))

    # 2. timer + log brew
    pg.click('[data-act=timerToggle]'); pg.evaluate('T.start = Date.now() - 62000'); pg.wait_for_timeout(500)
    check('timer shows pour 1', 'Pour 1' in pg.inner_text('#step-main'))
    pg.screenshot(path='/tmp/drawdown-brew.png')
    pg.click('[data-act=timerToggle]'); pg.click('[data-act=logTimed]'); pg.wait_for_timeout(500)
    pg.click('#sheet-save'); pg.wait_for_timeout(600)
    check('brew logged', pg.evaluate('S.brews.length') == 2)

    # 3. quick tip without AI moves the Ode one click finer
    check('rule tip', pg.evaluate("ruleAdvice(brewById('brew_a'), setupById('setup_a')).next.grind") == '3.2')

    # 4. sheet closes on drag
    pg.evaluate("openBrewDetail('brew_a')"); pg.wait_for_timeout(700)
    box = pg.locator('#sheet-top').bounding_box(); x = box['x'] + box['width'] / 2; y = box['y'] + 20
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x, y + 120, steps=4); pg.mouse.move(x, y + 300, steps=4); pg.mouse.up(); pg.wait_for_timeout(700)
    check('drag closes sheet', pg.evaluate("document.getElementById('sheet').hidden"))

    # 5. journal renders
    pg.goto(URL + '#journal'); pg.wait_for_timeout(800); pg.screenshot(path='/tmp/drawdown-journal.png')
    check('journal lists brews', pg.locator('.cell[data-act=brew]').count() >= 2)
    check('no page errors (web)', not errs, '; '.join(errs))

    # 6. AI scan inside Claude: call starts inside the tap
    from PIL import Image
    img = os.path.join(tempfile.gettempdir(), 'drawdown-bag.jpg'); Image.new('RGB', (1200, 1600), (200, 120, 60)).save(img)
    pg2, errs2 = page(MOCK_AI)
    pg2.goto(URL + '#beans'); pg2.wait_for_timeout(700)
    pg2.set_input_files('#pick', img); pg2.wait_for_timeout(1000)
    pg2.click('[data-act=readLabel]'); pg2.wait_for_timeout(700)
    calls = pg2.evaluate('window.__calls')
    check('AI call inside tap', bool(calls) and calls[0]['active'] is True and calls[0]['images'] == 1, str(calls))
    check('scan fills bean form', pg2.evaluate("document.getElementById('b-name')?.value") == 'Kochere')
    check('no page errors (AI)', not errs2, '; '.join(errs2))
    # 7. web version (no Claude): on-device label reader fills the form + starter recipe
    MOCK_OCR = "window.Tesseract={recognize:(s,l,o)=>{o.logger({status:'recognizing text',progress:.5});return Promise.resolve({data:{text:%s,lines:%s}});}};" % (
        json.dumps("FINCA EL PARAISO\nRoasted by Example Coffee Roasters\nColombia · Cauca\nProcess: Anaerobic washed\nVariety: Pink Bourbon, Caturra\nAltitude 1.850 masl\nTasting notes: strawberry, lychee, rose\nRoasted on 09/11/2026"),
        json.dumps([{"text": "FINCA EL PARAISO", "confidence": 90, "bbox": {"x0": 0, "y0": 0, "x1": 800, "y1": 120}}]))
    pg3, errs3 = page(MOCK_OCR)
    pg3.goto(URL + '#beans'); pg3.wait_for_timeout(700)
    pg3.set_input_files('#pick', img); pg3.wait_for_timeout(1000)
    pg3.click('[data-act=readLabel]'); pg3.wait_for_timeout(900)
    got = {k: pg3.evaluate(f"document.getElementById('{k}')?.value") for k in ['b-name', 'b-origin', 'b-process', 'b-date']}
    check('web label reader', got == {'b-name': 'Finca El Paraiso', 'b-origin': 'Cauca, Colombia', 'b-process': 'Anaerobic washed', 'b-date': '2026-11-09'}, str(got))
    pg3.click('#sheet-save'); pg3.wait_for_timeout(700)
    check('web starter recipe', pg3.evaluate("Object.values(S.beans.find(b => b.name === 'Finca El Paraiso').recipes)[0]?.grind") == '4.2')
    check('no page errors (web scan)', not errs3, '; '.join(errs3))
    b.close()
httpd.shutdown()
print('ALL PASS' if not fails else f'{len(fails)} FAILED: ' + ', '.join(fails))
sys.exit(1 if fails else 0)
