"""Native KiCad construction, using installed library symbols and pcbnew.
Run in a Python environment with system pcbnew and sexpdata available.
"""
from pathlib import Path
import copy, uuid, json, math, csv
import sexpdata as sx
S=sx.Symbol
ROOT=Path(__file__).resolve().parents[1]
def uid(): return str(uuid.uuid4())
def nodes(n,k): return [v for v in n if isinstance(v,list) and v and str(v[0])==k]
def node(n,k,d=None): return next(iter(nodes(n,k)),d)
def atom(n,k,d=''): return node(n,k,[None,d])[1]
def eff(sz=1): return [S('effects'),[S('font'),[S('size'),sz,sz]]]
def prop(k,v,x,y,hide=False):
 p=[S('property'),k,str(v),[S('at'),x,y,0],eff()]
 if hide: p.append([S('hide'),S('yes')])
 return p
CACHE={}
def symbol(lib,name):
 if lib not in CACHE:
  path=ROOT/'libraries'/f'{lib}.kicad_sym' if lib=='RoveFlight' else Path('/usr/share/kicad/symbols')/f'{lib}.kicad_sym'
  CACHE[lib]={str(v[1]):v for v in nodes(sx.loads(path.read_text()),'symbol')}
 a=copy.deepcopy(CACHE[lib][name]);base=atom(a,'extends')
 if base:
  b=symbol(lib,base);b[1]=name
  for v in nodes(b,'symbol'):v[1]=str(v[1]).replace(base+'_',name+'_',1)
  keys={v[1] for v in nodes(a,'property')}
  b=[v for v in b if not(isinstance(v,list) and v and str(v[0])=='property' and v[1] in keys)]
  b.extend(nodes(a,'property'));a=b
 return a
def pins(sym,unit=None):
 out=[]
 for b in nodes(sym,'symbol'):
  u=int(str(b[1]).rsplit('_',2)[1])
  if unit is None or u in [0,unit]:out+=nodes(b,'pin')
 return out
