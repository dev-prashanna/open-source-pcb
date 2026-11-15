"""Build TIWARI schematic and pin/part manifest using installed KiCad symbols.
Run with Python that has sexpdata. PCB layout is generated separately.
"""
from cadlib import *
(ROOT/'libraries').mkdir(exist_ok=True)
base=symbol('FPGA_Lattice','ICE40UP5K-SG48ITR')
base[1]='ICE40UP5K-SG48ITR_REVIEWED'
for unit in nodes(base,'symbol'):
 unit[1]=str(unit[1]).replace('ICE40UP5K-SG48ITR','ICE40UP5K-SG48ITR_REVIEWED')
 for pin in nodes(unit,'pin'):
  if str(atom(pin,'number'))=='29': pin[1]=S('power_in')
(ROOT/'libraries/TIWARI.kicad_sym').write_text(sx.dumps([S('kicad_symbol_lib'),[S('version'),20250114],[S('generator'),'kicad_symbol_editor'],base]))
(ROOT/'sym-lib-table').write_text('(sym_lib_table (lib (name "TIWARI") (type "KiCad") (uri "${KIPRJMOD}/libraries/TIWARI.kicad_sym") (options "") (descr "Reviewed UP5K pin 29 power input")))\n')
d=Design()
FPGA='https://www.latticesemi.com/api/document/download?id=51968'
FTDI='https://www.ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT2232H.pdf'
def add(ref,lib,name,value,nets,xy,fp=None,rot=0,mpn=None,source=''):
 return d.add(lib,name,value,nets,fp,xy,rot,ref,mpn or value,source=source)
res=0;cap=0
def r(value,a,b,xy,rot=0):
 global res;res+=1
 codes={'10k':'1002','100k':'1003','12k':'1202','2.2k':'2201','5.1k':'5101','1k':'1001','100':'1000','33':'33R0'}
 return add('R'+str(res),'Device','R',value,{'1':a,'2':b},xy,'Resistor_SMD:R_0603_1608Metric',rot,'RC0603FR-07'+{'10k':'10K','100k':'100K','12k':'12K','2.2k':'2K2','5.1k':'5K1','1k':'1K','100':'100R','33':'33R'}[value]+'L')
def c(value,a,b,xy,rot=0):
 global cap;cap+=1
 specs={'100n':('GRM188R71C104KA01D','0603_1608'),'1u':('GRM188R61A105KA61D','0603_1608'),'4.7u':('GRM21BR61A475KA73L','0805_2012'),'10n':('GRM188R71H103KA01D','0603_1608'),'27p':('GRM1885C1H270JA01D','0603_1608')}
 mpn,size=specs[value]
 return add('C'+str(cap),'Device','C',value,{'1':a,'2':b},xy,'Capacitor_SMD:C_'+size+'Metric',rot,mpn)
def header(ref,signals,xy,rot=90):
 n=len(signals)
 return add(ref,'Connector_Generic',f'Conn_01x{n:02}',ref+' / 3V3 ONLY',dict(enumerate(signals,1)),xy,f'Connector_PinHeader_2.54mm:PinHeader_1x{n:02}_P2.54mm_Vertical',rot,'6130'+str(n).zfill(2)+'11121')

