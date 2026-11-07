import sys, math, random
import os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
from assay_label_layout import plan_end_labels, segment_hits_rect, rects_intersect, stack_extent

def rightward_normal(dx, dy):           # même convention que core.track_layout (vérifiée ci-dessous)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.track_layout import rightward_normal as rn
    return rn(dx, dy)

random.seed(11)
N = 0; bad = {"leader_hits_label": 0, "labels_overlap": 0, "on_tracks": 0, "below_limit": 0, "dropped": 0}
worst = None
for trial in range(20000):
    ang = random.choice([random.uniform(25, 155), random.uniform(205, 335)])   # trous qui descendent (y>0) ou montent
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)                      # y vers le bas
    nx, ny = rightward_normal(ux, uy); nl = math.hypot(nx, ny); nx, ny = nx/nl, ny/nl
    nlab = random.choice([1, 2, 3])
    spacing = random.uniform(3.5, 8.0); t0 = random.uniform(4, 12)
    ts = [t0 + k*spacing for k in range(nlab)]
    ax0, ay0 = random.uniform(100, 500), random.uniform(100, 400)
    anchors = [(ax0 + nx*t, ay0 + ny*t, t) for t in ts]
    sizes = [(random.uniform(28, 52), random.uniform(8, 12)) for _ in range(nlab)]
    res = plan_end_labels(anchors, (ux, uy), (nx, ny), sizes)
    N += 1
    rects = [r["rect"] for r in res if r]; leaders = [r["leader"] for r in res if r]
    bad["dropped"] += sum(r is None for r in res)
    for i, ri in enumerate(res):
        if not ri: continue
        for j, rj in enumerate(res):
            if rj:
                if segment_hits_rect(*ri["leader"], rj["rect"], pad=0.4): bad["leader_hits_label"] += 1
                if j > i and i != j and rects_intersect(ri["rect"], rj["rect"]): bad["labels_overlap"] += 1
        # le nom ne recouvre pas la bande des pistes (derrière la fin du trou)
        x, y, w, h = ri["rect"]
        lo, hi = min(ts) - 3.5, max(ts) + 3.5
        for fx in (0, .25, .5, .75, 1):
            for fy in (0, 1):
                px, py = x + fx*w - ax0, y + fy*h - ay0
                s = px*ux + py*uy; p = px*nx + py*ny
                if s < -0.01 and lo <= p <= hi: bad["on_tracks"] += 1; break
# limite basse (axe) : jamais de nom dessous
lim_fail = 0; lim_total = 0
for trial in range(5000):
    a = math.radians(random.uniform(30, 150)); ux, uy = math.cos(a), math.sin(a)
    nx, ny = rightward_normal(ux, uy); nl = math.hypot(nx, ny); nx, ny = nx/nl, ny/nl
    ts = [6, 12.5]; ax0, ay0 = 300, 200; limit = ay0 + random.uniform(10, 60)
    anchors = [(ax0+nx*t, ay0+ny*t, t) for t in ts]
    res = plan_end_labels(anchors, (ux, uy), (nx, ny), [(40, 10)]*2, y_limit=limit)
    for r in res:
        if r: 
            lim_total += 1
            if r["rect"][1] + r["rect"][3] > limit + 1e-6: lim_fail += 1
print("configurations testées :", N)
print({k: v for k, v in bad.items() if k != "dropped"}, "| noms abandonnés (aucun problème de place) :", bad["dropped"])
print("limite basse : dépassements", lim_fail, "sur", lim_total, "noms placés")
# cas réel : les 2 éléments Li/Rb de l'export ZRA (trou 4 vers le bas-gauche)
a = math.radians(122); ux, uy = math.cos(a), math.sin(a)
nx, ny = rightward_normal(ux, uy); nl = math.hypot(nx, ny); nx, ny = nx/nl, ny/nl
anch = [(300+nx*t, 200+ny*t, t) for t in (7.0, 13.0)]
r = plan_end_labels(anch, (ux, uy), (nx, ny), [(34, 9.5), (38, 9.5)])
print("exemple Li/Rb :", [(round(x["leader"][2]), round(x["leader"][3]), [round(v) for v in x["rect"]]) for x in r], "| besoin vertical", round(stack_extent(2, 9.5, uy), 1), "px")
