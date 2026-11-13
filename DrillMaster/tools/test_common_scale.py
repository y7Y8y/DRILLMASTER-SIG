import sys, os, ast, math, types
sys.path.insert(0,"/home/claude/dm/DrillMaster/core")
from section_scale import *
print("== pas de graduation selon l'échelle seule (horizontal / vertical ×1 / vertical ×2) ==")
for n in (500,1000,2000,2500,5000):
    print(f"1:{n:<5} → {grid_step_for_ratio(n):>5g} m   | vertical ×2 : {grid_step_for_ratio(n,exag=2.0):>5g} m   | espacement papier ≈ {grid_step_for_ratio(n)*1000/n:.0f} mm")
# les 5 coupes KAB de l'utilisateur : longueurs et pas AVANT (auto) vs APRÈS (échelle commune)
sec={"002":258,"003":224,"004":195,"005":214,"006":303}
print("\n== pas horizontal AVANT (auto = nice(longueur/8)) vs APRÈS (1:1000) ==")
for k,L in sec.items(): print(f"coupe {k} ({L} m) : avant {nice_step(L/8):>4g} m → après {grid_step_for_ratio(1000):>3g} m")
# échelle écran : AVANT sx = fenêtre/longueur ; APRÈS sx constant
vw=1100
print("\n== px par mètre à l'écran (fenêtre 1100 px) ==")
for k,L in sec.items(): print(f"coupe {k} : avant {vw/L:5.2f} px/m   après {sx_for_ratio(1000):5.2f} px/m")
# vrai code de la coupe : _compute_scale / _common_ratio / _effective_ratio
src=open("/home/claude/dm/DrillMaster/ui/section_dock.py",encoding="utf-8").read(); tree=ast.parse(src)
want={"_compute_scale","_common_ratio","_effective_ratio"}; code={}
for n in ast.walk(tree):
    if isinstance(n,ast.ClassDef):
        for f in n.body:
            if isinstance(f,ast.FunctionDef) and f.name in want and f.name not in code: code[f.name]=ast.get_source_segment(src,f)
assert set(code)==want
ns=dict(__name__="DrillMaster.ui.section_dock",__package__="DrillMaster.ui",math=math,compute_isotropic_scales=lambda w,r,e:(max(w,1.0)/max(r,1e-9), max(w,1.0)/max(r,1e-9)*e))
sys.path.insert(0,"/home/claude/dm")
exec("class C:\n"+"\n".join(("    "+l if l.strip() else l) for c in code.values() for l in (c+"\n").splitlines()), ns); C=ns["C"]
class VP:
    def __init__(s,w): s.w=w
    def width(s): return s.w
def mk(L, ratio):
    c=C(); c._result=types.SimpleNamespace(max_along=L,min_along=0); c._v_exag=1.0; c._distance_unit="m"; c._fixed_sx=None
    c._margin_left=c._margin_right=96.0; c.viewport=lambda: VP(1100)
    cfg={"section_scale":{"ratio":ratio}} if ratio else {}
    c._parent_section=types.SimpleNamespace(main_dock=types.SimpleNamespace(project=types.SimpleNamespace(config=cfg)))
    return c
print("\n== vrai _compute_scale ==")
for ratio in (0,1000):
    sxs=[]
    for k,L in sec.items():
        c=mk(L,ratio); c._compute_scale(); sxs.append(round(c._sx,3))
    print(f"échelle {'auto' if not ratio else '1:'+str(ratio):<9}: sx par coupe = {sxs} → {'IDENTIQUES' if len(set(sxs))==1 else 'différents'}")
c=mk(214,1000); c._fixed_sx=sx_for_ratio(2000); print("export imposé 1:2000 → N effectif =", round(c._effective_ratio()), "| projet 1:1000 sans export → N effectif =", round(mk(214,1000)._effective_ratio()), "| auto →", mk(214,0)._effective_ratio())