d.section='USB-C and Sequenced Power'
usb={p:'GND' for p in ['A1','A12','B1','B12','SH']}
usb.update({p:'USB_5V' for p in ['A4','A9','B4','B9']})
usb.update({'A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM'})
add('J1','Connector','USB_C_Receptacle_USB2.0_16P','USB4105-GF-A',usb,(7,31.5),'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',source='https://gct.co/connector/usb4105')
r('5.1k','CC1','GND',(2.0,27),90);r('5.1k','CC2','GND',(12.0,27),90)
add('F1','Device','Polyfuse','500mA',{'1':'USB_5V','2':'VUSB'},(3,22),'Fuse:Fuse_1206_3216Metric',90,'1206L050YR')
add('U3','Regulator_Linear','AP2112K-1.2','AP2112K-1.2TRG1',{'1':'VUSB','2':'GND','3':'VUSB','5':'+1V2'},(3.5,5),source='https://www.diodes.com/datasheet/download/AP2112.pdf')
add('U4','Regulator_Linear','AP2112K-3.3','AP2112K-3.3TRG1',{'1':'VUSB','2':'GND','3':'POWER_GOOD','5':'+3V3'},(3.5,12),source='https://www.diodes.com/datasheet/download/AP2112.pdf')
# The fixed 1.12V threshold part uses the generic family symbol.
add('U5','Power_Supervisor','TPS3808DBV','TPS3808G12DBVR',{'1':'POWER_GOOD','2':'GND','3':'VUSB','4':'DELAY','5':'+1V2','6':'VUSB'},(9,4),'Package_TO_SOT_SMD:SOT-23-6',source='https://www.ti.com/lit/ds/symlink/tps3808.pdf')
r('10k','VUSB','POWER_GOOD',(12,3));c('10n','DELAY','GND',(9,7))
for value,a,xy in [('1u','VUSB',(2,2)),('4.7u','+1V2',(5,2)),('1u','VUSB',(2,9)),('4.7u','+3V3',(5,9)),('100n','VUSB',(6,5)),('4.7u','VUSB',(3,18))]:c(value,a,'GND',xy)
add('U6','Power_Protection','TPD2E2U06DCK','TPD2E2U06DCKR',{'1':'USB_DM','2':'USB_DP','3':'GND'},(7,27),'Package_TO_SOT_SMD:SOT-353_SC-70-5',rot=180,source='https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf')
d.note[d.section]='USB-C device / 5V input only; two independent 5.1k CC pull-downs.\nU5 monitors 1.2V with fixed 1.12V threshold before enabling U4 (3.3V).\nNo VIN or externally driven power header. GPIO headers provide 3.3V output only.\nUSB enumeration/suspend current and thermal performance require prototype qualification.'

d.section='USB Programmer and Serial'
ft={str(i):'GND' for i in [1,5,10,11,13,15,25,35,47,51]}
ft.update({str(i):'+3V3' for i in [20,31,42,50,56]})
ft.update({str(i):'FT_1V8' for i in [12,37,49,64]})
ft.update({'2':'XTAL_IN','3':'XTAL_OUT','4':'FT_VPHY','6':'FT_REF','7':'USB_DM','8':'USB_DP','9':'FT_VPLL','14':'FT_RESET_N',
 '16':'FLASH_SCK','17':'FLASH_MOSI','18':'FLASH_MISO','21':'FLASH_CS_N','23':'CDONE','24':'CRESET_N',
 '38':'UART_TO_CPU','39':'UART_FROM_CPU','61':'EE_DATA','62':'EE_CLK','63':'EE_CS'})
add('U2','Interface_USB','FT2232HL','FT2232HL-REEL',ft,(12.5,18),source=FTDI)
add('Y1','Device','Crystal_GND24','12MHz',{'1':'XTAL_IN','2':'GND','3':'XTAL_OUT','4':'GND'},(12.5,9),'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',mpn='ABM8-12.000MHZ-B2-T')
c('27p','XTAL_IN','GND',(10,9),90);c('27p','XTAL_OUT','GND',(15,9),90)
r('12k','FT_REF','GND',(6,15),90);r('10k','+3V3','FT_RESET_N',(6,11),90);c('100n','FT_RESET_N','GND',(8,11),90)
add('FB1','Device','FerriteBead','600R@100MHz',{'1':'+3V3','2':'FT_VPHY'},(6,18),'Inductor_SMD:L_0603_1608Metric',rot=90,mpn='BLM18AG601SN1D')
add('FB2','Device','FerriteBead','600R@100MHz',{'1':'+3V3','2':'FT_VPLL'},(8,24),'Inductor_SMD:L_0603_1608Metric',mpn='BLM18AG601SN1D')
for rail,xy in [('FT_VPHY',(6,20)),('FT_VPLL',(10,24)),('FT_1V8',(17,11)),('FT_1V8',(19,19)),('FT_1V8',(18,24)),('+3V3',(20,14)),('+3V3',(19,22)),('+3V3',(15,25)),('+3V3',(11,25))]:c('100n',rail,'GND',xy)
c('4.7u','FT_1V8','GND',(17,8));c('1u','FT_VPHY','GND',(4,19))
add('U8','Memory_EEPROM','93LCxxB','93LC46BT-I/SN',{'1':'EE_CS','2':'EE_CLK','3':'EE_DATA','4':'EE_DO','5':'GND','8':'+3V3'},(21.5,7),'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',source='https://ww1.microchip.com/downloads/en/DeviceDoc/20001749K.pdf')
r('2.2k','EE_DATA','EE_DO',(19,10));r('10k','+3V3','EE_DATA',(21,11));c('100n','+3V3','GND',(24,11))
d.note[d.section]='FT2232H channel A: MPSSE/iceprog; ADBUS4=CS, ADBUS7=CRESET, ADBUS6=CDONE.\nChannel B: 115200-baud UART (TX -> FPGA RX). Default VID/PID 0403:6010 retained.\n93LC46B is permanently x16. Program descriptors/max current with FT_PROG before normal operation.\nUSB high-speed routing requires 90-ohm differential geometry from the fabricator stackup.'

