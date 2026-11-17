import math
src=open('gen.py').read()
exec(src.split("# mark:")[0])  # imports
exec("SW=11\n"+src[src.index("def letters"):src.index("pad=SW/2+1")])
def spiral_pts(cx,cy,r0,r1,turns,start,direction=1,n=260):
    pts=[]
    for i in range(n+1):
        t=i/n; th=math.radians(start)+direction*t*turns*2*math.pi; r=r0+(r1-r0)*t
        pts.append((cx+r*math.cos(th), cy+r*math.sin(th)))
    return pts
# 'd' mark: stream falls down the right side, enters the outer ring at 0deg and spirals inward clockwise (seen mirrored = d)
CX,CY,R=54,72,38
pts = spiral_pts(CX,CY,R,6,1.62,0,direction=1)
def mark_path():
    x0,y0=pts[0]
    return f'M{x0:.2f} 8 L{x0:.2f} {y0:.2f} ' + " ".join("L%.2f %.2f"%p for p in pts[1:])
MP = mark_path()
def mark(c="#FF7A1A", sw=12): return f'<path d="{MP}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
# viewbox for mark: x from CX-R-6 to x0+6, y 2..CY+R+6
x0=pts[0][0]
VB=f"{CX-R-7:.1f} 1 {x0+7-(CX-R-7):.1f} {CY+R+7-1:.1f}"
pad=SW/2+1; WVB=f"{-pad} {-20-pad} {WW+2*pad:.1f} {60+2*pad:.1f}"
def wordmark(c): return f'<path d="{WM}" fill="none" stroke="{c}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>'
ORANGE="#FF6B1A"; INK="#0B0B0C"; PAPER="#F2EEE6"
files={
 'mark-orange.svg': f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}">{mark(ORANGE)}</svg>',
 'mark-ink.svg': f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}">{mark(INK)}</svg>',
 'mark-paper.svg': f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}">{mark(PAPER)}</svg>',
 'wordmark-ink.svg': f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{WVB}">{wordmark(INK)}</svg>',
 'wordmark-paper.svg': f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{WVB}">{wordmark(PAPER)}</svg>',
}
# horizontal lockup: mark height = cap-to-baseline-ish of wordmark ascender..baseline (60 units) -> scale
mvb=[float(v) for v in VB.split()]; wvb=[float(v) for v in WVB.split()]
s = (wvb[3]) / mvb[3] * 1.15
mw = mvb[2]*s; gap=26
def lockup(cm, cw):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {mw+gap+wvb[2]:.1f} {mvb[3]*s:.1f}">'
            f'<g transform="scale({s:.4f}) translate({-mvb[0]:.2f} {-mvb[1]:.2f})">{mark(cm)}</g>'
            f'<g transform="translate({mw+gap:.1f} {(mvb[3]*s-wvb[3])/2+ (mvb[3]*s-wvb[3])*0.32:.1f}) translate({-wvb[0]:.2f} {-wvb[1]:.2f})">{wordmark(cw)}</g></svg>')
files['lockup-dark.svg']=lockup(ORANGE,PAPER)
files['lockup-light.svg']=lockup('#E8590C',INK)
files['mark-orange-paper.svg']=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}">{mark("#E8590C")}</svg>'
# app icon 1024: ink bg, orange mark centered, ~58% height
ih=680; isc=ih/mvb[3]; iw=mvb[2]*isc
files['app-icon.svg']=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect width="1024" height="1024" fill="{INK}"/>'
  f'<g transform="translate({(1024-iw)/2:.1f} {(1024-ih)/2:.1f}) scale({isc:.4f}) translate({-mvb[0]:.2f} {-mvb[1]:.2f})">{mark(ORANGE)}</g></svg>')
files['app-icon-orange.svg']=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect width="1024" height="1024" fill="{ORANGE}"/>'
  f'<g transform="translate({(1024-iw)/2:.1f} {(1024-ih)/2:.1f}) scale({isc:.4f}) translate({-mvb[0]:.2f} {-mvb[1]:.2f})">{mark(INK)}</g></svg>')
import os; os.makedirs('out',exist_ok=True)
for k,v in files.items(): open('out/'+k,'w').write(v)
inner=lambda f: open('out/'+f).read()
prev=f'''<html><body style="margin:0;background:{INK};padding:36px;display:flex;flex-direction:column;gap:34px">
<div style="height:110px">{inner('lockup-dark.svg').replace('<svg ','<svg height="110" ')}</div>
<div style="display:flex;gap:28px;align-items:flex-end">
{inner('app-icon.svg').replace('<svg ','<svg width="180" style="border-radius:40px;outline:1px solid #333" ')}
{inner('app-icon-orange.svg').replace('<svg ','<svg width="180" style="border-radius:40px" ')}
{inner('app-icon.svg').replace('<svg ','<svg width="60" style="border-radius:14px;outline:1px solid #333" ')}
{inner('app-icon.svg').replace('<svg ','<svg width="29" style="border-radius:7px;outline:1px solid #333" ')}
<div style="background:{PAPER};padding:22px 26px">{inner('lockup-light.svg').replace('<svg ','<svg height="56" ')}</div>
</div></body></html>'''
open('final-preview.html','w').write(prev)
