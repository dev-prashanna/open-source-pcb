from route_utils import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
fig,ax=plt.subplots(figsize=(14,10))
for layer,col in [(p.B_Cu,'#287aca'),(p.F_Cu,'#ad3818')]:
 for g,net in zip(geoms[layer],owners[layer]):
  if g.geom_type!='Polygon': continue
  ax.add_patch(MP(np.asarray(g.exterior.coords),color=col,alpha=.65))
for ref,fp in fps.items():
 x,y=xy(fp);ax.text(x,y,ref,fontsize=6,color='black')
for net in ['CH2','CH3','IN7','SAMPLE_CLK']:
 for fp in b.GetFootprints():
  for q in fp.Pads():
   if q.GetNetname()==net:
    x,y=xy(q);ax.text(x,y-.3,f'{fp.GetReference()}.{q.GetNumber()}:{net}',fontsize=7,color='navy')
ax.set_xlim(0,55);ax.set_ylim(40,0);ax.set_aspect('equal');ax.grid(alpha=.2)
fig.savefig('/tmp/LogicScope_layout.png',dpi=180,bbox_inches='tight')