d.section='TIWARI CPU Fabric'
fp={'1':'+3V3','5':'+1V2','22':'+3V3','24':'+3V3','29':'FPGA_PLL','30':'+1V2','33':'+3V3','49':'GND',
 '7':'CDONE','8':'CRESET_N','14':'FLASH_MOSI','15':'FLASH_SCK','16':'FLASH_CS_N','17':'FLASH_MISO',
 '35':'CLK12','10':'CPU_RESET_N','9':'UART_TO_CPU','6':'UART_FROM_CPU','11':'USER_LED','12':'FAULT_LED','13':'PWM0','18':'PWM1'}
gpio_pins=[2,3,4,44,45,46,47,48,23,25,26,27,28,31,32,34]
fp.update({str(pin):'D'+str(i) for i,pin in enumerate(gpio_pins)})
add('U1','TIWARI','ICE40UP5K-SG48ITR_REVIEWED','ICE40UP5K-SG48ITR',fp,(34,18),fp='TIWARI:UP5K_SG48_Reviewed',source=FPGA)
add('U7','Memory_Flash','W25Q32JVSS','W25Q32JVSSIQ',{'1':'FLASH_CS_N','2':'FLASH_MISO','3':'FLASH_WP_N','4':'GND','5':'FLASH_MOSI','6':'FLASH_SCK','7':'FLASH_HOLD_N','8':'+3V3'},(24.5,24),'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm',source='https://www.winbond.com/resource-files/w25q32jv%20spi%20revg%2003272018%20plus.pdf')
add('Y2','Oscillator','ASE-xxxMHz','12MHz 3V3 CMOS',{'1':'+3V3','2':'GND','3':'CLK12','4':'+3V3'},(28,8),'Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',mpn='ASE-12.000MHZ-LC-T',source='https://abracon.com/Oscillators/ASE.pdf')
c('100n','+3V3','GND',(28,5.5))
r('10k','+3V3','FLASH_WP_N',(26,28));r('10k','+3V3','FLASH_HOLD_N',(29,28))
r('100','+1V2','FPGA_PLL',(34,23.5));c('1u','FPGA_PLL','GND',(36,23.5))
for rail,xy in [('+3V3',(29,14)),('+3V3',(39,18)),('+3V3',(34,13)),('+1V2',(29,18)),('+1V2',(34,22)),('+3V3',(29,24))]:c('100n',rail,'GND',xy)
c('4.7u','+1V2','GND',(38,24));c('4.7u','+3V3','GND',(39,13))
for net,xy in [('CRESET_N',(29,20)),('CDONE',(29,22)),('FLASH_CS_N',(22,28)),('CPU_RESET_N',(41,8))]:r('10k','+3V3',net,xy)
for ref,net,xy in [('SW1','CPU_RESET_N',(44,9)),('SW2','CRESET_N',(44,17))]:
 add(ref,'Switch','SW_Push','CPU RESET' if ref=='SW1' else 'RECONFIGURE',{'1':net,'2':'GND'},xy,'Button_Switch_SMD:SW_Push_1P1T-SH_NO_CK_KMR2xxG',mpn='KMR221GLFS')
