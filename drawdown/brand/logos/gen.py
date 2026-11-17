import math
def spiral(cx,cy,r0,r1,turns,start=-90,n=220):
    pts=[]
    for i in range(n+1):
        t=i/n; th=math.radians(start)+t*turns*2*math.pi
        r=r0+(r1-r0)*t
        pts.append((cx+r*math.cos(th), cy+r*math.sin(th)))
    d="M%.2f %.2f "%pts[0]+" ".join("L%.2f %.2f"%p for p in pts[1:])
    return d
# mark: spiral pour seen from above, ending in an open ring (the timer)
def mark(stroke="#FF7A1A", sw=11, size=120):
    s=spiral(60,60,4,44,2.15,start=-90)
    return f'<path d="{s}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'
# monoline lowercase wordmark: "drawdown"
SW=11
def letters():
    out=[];x=0
    r=17; top=6; base=40; mid=23; asc=-20
    def bowl(cx): return f'M{cx+r} {mid} A{r} {r} 0 1 1 {cx-r} {mid} A{r} {r} 0 1 1 {cx+r} {mid}'
    adv=lambda w: w+14+SW
    # d
    out.append(bowl(x+r)+f' M{x+2*r} {asc} V{base}'); x+=adv(2*r)
    # r
    out.append(f'M{x} {top} V{base} M{x} {mid+2} A{r} {r} 0 0 1 {x+r} {top}'); x+=adv(r)-4
    # a
    out.append(bowl(x+r)+f' M{x+2*r} {top} V{base}'); x+=adv(2*r)
    # w
    out.append(f'M{x} {top} L{x+11} {base} L{x+22} {top+6} L{x+33} {base} L{x+44} {top}'); x+=adv(44)
    # d
    out.append(bowl(x+r)+f' M{x+2*r} {asc} V{base}'); x+=adv(2*r)
    # o
    out.append(bowl(x+r)); x+=adv(2*r)
    # w
    out.append(f'M{x} {top} L{x+11} {base} L{x+22} {top+6} L{x+33} {base} L{x+44} {top}'); x+=adv(44)
    # n
    out.append(f'M{x} {base} V{top} M{x} {mid} A{r} {r} 0 0 1 {x+2*r} {mid} V{base}'); x+=2*r
    return " ".join(out), x
WM, WW = letters()
def wordmark(color="#F2EFE9"):
    return f'<path d="{WM}" fill="none" stroke="{color}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>'
pad=SW/2+1
wm_box=(-pad, -20-pad, WW+2*pad, 60+2*pad)
open('wordmark.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{wm_box[0]} {wm_box[1]} {wm_box[2]:.1f} {wm_box[3]:.1f}">{wordmark("#0B0B0C")}</svg>')
open('mark.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">{mark()}</svg>')
icon=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect width="1024" height="1024" fill="#0B0B0C"/><g transform="translate(152 152) scale(6)">{mark(sw=11)}</g></svg>'
open('icon.svg','w').write(icon)
# lockup preview page
html=f'''<html><body style="margin:0;background:#0B0B0C;display:flex;flex-direction:column;gap:40px;padding:40px;align-items:flex-start">
<div style="display:flex;align-items:center;gap:28px"><svg width="140" height="140" viewBox="0 0 120 120">{mark()}</svg>
<svg height="96" viewBox="{wm_box[0]} {wm_box[1]} {wm_box[2]:.1f} {wm_box[3]:.1f}">{wordmark()}</svg></div>
<div style="display:flex;gap:30px;align-items:end">
<svg width="180" height="180" viewBox="0 0 1024 1024" style="border-radius:40px">{icon[icon.index(">")+1:-6]}</svg>
<svg width="60" height="60" viewBox="0 0 1024 1024" style="border-radius:14px">{icon[icon.index(">")+1:-6]}</svg>
<svg width="29" height="29" viewBox="0 0 1024 1024" style="border-radius:7px">{icon[icon.index(">")+1:-6]}</svg>
<div style="background:#F2EFE9;padding:24px;display:flex;align-items:center;gap:16px"><svg width="64" height="64" viewBox="0 0 120 120">{mark()}</svg><svg height="44" viewBox="{wm_box[0]} {wm_box[1]} {wm_box[2]:.1f} {wm_box[3]:.1f}">{wordmark("#0B0B0C")}</svg></div>
</div></body></html>'''
open('preview.html','w').write(html)
print(WW)
