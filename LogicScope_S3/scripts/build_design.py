"""Native KiCad schematic construction from a reviewed pin-to-net manifest.

Preserves identities of components instantiated through the KiCad MCP server.
All land patterns come from installed KiCad libraries; no estimated footprints.
"""
from cadlib import *

TI='https://www.ti.com/lit/ds/symlink/sn74lvc245a.pdf'
ESP='https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf'
BUCK='https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf'
ESD='https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf'
USB='https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf'

# A datasheet-verified symbol for the permanently selected A-to-B mode.
base=symbol('74xx','74LS245');old='74LS245';name='SN74LVC245APW_A_TO_B'
base[1]=name
for unit in nodes(base,'symbol'):
    unit[1]=str(unit[1]).replace(old,name)
    for pin in nodes(unit,'pin'):
        number=int(atom(pin,'number'))
        if 2<=number<=9:pin[1]=S('input')
        elif 11<=number<=18:pin[1]=S('tri_state')
for field in nodes(base,'property'):
    if field[1]=='Value':field[2]='SN74LVC245APW'
    if field[1]=='Footprint':field[2]='Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm'
    if field[1]=='Datasheet':field[2]=TI
    if field[1]=='ki_fp_filters':field[2]='TSSOP*20*4.4x6.5mm*'
(ROOT/'libraries/LogicScope.kicad_sym').write_text(sx.dumps([S('kicad_symbol_lib'),[S('version'),20250114],[S('generator'),'kicad_symbol_editor'],base]))
# An original PCB probe feature, not an estimated component package. No paste.
probe=sx.loads(Path('/usr/share/kicad/footprints/TestPoint.pretty/TestPoint_Pad_D1.0mm.kicad_mod').read_text())
probe[1]='ProbePad_D0.5mm'
for q in nodes(probe,'pad'):node(q,'size')[1:]=[.5,.5]
for q in nodes(probe,'fp_circle'):
    if atom(q,'layer')=='F.CrtYd':node(q,'end')[1:]=[.4,0]
    elif atom(q,'layer')=='F.SilkS':node(q,'layer')[1]='F.Fab'
(ROOT/'libraries/LogicScope.pretty/ProbePad_D0.5mm.kicad_mod').write_text(sx.dumps(probe)+'\n')

d=Design()
def add(ref,lib,name,value,nets,fp=None,xy=None,rot=0,mpn='',mfr='',source=''):
    return d.add(lib,name,value,nets,fp=fp,xy=xy,rot=rot,ref=ref,mpn=mpn,mfr=mfr,source=source)
def r(ref,value,a,b,xy,rot=0):
    codes={'220':'220R','100k':'100K','10k':'10K','5.1k':'5K1','22':'22R','33':'33R','4.7k':'4K7','2.2k':'2K2'}
    size='0402' if ref in ('R32','R33') else '0603'
    fp='Resistor_SMD:R_0402_1005Metric' if size=='0402' else 'Resistor_SMD:R_0603_1608Metric'
    return add(ref,'Device','R',value,{'1':a,'2':b},fp,xy,rot,'RC'+size+'FR-07'+codes[value]+'L','Yageo','https://www.yageo.com/en/Product/Index/rchip')
def c(ref,value,a,b,xy,rot=0):
    specs={'100nF':('GRM188R71C104KA01D','C_0603_1608Metric'),
           '1uF':('GRM188R61A105KA61D','C_0603_1608Metric'),
           '10uF':('GRM21BR61A106KE19L','C_0805_2012Metric'),
           '22uF':('GRM21BR60J226ME39L','C_0805_2012Metric')}
    mpn,fp=specs[value]
    return add(ref,'Device','C',value,{'1':a,'2':b},'Capacitor_SMD:'+fp,xy,rot,mpn,'Murata','https://www.murata.com/en-global/products/capacitor/ceramiccapacitor')