# Alternate spelling in KiCad library is resolved below if necessary.
d.note[d.section]='Original TIWARI-8 processor in FPGA; 8-bit A/B datapath and 12-bit instruction PC.\n12MHz external oscillator -> FPGA PLL -> 36MHz CPU target. GPIO is 3.3V only.\nSPI_SO outputs MOSI to flash DI; SPI_SI receives flash DO. CS and CRESET are open-drain from FTDI.\nU1 exposed paddle and every ground via require reliable plane contact. NVCM programming is not supported.'

d.section='Expansion and Indicators'
header('J2',['GND','+3V3']+[f'D{i}' for i in range(8)],(22,32))
header('J3',['GND','+3V3']+[f'D{i}' for i in range(8,16)],(22,3))
header('J4',['GND','PWM0','PWM1','+3V3'],(47,12),0)
header('J5',['GND','FLASH_SCK','FLASH_MOSI','FLASH_MISO','FLASH_CS_N','CRESET_N'],(20,14),0)
# Programming header is fitted only on the back; ordinary use is over USB.
d.parts[-1]['side']='B'
d.parts[-1]['fp']='Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical_SMD_Pin1Left'
for idx,net,xy in [(1,'+3V3',(2,24)),(2,'USER_LED',(44,24)),(3,'FAULT_LED',(44,27))]:
 r('1k',net,'LED'+str(idx)+'_A',(xy[0]-3,xy[1]))
 add('D'+str(idx),'Device','LED',['POWER','USER','FAULT'][idx-1],{'1':'GND','2':'LED'+str(idx)+'_A'},xy,'LED_SMD:LED_0603_1608Metric',mpn='LTST-C190KGKT' if idx!=3 else 'LTST-C190KRKT')
d.note[d.section]='J2: GND,3V3,D0..D7. J3: GND,3V3,D8..D15. J4: GND,PWM0,PWM1,3V3.\nJ5 is a rear service header; do not attach a second SPI host while USB programmer is active.\nGPIO reset state is high impedance. No analog ADC or Arduino shield pin compatibility is provided.\nUse a common ground with external circuits; 3.3V rail on headers is output only.'
# Local decoupling on the back under supply pins, with short plane drops.
local_back={
 'C11':(6.8,15.5,0),'C12':(6.8,18,0),'C13':(6.8,20,0),
 'C14':(17.5,20,0),'C15':(9,12.5,0),'C16':(8.75,23,0),
 'C17':(14,23,0),'C18':(17.5,17,0),'C19':(12.5,12.5,0),
 'C20':(16,12.5,0),'FB1':(4.5,15.5,90),'FB2':(4.5,18,90),
 'R4':(9.5,17,90),'C24':(38,19,0),'C29':(38,16.5,0),
 'C30':(36,23,0)}
for part in d.parts:
 if part['ref'] in local_back:
  x,y,rot=local_back[part['ref']];part.update(xy=(x,y),rot=rot,side='B')
 if part['ref']=='J5':
  part.update(fp='TIWARI:ServicePads_1x06_P1.27',xy=(24,15),value='REAR SERVICE PADS',mpn='PCB_FEATURE')
# Original PCB test pads; this is a board feature, not a guessed IC land pattern.
pretty=ROOT/'libraries/TIWARI.pretty';pretty.mkdir(exist_ok=True)
pads=''.join(f'(pad "{i+1}" smd circle (at 0 {(i-2.5)*1.27}) (size 0.85 0.85) (layers "F.Cu" "F.Mask"))'for i in range(6))
(pretty/'ServicePads_1x06_P1.27.kicad_mod').write_text('(footprint "ServicePads_1x06_P1.27" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd exclude_from_pos_files exclude_from_bom) (fp_rect (start -0.8 -4.1) (end 0.8 4.1) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))'+pads+')')
(ROOT/'fp-lib-table').write_text('(fp_lib_table (lib (name "TIWARI") (type "KiCad") (uri "${KIPRJMOD}/libraries/TIWARI.pretty") (options "") (descr "Original rear service test pads")))\n')
d.save();d.schematic()
print(f'Wrote {len(d.parts)} components')
