import sys, ast, math, types
sys.path.insert(0,"/home/claude/dm/DrillMaster/core"); sys.path.insert(0,"/home/claude/dm")
from section_scale import *
src=open("/home/claude/dm/DrillMaster/ui/section_dock.py",encoding="utf-8").read(); tree=ast.parse(src)
want={"_compute_scale","_common_ratio","_effective_ratio","_elev_window_mode","_project_elev_extrema","_apply_common_elev_window"}; code={}
for n in ast.walk(tree):
    if isinstance(n,ast.ClassDef):
        for f in n.body:
            if isinstance(f,ast.FunctionDef) and f.name in want and f.name not in code: code[f.name]=ast.get_source_segment(src,f)
assert set(code)==want, want-set(code)
ns=dict(__name__="DrillMaster.ui.section_dock",__package__="DrillMaster.ui",math=math,compute_isotropic_scales=lambda w,r,e:(max(w,1.0)/max(r,1e-9), max(w,1.0)/max(r,1e-9)*e))
exec("class C:\n"+"\n".join(("    "+l if l.strip() else l) for c in code.values() for l in (c+"\n").splitlines()), ns); C=ns["C"]
from DrillMaster.core.data_model import CollarRecord, DrillHole, TrajectoryPoint
def hole(i,z,L,dip=60):
    tr=[TrajectoryPoint(0,0,z-k*math.sin(math.radians(dip)),k) for k in (0,L/2,L)]
    return DrillHole(f"H{i}", CollarRecord(f"H{i}",0,0,z,L,110,-dip), trajectory=tr)
# les 5 coupes KAB de l'utilisateur (longueurs réelles lues sur les exports) : 002 258 m, 003 224, 004 195, 005 214, 006 303
secs={"002":(258,83,226),"003":(224,102,222),"004":(195,146,232),"005":(214,126,216),"006":(303,134,214)}
dhs=[hole(1,236,126),hole(2,224,120),hole(3,215,144),hole(4,198,102),hole(5,216,90)]
def mk(name, cfg, vw=1100):
    L,zmin,zmax=secs[name]
    c=C(); c._drillholes=dhs; c._elevation_grid_step=20.0; c._v_exag=1.0; c._distance_unit="m"; c._fixed_sx=None
    c._result=types.SimpleNamespace(max_along=L,min_along=0, min_elev=zmin, max_elev=zmax, data_min_elev=zmin+2, data_max_elev=zmax-2)
    c._line=types.SimpleNamespace(length=L)
    c._margin_left=c._margin_right=96.0
    c.viewport=lambda vw=vw: types.SimpleNamespace(width=lambda: vw)
    project=types.SimpleNamespace(config={**cfg,"sections":[{"id":i,"length":v[0]} for i,v in enumerate(secs.values())]})
    c._parent_section=types.SimpleNamespace(main_dock=types.SimpleNamespace(project=project))
    return c
def metrics(cfg, label, vw=1100):
    rows=[]
    for k in secs:
        c=mk(k,cfg,vw); c._compute_scale(); c._apply_common_elev_window(c._result)
        r=c._result; rows.append((k,c._sx,c._sy,r.max_elev-r.min_elev,r.min_elev,r.max_elev, c._effective_ratio()))
    print(f"\n== {label} ==")
    print("coupe | px/m horiz | px/m vert | 20 m vertical = px | fenêtre d'élévation | N")
    for k,sx,sy,h,lo,hi,n in rows: print(f"  {k}  |   {sx:6.3f}   |  {sy:6.3f}   |       {20*sy:5.1f}        |   {lo:g}..{hi:g} ({h:g} m)   | {n:g}")
    ident=len({round(r[1],6) for r in rows})==1 and len({round(r[2],6) for r in rows})==1
    wins=len({(r[4],r[5]) for r in rows})==1
    print(f"  → échelle identique : {ident} | fenêtre identique : {wins} | repère orthonormé (sx = sy) : {all(abs(r[1]-r[2])<1e-9 for r in rows)}")
    return rows
metrics({"section_scale":{"ratio":0,"elev_window":"auto"}}, "ANCIEN comportement (fenêtre par coupe) — ce que vous voyez")
r=metrics({}, "NOUVEAU PAR DÉFAUT (aucun réglage) : projet auto")
r2=metrics({}, "idem, fenêtre QGIS plus large (1600 px) — l'échelle ne doit pas bouger", vw=1600)
print("\nstabilité vis-à-vis de la fenêtre :", [round(a[1],4) for a in r]==[round(a[1],4) for a in r2])
metrics({"section_scale":{"ratio":500}}, "échelle fixe 1:500 choisie")
# N auto selon la plus longue coupe
print("\nN auto selon la plus longue coupe du projet :", {L:auto_project_ratio(L) for L in (60,150,250,303,330,500,1500,5000)})