d.section='Controller and Acquisition'
# Map the eight bus bits through GPIO matrix; physical order minimizes crossings.
gpio=[4,5,6,7,15,16,17,18]
module=pinmap('RF_Module','ESP32-S3-WROOM-1')
byname={v:k for k,v in module.items()}
n={'1':'GND','2':'+3V3','3':'EN','13':'USB_DM','14':'USB_DP','27':'BOOT',
   '17':'CAM_DE','18':'CAM_VSYNC','19':'CAM_PCLK','20':'SAMPLE_CLK',
   '21':'BUF_OE_N','22':'STATUS_LED','36':'UART_RX','37':'UART_TX','40':'GND','41':'GND'}
for bit,g in enumerate(gpio):n[byname['IO'+str(g)]]=f'D{bit}'
add('U1','RF_Module','ESP32-S3-WROOM-1','ESP32-S3-WROOM-1-N8R2',n,xy=(37,6),mpn='ESP32-S3-WROOM-1-N8R2',mfr='Espressif',source=ESP)
c('C1','100nF','+3V3','GND',(26.2,2.01),180)
c('C2','10uF','+3V3','GND',(23.0,2.0))
r('R1','10k','+3V3','EN',(14.5,1.5));c('C3','1uF','EN','GND',(17.75,1.5))
r('R2','10k','+3V3','BOOT',(48.5,18.0),90)
r('R3','10k','+3V3','BUF_OE_N',(39.7,22.0),90)
r('R4','33','SAMPLE_CLK','CAM_PCLK',(37.6,21.0))
r('R5','100k','CAM_PCLK','GND',(35.0,22.3))
r('R6','100k','CAM_DE','GND',(32.8,22.3))
r('R7','100k','CAM_VSYNC','GND',(32.8,24.1))
for ref,net,xy in [('SW1','EN',(49,22)),('SW2','BOOT',(49,27))]:
    add(ref,'Switch','SW_Push','RESET' if ref=='SW1' else 'BOOT',{'1':net,'2':'GND'},'Button_Switch_SMD:SW_Push_1P1T-SH_NO_CK_KMR2xxG',xy,mpn='KMR221GLFS',mfr='C&K',source='https://www.ckswitches.com/media/1464/kmr2.pdf')
add('J4','Connector_Generic','Conn_01x03','DEBUG 3V3 UART',{'1':'GND','2':'UART_TX','3':'UART_RX'},'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',(51,5),mpn='61300311121',mfr='Wurth Elektronik',source='https://www.we-online.com/en/components/products/WR-PHD_254MM_PIN_HEADER')
d.note[d.section]='Eight buffered signals enter CAM_DATA[7:0] concurrently via GPIO matrix.\nGPIO4/5/6/7/15/16/17/18 = D0..D7. GPIO12 -> 33R -> GPIO11 = sampling clock.\nGPIO9/10 drive and internally loop back DE/VSYNC. GPIO13 enables buffer (active LOW).\nNative USB GPIO19/20. Unused module pins are intentionally unconnected; N8R2 Quad PSRAM is not required for initial SRAM capture.'

d.section='Digital Input Protection'
head1={'1':'CH0','2':'GND','3':'CH1','4':'GND','5':'CH2','6':'GND','7':'CH3','8':'GND','9':'CH4','10':'GND'}
head2={'1':'CH5','2':'GND','3':'CH6','4':'GND','5':'CH7','6':'GND','7':'VREF_3V3','8':'GND'}
for ref,nets,label,xy in [('J1',head1,'CH0..4 + GROUNDS',(3.5,5)),('J2',head2,'CH5..7 / REF ONLY',(3.5,23))]:
    add(ref,'Connector_Generic','Conn_02x05_Odd_Even',label,nets,'Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical',xy,mpn='61301021121',mfr='Wurth Elektronik',source='https://www.we-online.com/en/components/products/WR-PHD_254MM_PIN_HEADER')
for bit in range(8):
    r('R'+str(10+bit),'220',f'CH{bit}',f'IN{bit}',(11,3.0+bit*2.0))
    r('R'+str(20+bit),'100k',f'IN{bit}','GND',(14.5,3.0+bit*2.0),0)
