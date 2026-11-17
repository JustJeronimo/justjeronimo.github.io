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

def tesseract_json(png, psm='3'):
    """Stand-in for Tesseract.js in tests: the same engine (tesseract CLI), same result shape."""
    import csv, io
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, 'in.png'), 'wb').write(png)
        subprocess.run(['tesseract', os.path.join(d, 'in.png'), os.path.join(d, 'out'), '--psm', psm, 'txt', 'tsv'], capture_output=True)
        text = open(os.path.join(d, 'out.txt')).read(); rows = list(csv.DictReader(io.StringIO(open(os.path.join(d, 'out.tsv')).read()), delimiter='\t', quoting=3))
    words, lines = [], {}
    for r in rows:
        if r['level'] != '5' or not (r.get('text') or '').strip(): continue
        x, y, w, h, c = (int(r['left']), int(r['top']), int(r['width']), int(r['height']), float(r['conf']))
        words.append({'text': r['text'], 'confidence': c, 'bbox': {'x0': x, 'y0': y, 'x1': x + w, 'y1': y + h}})
        k = (r['block_num'], r['par_num'], r['line_num']); L = lines.setdefault(k, {'w': [], 'x0': x, 'y0': y, 'x1': x + w, 'y1': y + h})
        L['w'].append((r['text'], c)); L['x0'] = min(L['x0'], x); L['y0'] = min(L['y0'], y); L['x1'] = max(L['x1'], x + w); L['y1'] = max(L['y1'], y + h)
    ls = [{'text': ' '.join(t for t, _ in L['w']), 'confidence': sum(c for _, c in L['w']) / len(L['w']), 'bbox': {k: L[k] for k in ('x0', 'y0', 'x1', 'y1')}} for L in lines.values()]
    return {'text': text, 'words': words, 'lines': ls}

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        import base64
        body = self.rfile.read(int(self.headers['Content-Length'])).decode()
        out = json.dumps(tesseract_json(base64.b64decode(body.split(',', 1)[1]), self.headers.get('X-Psm', '3'))).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(out)
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

    # 2. guided brew page: opens on the Brew step, hero timer, skip, stop → taste → log
    check('opens on brew step', 'Brew' in pg.inner_text('.fl-step.on .fl-sh'), pg.inner_text('.fl-step.on .fl-sh'))
    check('beans and gear folded in', pg.locator('.fl-step.done').count() == 3 and pg.locator('nav a').count() == 2)
    pg.click('[data-act=timerToggle]'); pg.evaluate('T.start = Date.now() - 62000'); pg.wait_for_timeout(500)
    check('timer shows pour 1', 'POUR 1' in pg.inner_text('#h-l').upper() and 'Pour to' in pg.inner_text('#h-s'), pg.inner_text('#h-l'))
    check('rolling counter digits', pg.locator('#h-t .rc').count() == 3 and pg.get_attribute('#h-t', 'aria-label') in ('1:02', '1:03'), str(pg.get_attribute('#h-t', 'aria-label')))
    check('step text animates on change', 'swap' in pg.eval_on_selector('#h-s', 'e => e.className'))
    pg.click('[data-act=timerSkip]'); pg.wait_for_timeout(300)
    check('skip jumps to pour 2', 'POUR 2' in pg.inner_text('#h-l').upper(), pg.inner_text('#h-l'))
    pg.screenshot(path='/tmp/drawdown-brew.png')
    pg.click('[data-act=timerStop]'); pg.wait_for_timeout(500)
    check('stop opens taste', 'Taste' in pg.inner_text('.fl-step.on .fl-sh'))
    pg.click('[data-act=tRate][data-id="4"]'); pg.click('[data-act=tTag][data-id=sweet]'); pg.fill('#t-notes', 'Stone fruit')
    pg.click('[data-act=tLog]'); pg.wait_for_timeout(700)
    nb = pg.evaluate('S.brews[0]')
    check('brew logged', pg.evaluate('S.brews.length') == 2 and nb['rating'] == 4 and nb['tags'] == ['sweet'] and nb['notes'] == 'Stone fruit' and nb['time'] >= 75, str(nb))
    pg.evaluate('closeSheet()'); pg.wait_for_timeout(500)
    pg.click('.fl-step [data-act=step][data-id="0"]'); pg.wait_for_timeout(500)
    check('beans step opens', pg.locator('[data-act=pickBean]').count() == 1)
    pg.screenshot(path='/tmp/drawdown-beans.png')
    pg.click('[data-act=pickBean]'); pg.wait_for_timeout(500)
    check('picking beans moves to recipe', 'Recipe' in pg.inner_text('.fl-step.on .fl-sh'))

    # 2b. DialKit-style sliders in Adjust: drag, tap-snap, type a value, grind steps
    pg.evaluate("goStep(2)"); pg.wait_for_timeout(400)
    pg.click('[data-act=editPlan]'); pg.wait_for_timeout(700)
    bx = pg.locator('.dk[data-for=p-water]').bounding_box(); y = bx['y'] + bx['height'] / 2
    pg.mouse.move(bx['x'] + 20, y); pg.mouse.down(); pg.mouse.move(bx['x'] + bx['width'] * .5, y, steps=6); pg.mouse.move(bx['x'] + bx['width'] * .4, y, steps=4); pg.mouse.up(); pg.wait_for_timeout(300)
    w = pg.evaluate("+document.getElementById('p-water').value")
    check('slider drag sets water', 300 <= w <= 340 and w % 5 == 0, str(w))
    pg.mouse.click(bx['x'] + bx['width'] * .2 + 2, y); pg.wait_for_timeout(600)
    check('slider tap snaps to a tenth', pg.evaluate("+document.getElementById('p-water').value") == 210, pg.evaluate("document.getElementById('p-water').value"))
    vb = pg.locator('#p-dose-o').bounding_box(); pg.mouse.click(vb['x'] + vb['width'] / 2, vb['y'] + vb['height'] / 2); pg.wait_for_timeout(300)
    pg.keyboard.press('Control+a'); pg.keyboard.type('16.5'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
    check('slider typed value', pg.evaluate("+document.getElementById('p-dose').value") == 16.5)
    gb = pg.locator('.dk[data-for=g-range]').bounding_box()
    pg.locator('.dk[data-for=g-range]').focus(); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(200)
    check('grind slider steps the Ode dial', pg.evaluate("readGrind()") == '4.2', pg.evaluate("readGrind()"))
    pg.screenshot(path='/tmp/drawdown-sliders.png')
    pg.click('#sheet-save'); pg.wait_for_timeout(500)
    check('adjust saves', pg.evaluate("curPlan().water") == 210 and pg.evaluate("curPlan().dose") == 16.5 and pg.evaluate("curPlan().grind") == '4.2', str(pg.evaluate("curPlan()")))
    pg.evaluate("save({ ...S.prefs, plan:null })"); pg.wait_for_timeout(300)

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
    # 5b. settings: version + update check
    pg.goto(URL + '#brew'); pg.wait_for_timeout(700)
    pg.click('[data-act=settings]'); pg.wait_for_timeout(700)
    ver = pg.evaluate('APP_VERSION')
    check('settings shows version', ver in pg.inner_text('#sheet-body'), ver)
    pg.click('[data-act=checkUpdate]'); pg.wait_for_timeout(900)
    check('update check says latest', 'latest version' in pg.inner_text('#upd'), pg.inner_text('#upd'))
    pg.screenshot(path='/tmp/drawdown-settings.png')
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
    # strawberry/lychee/rose with no roast printed → guessed light (a click finer), anaerobic → a click coarser
    check('web starter recipe', pg3.evaluate("Object.values(S.beans.find(b => b.name === 'Finca El Paraiso').recipes)[0]?.grind") == '4.1')
    check('no page errors (web scan)', not errs3, '; '.join(errs3))

    # 8. real bag photos through the full scan: canvas prep in Chrome, OCR by the tesseract engine, rules → recipe
    MOCK_TESS = "window.__psm='3';window.Tesseract={createWorker:async(l,n,o)=>({setParameters:async p=>{window.__psm=p.tessedit_pageseg_mode;},recognize:async c=>{o.logger({status:'recognizing text',progress:.5});const r=await fetch('/__ocr',{method:'POST',headers:{'X-Psm':window.__psm},body:c.toDataURL('image/png')});return {data:await r.json()};},terminate:async()=>{}})};"
    LABELS = [
      ('sogongera.png', {'b-name': 'Sogongera', 'b-roaster': 'Stean’s Beans', 'b-origin': 'Rwanda', 'b-process': 'Experimental', 'b-roast': 'medium-light'},
       {'dose': 15, 'water': 250, 'grind': '4.1', 'temp': 93}),
      ('motto.jpg', {'b-name': 'Motto', 'b-roaster': 'Stooker', 'b-origin': '75% Minas Gerais, Brazil / 25% Tolima, Colombia', 'b-process': 'Natural & Washed', 'b-roast': ''},
       {'dose': 15, 'water': 240, 'grind': '4.2', 'temp': 91}),
      ('bombe.jpg', {'b-name': 'Bombe', 'b-process': 'Natural', 'b-date': '2026-10-12', 'b-roast': ''},
       {'dose': 15, 'water': 240, 'grind': '4', 'temp': 94, 'bloomTime': 30}),
    ]
    notes_want = {'sogongera.png': 'Peach, Wild Strawberry, Speculaas, Chestnut', 'motto.jpg': 'Roasted Almond, Maple Syrup & Milk Chocolate', 'bombe.jpg': 'Strawberry, Blueberry jam, Lemon verbena'}
    for fn, want, rec in LABELS:
        pg4, errs4 = page(MOCK_TESS)
        pg4.clock.set_fixed_time('2026-11-17T20:00:00')
        pg4.goto(URL + '#beans'); pg4.wait_for_timeout(700)
        pg4.set_input_files('#pick', os.path.join(ROOT, 'drawdown', 'tests', 'labels', fn)); pg4.wait_for_timeout(1200)
        pg4.click('[data-act=readLabel]')
        pg4.wait_for_selector('#b-name', timeout=180000); pg4.wait_for_timeout(300)
        got = {k: pg4.evaluate(f"document.getElementById('{k}')?.value") for k in want}
        flav = pg4.evaluate("document.getElementById('b-flav')?.value")
        check(f'label {fn}: fields', got == want, f'{got} · notes: {flav}')
        check(f'label {fn}: tasting notes', flav == notes_want[fn], flav)
        pg4.click('#sheet-save'); pg4.wait_for_timeout(700)
        r = pg4.evaluate("(n => { const b = S.beans.find(b => b.name === n); return b ? Object.values(b.recipes || {})[0] || {} : {}; })", want['b-name'])
        check(f'label {fn}: recipe', all(r.get(k) == v for k, v in rec.items()), str({k: r.get(k) for k in list(rec) + ['why']}))
        check(f'label {fn}: no page errors', not errs4, '; '.join(errs4))
    b.close()
httpd.shutdown()
print('ALL PASS' if not fails else f'{len(fails)} FAILED: ' + ', '.join(fails))
sys.exit(1 if fails else 0)