def pinmap(lib,name):return {str(atom(p,'number')):str(atom(p,'name')) for p in pins(symbol(lib,name))}
class Design:
 def __init__(self):
  self.parts=[];self.count={};self.section='';self.parent=None;self.note={}
  self.existing={c['ref']:c['uuid'] for c in json.loads((ROOT/'design.json').read_text())} if (ROOT/'design.json').exists() else {}
 def add(self,lib,name,value,nets,fp=None,xy=None,rot=0,ref=None,mpn='',mfr='',source='',side='F'):
  if ref is None:
   prefix={'R':'R','C':'C','C_Polarized':'C','D_Schottky':'D','D_TVS':'D','LED':'D','L':'L','Ferrite_Bead':'FB','Fuse':'F','Polyfuse':'F','SW_Push':'SW','TestPoint':'TP'}.get(name,'U')
   self.count[prefix]=self.count.get(prefix,0)+1;ref=prefix+str(self.count[prefix])
  else:
   import re
   a=re.match(r'([A-Z]+)(\d+)',ref)
   if a:self.count[a[1]]=max(self.count.get(a[1],0),int(a[2]))
  sym=symbol(lib,name)
  fp=fp or next((p[2] for p in nodes(sym,'property') if p[1]=='Footprint'),'')
  assert fp,(ref,'missing footprint')
  nums={str(atom(p,'number')) for p in pins(sym)}
  nets={str(k):v for k,v in nets.items()}
  assert not set(nets)-nums,(ref,set(nets)-nums)
  self.parts.append(dict(ref=ref,lib=lib,name=name,value=value,nets=nets,fp=fp,xy=xy,rot=rot,mpn=mpn or value,mfr=mfr,source=source,side=side,section=self.section,parent=self.parent,uuid=self.existing.get(ref,uid())))
  return ref
 def r(self,val,a,b,**kw):return self.add('Device','R',val,{'1':a,'2':b},fp='Resistor_SMD:R_0603_1608Metric',mpn='RC0603FR-07'+val.replace('.','L'),mfr='Yageo',**kw)
 def c(self,val,a,b,**kw):return self.add('Device','C',val,{'1':a,'2':b},fp=kw.pop('fp','Capacitor_SMD:C_0603_1608Metric'),mpn=kw.pop('mpn','SELECT_X7R_'+val),**kw)
 def conn(self,ref,nets,label,xy,kind='gh',rot=0):
  n=len(nets)
  if kind=='term':fp='TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-2-3.5-H_1x02_P3.50mm_Horizontal';mpn='1984617';mfr='Phoenix Contact'
  elif kind=='servo':fp='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical';mpn='61300311121';mfr='Wurth Elektronik'
  elif kind=='header':fp=f'Connector_PinHeader_2.00mm:PinHeader_1x{n:02}_P2.00mm_Vertical';mpn=f'M22-201{n:02}05';mfr='Harwin'
  else:fp=f'Connector_JST:JST_GH_SM{n:02}B-GHS-TB_1x{n:02}-1MP_P1.25mm_Horizontal';mpn=f'SM{n:02}B-GHS-TB(LF)(SN)';mfr='JST'
  return self.add('Connector_Generic',f'Conn_01x{n:02}',label,{str(i+1):v for i,v in enumerate(nets)},fp,xy,rot,ref,mpn,mfr)
 def led(self,ref,a,k,xy=None):return self.add('Device','LED','GREEN',{'1':k,'2':a},'LED_SMD:LED_0603_1608Metric',xy,ref=ref,mpn='LTST-C190KGKT',mfr='Lite-On')
 def switch(self,ref,a,b,xy):return self.add('Switch','SW_Push',ref,{'1':a,'2':b},'Button_Switch_SMD:SW_Push_1P1T-SH_NO_CK_KMR2xxG',xy,ref=ref,mpn='KMR221GLFS',mfr='C&K')
 def save(self):
  (ROOT/'design.json').write_text(json.dumps(self.parts,indent=2))
  with (ROOT/'BOM.csv').open('w') as f:
   w=csv.writer(f);w.writerow(['Reference','Value','MPN','Manufacturer','Footprint','Section','Datasheet'])
   for c in self.parts:w.writerow([c[k] for k in ['ref','value','mpn','mfr','fp','section','source']])
 def schematic(self):
  # Preserve the controller identity originally placed using the connected MCP.
  seed=ROOT/'mcp_seed.kicad_sch'
  if seed.exists():
   s=sx.loads(seed.read_text())
   for c in self.parts:
    for v in nodes(s,'symbol'):
     if any(p[1]=='Reference' and p[2]==c['ref'] for p in nodes(v,'property')):c['uuid']=atom(v,'uuid')
  prev=sx.loads((ROOT/'RoveFlight_S3.kicad_sch').read_text())
  rootid=atom(prev,'uuid',uid());previous_sheets={next((p[2] for p in nodes(sh,'property') if p[1]=='Sheetfile'),''):atom(sh,'uuid') for sh in nodes(prev,'sheet')};groups={}
  for c in self.parts:groups.setdefault(c['section'],[]).append(c)
  root=[S('kicad_sch'),[S('version'),20250114],[S('generator'),'eeschema'],[S('uuid'),rootid],[S('paper'),'A3'],[S('title_block'),[S('title'),'RoveFlight S3 | RF-S3-A0'],[S('rev'),'A.0 ENGINEERING PROTOTYPE'],[S('date'),'2026-11-08']],[S('lib_symbols')]]
  pages=[]
  for sec,cs in groups.items():
   multi=[];single=[]
   for c in cs:
    sym=symbol(c['lib'],c['name']);us={int(str(b[1]).rsplit('_',2)[1]) for b in nodes(sym,'symbol') if nodes(b,'pin')}-{0}
    (multi if len(us)>1 else single).append(c)
   for offset in range(0,len(single),20):pages.append((sec,single[offset:offset+20],offset//20))
   for c in multi:pages.append((sec,[c],len(single)//20+1))
  for idx,(sec,cs,sub) in enumerate(pages):
   file=f'{idx+1:02}_{sec.replace(" ","_")}_{sub+1}.kicad_sch';sheetid=previous_sheets.get(file,uid())
   sid=atom(sx.loads((ROOT/file).read_text()),'uuid') if (ROOT/file).exists() else uid()
   x=25.4+(idx%4)*96.52;y=55.88+(idx//4)*50.8
   root.append([S('sheet'),[S('at'),x,y],[S('size'),81.28,30.48],[S('fields_autoplaced'),S('yes')],[S('stroke'),[S('width'),.15],[S('type'),S('default')]],[S('fill'),[S('color'),0,0,0,0]],[S('uuid'),sheetid],prop('Sheetname',f'{idx+1:02} {sec} {sub+1}',x,y-2),prop('Sheetfile',file,x,y+33),[S('instances'),[S('project'),'RoveFlight_S3',[S('path'),'/'+rootid,[S('page'),str(idx+2)]]]]])
   doc=[S('kicad_sch'),[S('version'),20250114],[S('generator'),'eeschema'],[S('uuid'),sid],[S('paper'),'A3'],[S('title_block'),[S('title'),'RoveFlight S3 | '+sec],[S('rev'),'A.0 PROTOTYPE'],[S('date'),'2026-11-08']]]
   rowheights=[]
   for off in range(0,len(cs),4):
    spans=[]
    for cc in cs[off:off+4]:
     ys=[float(node(pp,'at')[2]) for pp in pins(symbol(cc['lib'],cc['name']))]
     spans.append(max(ys)-min(ys)+20.32 if ys else 35.56)
    rowheights.append(max(43.18,max(spans)))
   embedded={};items=[]
   for j,c in enumerate(cs):
    sym=symbol(c['lib'],c['name']);libid=c['lib']+':'+c['name'];sym[1]=libid;embedded[libid]=sym
    units=sorted({int(str(b[1]).rsplit('_',2)[1]) for b in nodes(sym,'symbol') if nodes(b,'pin')}-{0}) or [1]
    for ui,unit in enumerate(units):
     xx=50.8+(j%4)*96.52;yy=20.32+sum(rowheights[:j//4])+rowheights[j//4]/2
     if len(units)>1:xx=50.8+(ui%4)*96.52;yy=66.04+(ui//4)*76.2
     ymax=max([float(node(pp,'at')[2]) for pp in pins(sym,unit)] or [5.08]);refy=yy-ymax-10.16
     inst=[S('symbol'),[S('lib_id'),libid],[S('at'),xx,yy,0],[S('unit'),unit],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],[S('dnp'),S('no')],[S('uuid'),c['uuid'] if ui==0 else uid()],prop('Reference',c['ref'],xx,refy),prop('Value',c['value'],xx,refy+2.54),prop('Footprint',c['fp'],xx,yy,True),prop('MPN',c['mpn'],xx,yy,True),prop('Manufacturer',c['mfr'],xx,yy,True),prop('Datasheet',c['source'],xx,yy,True),[S('instances'),[S('project'),'RoveFlight_S3',[S('path'),'/'+rootid+'/'+sheetid,[S('reference'),c['ref']],[S('unit'),unit]]]]]
     if c['name']=='TestPoint':node(inst,'in_bom')[1]=S('no')
     for p in pins(sym,unit):
      num=str(atom(p,'number'));pa=node(p,'at');px=round(xx+float(pa[1]),4);py=round(yy-float(pa[2]),4);ang=float(pa[3]);net=c['nets'].get(num)
      inst.append([S('pin'),num,[S('uuid'),uid()]])
      if net is None:items.append([S('no_connect'),[S('at'),px,py],[S('uuid'),uid()]])
      else:
       ex=round(px-5.08*math.cos(math.radians(ang)),4);ey=round(py+5.08*math.sin(math.radians(ang)),4)
       items.append([S('wire'),[S('pts'),[S('xy'),px,py],[S('xy'),ex,ey]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
       items.append([S('global_label'),net,[S('shape'),S('passive')],[S('at'),ex,ey,ang],[S('fields_autoplaced'),S('yes')],eff(.95),[S('uuid'),uid()]])
     items.append(inst)
   note=self.note.get(sec,'All signal names are global nets. Logic is 3.3 V unless explicitly marked. See engineering documentation.')
   ne=eff(1.0);ne.append([S('justify'),S('left')]);items.append([S('text'),note,[S('at'),20.32,266.7,0],ne,[S('uuid'),uid()]])
   doc.extend([[S('lib_symbols'),*embedded.values()],*items,[S('embedded_fonts'),S('no')]])
   (ROOT/file).write_text(sx.dumps(doc)+'\n')
  flag=symbol('power','PWR_FLAG');flag[1]='power:PWR_FLAG';node(root,'lib_symbols').append(flag)
  for i,rail in enumerate(['GND','BAT_RAW','BAT_FUSED','BAT_PROTECTED','VM','SYS_IN','+3V3_SENS','REG_VINA','IR_VS']):
   x=180.34+i*25.4;y=35.56;ref='#FLG'+str(i+1)
   root.append([S('symbol'),[S('lib_id'),'power:PWR_FLAG'],[S('at'),x,y,0],[S('unit'),1],[S('in_bom'),S('no')],[S('on_board'),S('no')],[S('uuid'),uid()],prop('Reference',ref,x,y,True),prop('Value','PWR_FLAG',x,y-5,True),[S('pin'),'1',[S('uuid'),uid()]],[S('instances'),[S('project'),'RoveFlight_S3',[S('path'),'/'+rootid,[S('reference'),ref],[S('unit'),1]]]]])
   root.append([S('global_label'),rail,[S('shape'),S('passive')],[S('at'),x,y,0],eff(.85),[S('uuid'),uid()]])
  root.extend([[S('text'),'RoveFlight S3 / 1S brushed quadcopter.\nA.0 engineering prototype: see docs/Manufacturing_Readiness.md before fabrication.\nProtected 1S battery; external charger. USB forces motor disarm.\nGlobal nets join functional sheets. Six-layer board; 45 x 45 mm nominal.',[S('at'),25.4,20.32,0],[S('effects'),[S('font'),[S('size'),1.27,1.27]],[S('justify'),S('left')]],[S('uuid'),uid()]],[S('embedded_fonts'),S('no')]])
  (ROOT/'RoveFlight_S3.kicad_sch').write_text(sx.dumps(root)+'\n')