r('R28','10k','+3V3','VREF_3V3',(7.9,32.5))
for index in range(2):
    nets={'3':'GND','8':'GND'}
    for bit,pin in enumerate([1,2,4,5]):nets[str(pin)]=f'CH{index*4+bit}'
    add('U'+str(5+index),'Power_Protection','TPD4E05U06DQA','TPD4E05U06DQAR (OPTIONAL)',nets,xy=(8,11+index*16),mpn='TPD4E05U06DQAR',mfr='Texas Instruments',source=ESD)
    d.parts[-1]['dnp']=True
buf={'1':'+3V3','10':'GND','19':'BUF_OE_N','20':'+3V3'}
for bit in range(8):buf[str(2+bit)]=f'IN{bit}';buf[str(18-bit)]=f'D{bit}'
add('U2','LogicScope',name,'SN74LVC245APW',buf,xy=(20.5,9.0),mpn='SN74LVC245APW',mfr='Texas Instruments',source=TI)
c('C4','100nF','+3V3','GND',(23.5,4.2));c('C5','1uF','+3V3','GND',(20.0,3.5))
d.note[d.section]='External inputs: 0..5 V DIGITAL ONLY; 220R series + 100k pulldown each.\nU2 at 3.3V, DIR HIGH fixes A inputs -> B outputs; OE pullup disables outputs during reset.\nU5/U6 optional DNP low-capacitance ESD footprints; NC pins intentionally unused.\nHeader J2 pin 7 is a 10k-isolated reference, not a target power source. J2 pins 9/10 intentionally NC.'

d.section='USB and Power'
un={'A1':'GND','A4':'USB_5V','A5':'USB_CC1','A6':'USB_DP_CONN','A7':'USB_DM_CONN','A9':'USB_5V','A12':'GND',
    'B1':'GND','B4':'USB_5V','B5':'USB_CC2','B6':'USB_DP_CONN','B7':'USB_DM_CONN','B9':'USB_5V','B12':'GND','SH':'GND'}
add('J3','Connector','USB_C_Receptacle_USB2.0_16P','USB4105-GF-A',un,'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',(26,37),mpn='USB4105-GF-A',mfr='GCT',source='https://gct.co/connector/usb4105')
r('R30','5.1k','USB_CC1','GND',(20.3,31.2),90)
r('R31','5.1k','USB_CC2','GND',(31.7,31.2),90)
add('U4','Power_Protection','TPD2E2U06DCK','TPD2E2U06DCKR',{'1':'USB_DM_CONN','2':'USB_DP_CONN','3':'GND'},xy=(22.96,29.0),rot=90,mpn='TPD2E2U06DCKR',mfr='Texas Instruments',source=USB)
r('R32','22','USB_DP_CONN','USB_DP',(25.0,17.25),0)
r('R33','22','USB_DM_CONN','USB_DM',(25.0,15.98),0)
add('F1','Device','Polyfuse','500mA',{'1':'USB_5V','2':'VUSB'},'Fuse:Fuse_1206_3216Metric',(36,33.0),mpn='1206L050YR',mfr='Littelfuse',source='https://www.littelfuse.com/products/polyswitch-resettable-pptcs/surface-mount/1206l')
add('U3','Regulator_Switching','AP63203WU','AP63203WU-7',{'1':'+3V3','2':'VUSB','3':'VUSB','4':'GND','5':'SW','6':'BST'},xy=(43,31),mpn='AP63203WU-7',mfr='Diodes Incorporated',source=BUCK)
c('C6','10uF','VUSB','GND',(40.2,34.5),180)
c('C7','100nF','VUSB','GND',(40.2,31.5),90)
c('C8','100nF','BST','SW',(45.4,30.5),90)
add('L1','Device','L','4.7uH',{'1':'SW','2':'+3V3'},'Inductor_SMD:L_Bourns-SRN4018',(48,32.0),rot=0,mpn='SRN4018-4R7M',mfr='Bourns',source='https://www.bourns.com/docs/product-datasheets/srn4018.pdf')
c('C9','22uF','+3V3','GND',(46.5,37.0));c('C10','22uF','+3V3','GND',(42.7,37.0))
r('R34','4.7k','+3V3','PWR_LED_A',(51,31.0),90)
add('D1','Device','LED','PWR GREEN',{'1':'GND','2':'PWR_LED_A'},'LED_SMD:LED_0603_1608Metric',(51,33.8),rot=90,mpn='LTST-C190KGKT',mfr='Lite-On')
r('R35','2.2k','STATUS_LED','STATUS_LED_A',(42.5,22),90)
add('D2','Device','LED','CAPTURE GREEN',{'1':'GND','2':'STATUS_LED_A'},'LED_SMD:LED_0603_1608Metric',(45,22),rot=90,mpn='LTST-C190KGKT',mfr='Lite-On')
d.note[d.section]='USB 2.0 FULL SPEED only. D+ = GPIO20, D- = GPIO19. Both plug orientations wired.\nUSB-C CC1/CC2 each have 5.1k Rd. No target-power output. Buck input is USB only.\nAP63203 fixed 3.3V: FB senses output, VIN/EN on fused 5V, 100nF BST-to-SW.\nSBU pins unused. USB shield bonded to GND; USB_5V test point is not an accessory output.'

