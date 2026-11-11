"""Generates animated 3D wireframe SVGs (SMIL) for the GitHub profile README."""
import math, os
from xml.sax.saxutils import escape

OUT = "assets"
os.makedirs(OUT, exist_ok=True)
FONT = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Liberation Mono',monospace"

# ---------- solids ----------
phi = (1 + 5 ** 0.5) / 2

def norm(vs):
    m = max(math.sqrt(x*x+y*y+z*z) for x, y, z in vs)
    return [(x/m, y/m, z/m) for x, y, z in vs]

def edges_by_len(vs, tol=1e-3):
    d = lambda a, b: math.dist(vs[a], vs[b])
    pairs = [(i, j) for i in range(len(vs)) for j in range(i+1, len(vs))]
    mn = min(d(i, j) for i, j in pairs)
    return [(i, j) for i, j in pairs if abs(d(i, j) - mn) < tol]

def icosa():
    v = []
    for a in (-1, 1):
        for b in (-phi, phi):
            v += [(0, a, b), (a, b, 0), (b, 0, a)]
    v = norm(v); return v, edges_by_len(v)

def cube():
    v = norm([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
    return v, edges_by_len(v)

def octa():
    v = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
    return v, edges_by_len(v)

def tetra():
    v = norm([(1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)])
    return v, edges_by_len(v)

def dodeca():
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for a in (-1/phi, 1/phi):
        for b in (-phi, phi):
            v += [(0, a, b), (a, b, 0), (b, 0, a)]
    v = norm(v); return v, edges_by_len(v)

def cube_stack():
    # three stacked slabs (a "storage engine" look)
    v, e = [], []
    for k, y0 in enumerate((-0.95, -0.2, 0.55)):
        base = len(v)
        for x in (-1.0, 1.0):
            for y in (y0, y0+0.4):
                for z in (-1.0, 1.0):
                    v.append((x, y, z))
        sub = [(i, j) for i in range(8) for j in range(i+1, 8)
               if sum(a != b for a, b in zip(v[base+i], v[base+j])) == 1]
        e += [(base+i, base+j) for i, j in sub]
    return norm(v), e

# ---------- animation ----------
def rot(p, ax, ay, az):
    x, y, z = p
    c, s = math.cos(ax), math.sin(ax); y, z = y*c - z*s, y*s + z*c
    c, s = math.cos(ay), math.sin(ay); x, z = x*c + z*s, -x*s + z*c
    c, s = math.cos(az), math.sin(az); x, y = x*c - y*s, x*s + y*c
    return x, y, z

def solid_svg(solid, cx, cy, r, dur, frames=72, tilt=(0.45, 0.0, 0.18),
              grad="g", dots=True, sw=1.6):
    vs, es = solid
    proj = []  # per frame: list of (sx, sy, z)
    for f in range(frames + 1):
        t = 2 * math.pi * f / frames
        fr = []
        for p in vs:
            x, y, z = rot(p, tilt[0], t, tilt[2])          # spin about Y
            x, y, z = rot((x, y, z), 0.25*math.sin(t), 0, 0)  # gentle wobble
            persp = 3.2 / (3.2 - z)
            fr.append((cx + x*r*persp, cy + y*r*persp, z))
        proj.append(fr)
    out = []
    fmt = lambda a: ";".join(f"{x:.1f}" for x in a)
    for i, j in es:
        x1 = fmt(fr[i][0] for fr in proj); y1 = fmt(fr[i][1] for fr in proj)
        x2 = fmt(fr[j][0] for fr in proj); y2 = fmt(fr[j][1] for fr in proj)
        op = ";".join(f"{0.25+0.75*((fr[i][2]+fr[j][2])/2+1)/2:.2f}" for fr in proj)
        a = f'dur="{dur}s" repeatCount="indefinite"'
        out.append(
            f'<line x1="{proj[0][i][0]:.1f}" y1="{proj[0][i][1]:.1f}" x2="{proj[0][j][0]:.1f}" y2="{proj[0][j][1]:.1f}" stroke="url(#{grad})" stroke-width="{sw}" stroke-linecap="round">'
            f'<animate attributeName="x1" values="{x1}" {a}/>'
            f'<animate attributeName="y1" values="{y1}" {a}/>'
            f'<animate attributeName="x2" values="{x2}" {a}/>'
            f'<animate attributeName="y2" values="{y2}" {a}/>'
            f'<animate attributeName="stroke-opacity" values="{op}" {a}/></line>')
    if dots:
        for k in range(len(vs)):
            xs = fmt(fr[k][0] for fr in proj); ys = fmt(fr[k][1] for fr in proj)
            rs = ";".join(f"{1.4+1.6*(fr[k][2]+1)/2:.1f}" for fr in proj)
            a = f'dur="{dur}s" repeatCount="indefinite"'
            out.append(f'<circle cx="{proj[0][k][0]:.1f}" cy="{proj[0][k][1]:.1f}" r="2" fill="#e0fbff" filter="url(#glow)">'
                       f'<animate attributeName="cx" values="{xs}" {a}/>'
                       f'<animate attributeName="cy" values="{ys}" {a}/>'
                       f'<animate attributeName="r" values="{rs}" {a}/></circle>')
    return "\n".join(out)

DEFS = """
<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#22d3ee"/><stop offset="0.55" stop-color="#818cf8"/><stop offset="1" stop-color="#c084fc"/>
</linearGradient>
<linearGradient id="txt" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#67e8f9"/><stop offset="0.5" stop-color="#a5b4fc"/><stop offset="1" stop-color="#e879f9"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-0.5 0;0.5 0;-0.5 0" dur="8s" repeatCount="indefinite"/>
</linearGradient>
<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="#22d3ee" stop-opacity="0.28"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/>
</radialGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="softglow" x="-20%" y="-20%" width="140%" height="140%">
  <feGaussianBlur stdDeviation="6"/>
</filter>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
  <path d="M28 0H0V28" fill="none" stroke="#1e293b" stroke-width="1"/>
</pattern>
"""

# ---------- HERO ----------
def hero():
    W, H = 1000, 340
    cx, cy = 790, 170
    ico = solid_svg(icosa(), cx, cy, 92, 14, frames=90, sw=1.8)
    inner = solid_svg(octa(), cx, cy, 34, 7, frames=60, tilt=(0.9, 0, 0.6), dots=False, sw=1.2)
    # orbit rings with travelling particles
    rings = ""
    for k, (rx, ry, rotd, d, col) in enumerate([(150, 42, -18, 6, "#22d3ee"), (138, 60, 24, 9, "#c084fc")]):
        rings += (f'<g transform="rotate({rotd} {cx} {cy})">'
                  f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-opacity="0.35" stroke-dasharray="3 6">'
                  f'<animate attributeName="stroke-dashoffset" values="0;-90" dur="6s" repeatCount="indefinite"/></ellipse>'
                  f'<circle r="4" fill="{col}" filter="url(#glow)"><animateMotion dur="{d}s" repeatCount="indefinite" '
                  f'path="M{cx-rx},{cy} a{rx},{ry} 0 1,0 {2*rx},0 a{rx},{ry} 0 1,0 {-2*rx},0"/></circle></g>')
    # floating particles
    import random; random.seed(7)
    parts = ""
    for _ in range(26):
        x, y = random.randint(20, W-20), random.randint(20, H-20)
        d = random.uniform(5, 11); r = random.uniform(0.8, 1.9)
        parts += (f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="#67e8f9" opacity="0">'
                  f'<animate attributeName="opacity" values="0;0.8;0" dur="{d:.1f}s" begin="{random.uniform(0,6):.1f}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="cy" values="{y};{y-30}" dur="{d:.1f}s" begin="{random.uniform(0,6):.1f}s" repeatCount="indefinite"/></circle>')
    roles = ["Backend Engineer", "GenAI &amp; Agentic AI Builder", "Distributed Systems Tinkerer", "Full-Stack Developer"]
    n = len(roles); per = 3.0; total = n*per
    role_txt = ""
    for i, r in enumerate(roles):
        kt = [0, i/n, (i+0.08)/n, (i+0.92)/n, (i+1)/n, 1]
        vals = ["0", "0", "1", "1", "0", "0"]
        if i == 0: kt, vals = [0, 0.08/n, 0.92/n, 1/n, 1], ["1", "1", "1", "0", "0"]
        role_txt += (f'<text x="60" y="212" font-family="{FONT}" font-size="21" fill="#e2e8f0" opacity="{1 if i==0 else 0}">'
                     f'<tspan fill="#22d3ee">&gt;</tspan> {r}'
                     f'<animate attributeName="opacity" values="{";".join(vals)}" keyTimes="{";".join(f"{k:.4f}" for k in kt)}" dur="{total}s" repeatCount="indefinite"/></text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>{DEFS}
<clipPath id="clip"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#clip)">
<rect width="{W}" height="{H}" fill="#070b14"/>
<rect width="{W}" height="{H}" fill="url(#grid)" opacity="0.7"/>
<rect x="0" y="-80" width="{W}" height="80" fill="#22d3ee" opacity="0.05">
  <animate attributeName="y" values="-80;{H}" dur="5s" repeatCount="indefinite"/></rect>
{parts}
<circle cx="{cx}" cy="{cy}" r="170" fill="url(#halo)"/>
{rings}
{ico}
{inner}
<text x="60" y="78" font-family="{FONT}" font-size="15" fill="#64748b">~/tanjiro1709 $ <tspan fill="#a5f3fc">whoami</tspan></text>
<text x="58" y="138" font-family="'Segoe UI','Inter','Helvetica Neue',Arial,sans-serif" font-size="46" font-weight="800" fill="url(#txt)">Sujal Kumar Agarwal</text>
{role_txt}
<rect x="62" y="240" width="0" height="2" fill="url(#g)">
  <animate attributeName="width" values="0;340;340" keyTimes="0;0.4;1" dur="4s" fill="freeze"/></rect>
<text x="60" y="280" font-family="{FONT}" font-size="14" fill="#94a3b8">NIT Rourkela · Ex-Fractal Analytics · VP @ Webwiz</text>
<text x="60" y="304" font-family="{FONT}" font-size="14" fill="#94a3b8">status: <tspan fill="#4ade80">● building</tspan> · learning · shipping<tspan fill="#22d3ee">▍<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan></text>
</g>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#1e3a5f"/>
</svg>'''
    open(f"{OUT}/hero.svg", "w").write(svg)

# ---------- PROJECT CARDS ----------
def wrap(s, n):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    lines.append(cur); return lines

def card(slug, title, tag, desc, tech, solid, accent, r=52):
    W, H = 480, 230
    shape = solid_svg(solid, 395, 112, r, 10, frames=72, sw=1.4)
    lines = wrap(desc, 40)[:4]
    dtxt = "".join(f'<text x="26" y="{98+i*20}" font-family="{FONT}" font-size="12.5" fill="#cbd5e1">{escape(l)}</text>' for i, l in enumerate(lines))
    px, pills = 26, ""
    for t in tech:
        w = 8 + len(t)*7.2
        pills += (f'<rect x="{px}" y="186" width="{w:.0f}" height="22" rx="11" fill="{accent}" fill-opacity="0.12" stroke="{accent}" stroke-opacity="0.55"/>'
                  f'<text x="{px+w/2:.0f}" y="201" text-anchor="middle" font-family="{FONT}" font-size="11" fill="{accent}">{escape(t)}</text>')
        px += w + 8
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>{DEFS}
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#111827"/></linearGradient>
<linearGradient id="border" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{accent}"/><stop offset="0.5" stop-color="#c084fc"/><stop offset="1" stop-color="{accent}"/>
  <animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="6s" repeatCount="indefinite"/>
</linearGradient>
<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#grid)" opacity="0.45"/>
<circle cx="395" cy="112" r="85" fill="url(#halo)"/>
{shape}
<text x="26" y="40" font-family="{FONT}" font-size="11" fill="{accent}" letter-spacing="2">{escape(tag.upper())}</text>
<text x="26" y="70" font-family="'Segoe UI','Inter','Helvetica Neue',Arial,sans-serif" font-size="25" font-weight="800" fill="#f1f5f9">{escape(title)}<tspan fill="{accent}">_<animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></tspan></text>
{dtxt}
{pills}
</g>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="15" fill="none" stroke="url(#border)" stroke-width="1.5" stroke-opacity="0.8"/>
</svg>'''
    open(f"{OUT}/card-{slug}.svg", "w").write(svg)

hero()
card("tachyon", "Tachyon", "AI inference serving",
     "Real-time LLM serving layer with dynamic size- and latency-bounded batching. 10x throughput, p99 < 50 ms at 64 req/s.",
     ["TypeScript", "Node.js", "Batching"], octa(), "#22d3ee")
card("strata", "Strata", "Storage engine",
     "My own Redis-style in-memory data store, built from scratch to learn how storage engines really work.",
     ["Systems", "Redis", "Networking"], cube_stack(), "#f472b6", r=62)
card("refactoriq", "RefactorIQ", "AI code review",
     "Full-stack AI code review platform: VS Code-style editor, GitHub OAuth, live review dashboard over SSE streaming.",
     ["Next.js", "Express", "SSE"], tetra(), "#a78bfa", r=62)
card("terraagent", "TerraAgent", "Agentic infra",
     "AI infra agent that turns plain-English prompts into live AWS provisioning: Gemini plans, AWS SDK v3 executes.",
     ["Gemini", "AWS SDK v3", "Agents"], dodeca(), "#4ade80")

# ---------- animated divider ----------
div = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="14" viewBox="0 0 1000 14">
<defs><linearGradient id="d" x1="0" x2="1"><stop offset="0" stop-color="#22d3ee" stop-opacity="0"/><stop offset="0.5" stop-color="#a78bfa"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/>
<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="4s" repeatCount="indefinite"/></linearGradient></defs>
<rect y="6" width="1000" height="2" rx="1" fill="url(#d)"/></svg>'''
open(f"{OUT}/divider.svg", "w").write(div)
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(f"{OUT}/{f}")//1024, "KB")
