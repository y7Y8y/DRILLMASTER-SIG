import sys, ast, math, types
sys.path.insert(0,"/home/claude/dm/DrillMaster/core"); sys.path.insert(0,"/home/claude/dm")
from section_scale import common_elev_window, grid_step_for_ratio, sx_for_ratio
print("== fenêtre pure : arrondie vers l'extérieur au pas ==")
for zmin,zmax,step in ((124.6,236.0,20),(77.2,238.4,20),(150.0,235.0,50),(198.0,201.0,5)):
    lo,hi=common_elev_window(zmin,zmax,step); print(f"z {zmin}..{zmax} pas {step} → fenêtre {lo:g}..{hi:g} (multiples du pas : {lo%step==0 and hi%step==0}, englobe les données : {lo<=zmin and hi>=zmax})")
src=open("/home/claude/dm/DrillMaster/ui/section_dock.py",encoding="utf-8").read(); tree=ast.parse(src)
want={"_elev_window_mode","_project_elev_extrema","_apply_common_elev_window","_effective_ratio","_common_ratio"}; code={}
for n in ast.walk(tree):
    if isinstance(n,ast.ClassDef):
        for f in n.body:
            if isinstance(f,ast.FunctionDef) and f.name in want and f.name not in code: code[f.name]=ast.get_source_segment(src,f)
assert set(code)==want, want-set(code)
ns=dict(__name__="DrillMaster.ui.section_dock",__package__="DrillMaster.ui",math=math)
exec("class C:\n"+"\n".join(("    "+l if l.strip() else l) for c in code.values() for l in (c+"\n").splitlines()), ns); C=ns["C"]
from DrillMaster.core.data_model import CollarRecord, DrillHole, TrajectoryPoint
def hole(i,z,L,dip=60):
    tr=[TrajectoryPoint(0,0,z-k*math.sin(math.radians(dip)),k) for k in (0,L/2,L)]
    return DrillHole(f"H{i}", CollarRecord(f"H{i}",0,0,z,L,110,-dip), trajectory=tr)
# projet : collets de 198 à 236 m, trou le plus profond 150 m (dip 60) → z min ≈ 105
dhs=[hole(1,236,126),hole(2,224,120),hole(3,215,144),hole(4,198,102),hole(5,230,60)]
def sr(zmin,zmax,dmin,dmax): return types.SimpleNamespace(min_elev=zmin,max_elev=zmax,data_min_elev=dmin,data_max_elev=dmax)
def mk(mode, ratio=0):
    c=C(); c._drillholes=dhs; c._elevation_grid_step=20.0; c._v_exag=1.0; c._distance_unit="m"; c._fixed_sx=None
    cfg={"section_scale":{"ratio":ratio,"elev_window":mode}}
    c._parent_section=types.SimpleNamespace(main_dock=types.SimpleNamespace(project=types.SimpleNamespace(config=cfg)))
    return c
# 3 coupes de plages très différentes (celles de l'utilisateur : 002/003/004-like)
secs=[sr(83.0,226.0,85.0,224.0), sr(106.0,223.0,108.0,221.0), sr(146.0,232.0,150.0,230.0)]   # cohérent : le projet descend à ≈90 m
orig=[(s.min_elev,s.max_elev,s.data_min_elev,s.data_max_elev) for s in secs]
print("\n== AVANT (auto) : fenêtres propres à chaque coupe ==")
for s in secs: print(f"  {s.min_elev:g}..{s.max_elev:g}  (hauteur {s.max_elev-s.min_elev:g} m)")
c=mk("project")
for s in secs: c._apply_common_elev_window(s)
print("== APRÈS (commune au projet) ==")
for s in secs: print(f"  {s.min_elev:g}..{s.max_elev:g}  (hauteur {s.max_elev-s.min_elev:g} m) graduations {s.data_min_elev:g}..{s.data_max_elev:g}")
w=set((s.min_elev,s.max_elev,s.data_min_elev,s.data_max_elev) for s in secs)
print("fenêtres identiques :", len(w)==1)
# idempotence + marge « noms de teneurs » déjà appliquée avant : doit être défaite proprement
for s in secs: s._assay_pad_m=7.5; s.min_elev-=7.5
for s in secs: c._apply_common_elev_window(s); c._apply_common_elev_window(s)
print("idempotent + marge restituée :", len(set((s.min_elev,s.max_elev) for s in secs))==1, "| marge remise à 0 :", all(s._assay_pad_m==0 for s in secs))
# retour à Auto : états d'origine restitués exactement
c2=mk("auto")
for s in secs: c2._apply_common_elev_window(s)
print("retour à « Auto » restitue l'état d'origine :", [(s.min_elev,s.max_elev,s.data_min_elev,s.data_max_elev) for s in secs]==orig)
# jamais d'écrêtage : une coupe dont les données dépassent la fenêtre du projet
big=sr(40.0,300.0,45.0,290.0); c._apply_common_elev_window(big); print("aucun écrêtage (données hors fenêtre conservées) :", big.min_elev<=40.0 and big.max_elev>=300.0)
# échelle imposée (export) : le pas d'arrondi suit l'échelle
c3=mk("project",1000); s=sr(100,230,100,230); c3._apply_common_elev_window(s); print("avec échelle 1:1000 : fenêtre", s.min_elev, s.max_elev, "| pas 1:1000 =", grid_step_for_ratio(1000))
# profil Auger : l'axe d'affichage est étiré, la fenêtre doit l'englober
aug=[hole(9,210,6,dip=90)]; c4=mk("project"); c4._drillholes=aug
c4._parent_section.main_dock.project.config["display_profiles"]={"enabled":True,"global":"AUGER"}
print("Auger (6 m) extrema d'affichage :", tuple(round(v,1) for v in c4._project_elev_extrema()), "(réel : 204.0..210.0)")