d.section='Test Points'
for i,(net,xy) in enumerate([('USB_5V',(34,36.5)),('VUSB',(38,36.5)),('+3V3',(44,26)),('GND',(38,26)),('EN',(46,24.5)),('USB_DP',(26.6,17.25)),('USB_DM',(26.6,15.98)),('CAM_PCLK',(37.7,24)),('CAM_DE',(33,26)),('CAM_VSYNC',(35,26)),('BUF_OE_N',(40,24))],1):
    add('TP'+str(i),'Connector','TestPoint',net,{'1':net},'LogicScope:ProbePad_D0.5mm' if net in ('USB_DP','USB_DM') else 'TestPoint:TestPoint_Pad_D1.0mm',xy,mpn='PCB_PAD',mfr='PCB')
d.save();d.schematic()
# Native dnp metadata and assembly BOM include the intentionally optional arrays.
for file in ROOT.glob('*.kicad_sch'):
    doc=sx.loads(file.read_text())
    for inst in nodes(doc,'symbol'):
        fields={p[1]:p[2] for p in nodes(inst,'property')}
        if fields.get('Reference') in ('U5','U6'):node(inst,'dnp')[1]=S('yes')
    file.write_text(sx.dumps(doc)+'\n')
with (ROOT/'BOM.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','MPN','Manufacturer','Footprint','DNP','Datasheet'])
    for part in d.parts:
        if part['ref'].startswith('TP'):continue
        w.writerow([part['ref'],part['value'],part['mpn'],part['mfr'],part['fp'],'YES' if part.get('dnp') else 'NO',part['source']])
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "LogicScope") (type "KiCad") (uri "${KIPRJMOD}/libraries/LogicScope.pretty") (options "") (descr "Reviewed project variants")))\n')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "LogicScope") (type "KiCad") (uri "${KIPRJMOD}/libraries/LogicScope.kicad_sym") (options "") (descr "Datasheet verified fixed-direction LVC buffer")))\n')
(ROOT/'GPIO_Allocation.csv').write_text('Channel,GPIO,Module_pad,Buffer_output_pad\n'+''.join(f'CH{bit},{g},{byname["IO"+str(g)]},{18-bit}\n' for bit,g in enumerate(gpio)))
with (ROOT/'Connector_Pinouts.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Pin','Signal'])
    for part in d.parts:
        if not part['ref'].startswith('J'):continue
        for pin,net in part['nets'].items():w.writerow([part['ref'],pin,net])
print('Built',len(d.parts),'electrical entries; exact input-bus mapping:',gpio)
