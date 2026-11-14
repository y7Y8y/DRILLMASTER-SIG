import sys, os, ast, math, types
os.environ["QT_QPA_PLATFORM"]="offscreen"
sys.path.insert(0,"/home/claude/shim"); sys.path.insert(0,"/home/claude/dm")
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontMetricsF
app=QApplication([])
from DrillMaster.core import multi_assay as multi_assay_mod
from DrillMaster.core.data_model import CollarRecord, DrillHole, TrajectoryPoint
src=open("/home/claude/dm/DrillMaster/ui/section_dock.py",encoding="utf-8").read(); tree=ast.parse(src)
want={"_compute_scale","_common_ratio","_effective_ratio","_elev_window_mode","_project_elev_extrema","_apply_common_elev_window","_assay_label_font","_assay_label_context","_reserve_assay_label_room"}; code={}
for n in ast.walk(tree):
    if isinstance(n,ast.ClassDef):
        for f in n.body:
            if isinstance(f,ast.FunctionDef) and f.name in want and f.name not in code: code[f.name]=ast.get_source_segment(src,f)
assert set(code)==want, want-set(code)
ns=dict(__name__="DrillMaster.ui.section_dock",__package__="DrillMaster.ui",math=math,multi_assay_mod=multi_assay_mod,QFont=QFont,QFontMetricsF=QFontMetricsF,
        compute_isotropic_scales=lambda w,r,e:(w/r,w/r*e))
exec("class C:\n"+"\n".join(("    "+l if l.strip() else l) for c in code.values() for l in (c+"\n").splitlines()), ns); C=ns["C"]
class Pt:
    def __init__(s,d,a,e): s.depth,s.along,s.elevation=d,a,e
def dh(i,z,L,dip=60):
    tr=[TrajectoryPoint(0,0,z-k*math.sin(math.radians(dip)),k) for k in (0,L/2,L)]
    return DrillHole(f"H{i}", CollarRecord(f"H{i}",0,0,z,L,110,-dip), trajectory=tr)
dhs=[dh(1,236,126),dh(2,224,120),dh(3,215,144),dh(4,198,102),dh(5,216,90)]
# 5 coupes ; chaque coupe contient 1 trou ; le plus profond (H3, 144 m) est dans la coupe 003
specs={"002":(258,dhs[1]),"003":(224,dhs[2]),"004":(195,dhs[3]),"005":(214,dhs[4]),"006":(303,dhs[0])}
def mk(name):
    L,h=specs[name]; z0=h.collar.z; zE=h.trajectory[-1].z
    # fenêtre propre de la coupe = écart des données + marge standard (8 m)
    c=C(); c._drillholes=dhs; c._elevation_grid_step=20.0; c._v_exag=1.0; c._distance_unit="m"; c._fixed_sx=None
    sr=types.SimpleNamespace(max_along=L,min_along=0,min_elev=zE-8,max_elev=z0+3,data_min_elev=zE,data_max_elev=z0,
        holes=[types.SimpleNamespace(hole_id=h.hole_id, points=[Pt(t.depth, t.depth*math.cos(math.radians(60)), t.z) for t in h.trajectory],
               assays=[types.SimpleNamespace(attributes={"Li":100.0,"Rb":50.0})])])
    c._result=sr; c._line=types.SimpleNamespace(length=L)
    c._show_assays=True; c._assay_elements=["Li","Rb"]; c._element="Li"; c._assay_scales={"Li":1,"Rb":1}; c._show_depth=True
    c._track_plan=types.SimpleNamespace(by_key={"assays":types.SimpleNamespace(inner_edge=4.0,width=18.0,side="right")}); c._collar_info_font_size=7
    c._margin_left=c._margin_right=96.0; c.viewport=lambda: types.SimpleNamespace(width=lambda:1100)
    c._parent_section=types.SimpleNamespace(main_dock=types.SimpleNamespace(project=types.SimpleNamespace(config={"sections":[{"length":v[0]} for v in specs.values()]})))
    return c,sr
rows=[]
for k in specs:
    c,sr=mk(k); c._compute_scale(); c._apply_common_elev_window(sr); c._reserve_assay_label_room(sr)
    rows.append((k,sr.min_elev,sr.max_elev,round(sr._assay_pad_m,2)))
print("coupe | fenêtre finale | marge « noms de teneurs » ajoutée ensuite")
for k,lo,hi,pad in rows: print(f"  {k}  |  {lo:g}..{hi:g}  |  {pad} m")
print("fenêtres identiques sur les 5 coupes (noms de teneurs affichés) :", len({(r[1],r[2]) for r in rows})==1, "| aucune marge supplémentaire :", all(r[3]==0 for r in rows))
