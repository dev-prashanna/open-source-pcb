"""RoveCore One A.0: original electrical design; all connectivity explicit."""
from cadlib import *
import pcbnew as p
LIB=ROOT/'libraries';LIB.mkdir(exist_ok=True)
(LIB/'RoveCore.pretty').mkdir(exist_ok=True)
# Datasheet-derived ambient sensor, absent from the installed symbol library.
als=[S('symbol'),'VEML7700',[S('pin_names'),[S('offset'),.5]],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],prop('Reference','U',0,8),prop('Value','VEML7700',0,6),prop('Footprint','RoveCore:VEML7700_TT',0,0,True)]
body=[S('symbol'),'VEML7700_0_1',[S('rectangle'),[S('start'),-7.62,5.08],[S('end'),7.62,-5.08],[S('stroke'),[S('width'),.254],[S('type'),S('default')]],[S('fill'),[S('type'),S('background')]]]]
als.append(body);b=[S('symbol'),'VEML7700_1_1']
for num,name,typ,x,y,a in [('1','SCL','input',-10.16,2.54,0),('2','VDD','power_in',0,7.62,270),('3','GND','power_in',0,-7.62,90),('4','SDA','bidirectional',-10.16,-2.54,0)]:
 b.append([S('pin'),S(typ),S('line'),[S('at'),x,y,a],[S('length'),2.54],[S('name'),name,eff()],[S('number'),num,eff()]])
als.append(b)
(LIB/'RoveCore.kicad_sym').write_text(sx.dumps([S('kicad_symbol_lib'),[S('version'),20250114],[S('generator'),'kicad_symbol_editor'],als]))
# VEML7700-TT top-view package. Vishay 84286 Rev1.8 page10: 1.27 pitch,
# 0.7 x 1.6 pads, body 6.8 x 2.35. Optical aperture points out of top face.
fp=p.FOOTPRINT(None);fp.SetReference('REF**');fp.SetValue('VEML7700-TT');fp.SetAttributes(p.FP_SMD)
for i in range(4):
 pad=p.PAD(fp);pad.SetNumber(str(i+1));pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_RECT);pad.SetSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(1.6)));pad.SetPosition(p.VECTOR2I(p.FromMM((i-1.5)*1.27),0));pad.SetLayerSet(p.LSET.FrontMask());fp.Add(pad)
for layer,box in [(p.F_Fab,(-3.4,-1.175,3.4,1.175)),(p.F_CrtYd,(-3.65,-1.425,3.65,1.425))]:
 x0,y0,x1,y1=box
 for a,z in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
  s=p.PCB_SHAPE(fp);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));s.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));s.SetLayer(layer);s.SetWidth(p.FromMM(.05));fp.Add(s)
fp.SetFPID(p.LIB_ID('RoveCore','VEML7700_TT'))
(LIB/'RoveCore.pretty'/'VEML7700_TT.kicad_mod').write_text('''(footprint "VEML7700_TT" (version 20250108) (generator pcbnew) (layer "F.Cu") (attr smd)
 (property "Reference" "REF**" (at 0 -2) (layer "F.SilkS") (effects(font(size 0.8 0.8))))
 (property "Value" "VEML7700-TT" (at 0 2) (layer "F.Fab") (effects(font(size 0.8 0.8))))
 (fp_rect (start -3.4 -1.175)(end 3.4 1.175)(stroke(width 0.1)(type default))(fill none)(layer "F.Fab"))
 (fp_rect (start -3.65 -1.425)(end 3.65 1.425)(stroke(width 0.05)(type default))(fill none)(layer "F.CrtYd"))
 (pad "1" smd rect (at -1.905 0)(size 0.7 1.6)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "2" smd rect (at -0.635 0)(size 0.7 1.6)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "3" smd rect (at 0.635 0)(size 0.7 1.6)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "4" smd rect (at 1.905 0)(size 0.7 1.6)(layers "F.Cu" "F.Paste" "F.Mask")))''')
(ROOT/'sym-lib-table').write_text('(sym_lib_table\n (version 7)\n (lib (name "RoveCore") (type "KiCad") (uri "${KIPRJMOD}/libraries/RoveCore.kicad_sym") (options "") (descr "Vishay datasheet-derived ambient sensor"))\n)\n')
(ROOT/'fp-lib-table').write_text('(fp_lib_table\n (version 7)\n (lib (name "RoveCore") (type "KiCad") (uri "${KIPRJMOD}/libraries/RoveCore.pretty") (options "") (descr "Project-local footprints"))\n)\n')
d=Design()
sources=json.loads((ROOT/'datasheets/sources.json').read_text())
def ic(ref,lib,name,value,nets,xy,key='',fp=None,rot=0):
 d.parent=None;d.add(lib,name,value,nets,fp,xy,rot,ref,value,source=sources.get(key,''));d.parent=ref
def dec(rail='+3V3',n=1):
 for _ in range(n):d.c('100nF 16V',rail,'GND')
def bulk(value,rail):d.add('Device','C_Polarized',value,{1:rail,2:'GND'},'Capacitor_SMD:CP_Elec_8x10.5',mpn='EEE-FK1C471P',mfr='Panasonic')
def schottky(ref,a,k,xy=None,mpn='SS34'):
 d.add('Device','D_Schottky',mpn,{'1':k,'2':a},'Diode_SMD:D_SMA',xy,ref=ref,mpn=mpn,mfr='Diodes Inc.')
def pfet(ref,raw,out):
 ic(ref,'Transistor_FET','AO3401A','AO3401A',{'1':ref+'_G','2':out,'3':raw},None)
 d.r('100k',ref+'_G','GND')
def fuse(ref,a,b,val='2A hold'):
 d.add('Device','Polyfuse',val,{'1':a,'2':b},'Fuse:Fuse_1812_4532Metric',ref=ref,mpn='1812L200/16DR',mfr='Littelfuse')

d.section='Controller'
gpio={36:'ENC_LA',39:'ENC_LB',34:'ENC_RA',35:'ENC_RB',32:'IMU_INT',33:'BAT_ADC',25:'M_A1',26:'M_A2',27:'M_B1',14:'M_B2',12:'STRAP12',13:'US_ECHO',15:'SERVO_OE',2:'BUZZ_PWM',0:'BOOT',4:'US_TRIG',16:'UART_RX',17:'UART_TX',5:'SPI_CS',18:'SPI_SCK',19:'SPI_MISO',21:'I2C_SDA',22:'I2C_SCL',23:'SPI_MOSI',1:'U0_TX',3:'U0_RX'}
mp=pinmap('RF_Module','ESP32-WROOM-32E');nets={'2':'+3V3','3':'EN','[1,15,38,39]':'GND'}
for n,label in mp.items():
 if label.startswith('IO') and label[2:].isdigit():nets[n]=gpio[int(label[2:])]
nets.update({'4':'ENC_LA','5':'ENC_LB','34':'U0_RX','35':'U0_TX'})
ic('U1','RF_Module','ESP32-WROOM-32E','ESP32-WROOM-32E-N8',nets,(22,7),'esp32')
dec();d.c('22uF 10V','+3V3','GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61A226ME44L')
d.r('10k','+3V3','EN');d.c('1uF 16V','EN','GND');d.r('10k','+3V3','BOOT')
d.r('10k','STRAP12','GND');d.r('10k','+3V3','SPI_CS');d.r('10k','+3V3','SERVO_OE');d.r('100k','BUZZ_PWM','GND')
d.switch('SW1','EN','GND',(7,24));d.switch('SW2','BOOT','GND',(7,29))
d.conn('J1',['GND','+3V3','U0_TX','U0_RX','EN','BOOT'],'SERVICE 3V3',(4,34),'header')
d.note[d.section]='ESP32-WROOM-32E-N8: 8 MB flash; no PSRAM; USB bridge required.\nGPIO34/35/36/39 input only. GPIO12 held LOW for 3.3V flash. Boot: hold BOOT, tap RESET.\nAll allocated GPIO are accessible at headers/test pads; shared signals are not free outputs.'

d.section='USB Programming'
usb={'A1':'GND','A4':'USB_VBUS','A5':'CC1','A6':'USB_DP','A7':'USB_DM','A9':'USB_VBUS','A12':'GND','B1':'GND','B4':'USB_VBUS','B5':'CC2','B6':'USB_DP','B7':'USB_DM','B9':'USB_VBUS','B12':'GND','SH':'GND'}
ic('J2','Connector','USB_C_Receptacle_USB2.0_16P','USB-C 5V DATA',usb,(9,43),fp='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',rot=270)
d.r('5.1k','CC1','GND');d.r('5.1k','CC2','GND');d.c('1uF 16V','USB_VBUS','GND')
ic('U2','Interface_USB','CP2102N-Axx-xQFN24','CP2102N-A02-GQFN24',{'2':'GND','3':'USB_DP','4':'USB_DM','5':'+3V3','6':'+3V3','7':'+3V3','8':'VBUS_SENSE','9':'USB_RST','19':'RTS','20':'U0_TX','21':'U0_RX','23':'DTR','25':'GND'},(19,43),'usb')
dec(n=2);d.c('4.7uF 10V','+3V3','GND');d.r('1k','+3V3','USB_RST');d.r('22.1k','USB_VBUS','VBUS_SENSE');d.r('47.5k','VBUS_SENSE','GND')
ic('U3','Power_Protection','USBLC6-2SC6','USBLC6-2SC6',{'1':'USB_DP','6':'USB_DP','3':'USB_DM','4':'USB_DM','2':'GND','5':'USB_VBUS'},(13,43))
# Espressif crossed two-NPN automatic programming circuit.
ic('Q1','Transistor_BJT','MMBT3904','MMBT3904',{'1':'AUTO_EN_B','2':'RTS','3':'EN'},None)
d.r('10k','DTR','AUTO_EN_B')
ic('Q2','Transistor_BJT','MMBT3904','MMBT3904',{'1':'AUTO_BOOT_B','2':'DTR','3':'BOOT'},None)
d.r('10k','RTS','AUTO_BOOT_B')
d.note[d.section]='Self-powered CP2102N: VREGIN, VDD and VIO tied to 3V3 per Silicon Labs.\nVBUS sensing uses 22.1k / 47.5k divider. Dual 5.1k CC pulldowns: 5V sink, no PD.\nUSB supplies LOGIC ONLY. Firmware must respect the host current entitlement.'

d.section='Power Inputs'
d.parent=None
d.conn('J3',['BAT_RAW','GND'],'2S BAT 6.4-8.4V',(10,60),'term')
fuse('F1','BAT_RAW','BAT_FUSED');pfet('Q3','BAT_FUSED','VBAT')
bulk('470uF 16V','VBAT');dec('VBAT')
d.conn('J4',['EXT5_RAW','GND'],'EXT 5V LOGIC',(22,60),'term');fuse('F2','EXT5_RAW','EXT5_FUSED','1.1A hold')
fuse('F3','USB_VBUS','USB_FUSED','0.5A hold')
schottky('D1','EXT5_FUSED','LOGIC5');schottky('D2','USB_FUSED','LOGIC5');schottky('D3','BAT5','LOGIC5')
d.c('22uF 10V','LOGIC5','GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61A226ME44L')
# Only diode cathodes are common: sources cannot feed one another.
d.r('100k','VBAT','BAT_DIV');d.r('33k','BAT_DIV','GND');d.r('1k','BAT_DIV','BAT_ADC');d.c('100nF 16V','BAT_ADC','GND')
d.note[d.section]='2S pack MUST include cell-level protection, overcurrent cutoff and balancing.\nNO onboard charger: disconnect pack and charge with a proper 2S balance charger.\nSchottky source OR prevents backfeeding USB/external/battery logic sources. Common ground.'

d.section='Logic Regulators'
for ref,part,vi,vo,sw,xy,L in [('U4','AP63205WU','VBAT','BAT5','SW_BAT',(31,54),'4.7uH'),('U5','AP63203WU','LOGIC5','+3V3','SW_3V3',(27,42),'4.7uH')]:
 ic(ref,'Regulator_Switching',part,part+'-7',{'1':vo,'2':ref+'_EN','3':vi,'4':'GND','5':sw,'6':ref+'_BST'},xy,'buck')
 d.r('100k',vi,ref+'_EN');d.r('27.4k' if ref=='U4' else '100k',ref+'_EN','GND')
 d.c('100nF 16V',ref+'_BST',sw)
 d.c('10uF 16V',vi,'GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61C106KE15L');dec(vi)
 d.add('Device','L',L,{1:sw,2:vo},'Inductor_SMD:L_Bourns_SRP5030T',mpn='SRP5030T-4R7M',mfr='Bourns')
 for _ in range(2):d.c('22uF 10V',vo,'GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61A226ME44L')
d.parent='U5';d.add('Device','FerriteBead','600R @100MHz',{1:'+3V3',2:'+3V3_SENS'},'Inductor_SMD:L_0603_1608Metric',ref='FB1',mpn='BLM18AG601SN1D',mfr='Murata')
d.c('4.7uF 10V','+3V3_SENS','GND');dec('+3V3_SENS')
d.r('2.2k','+3V3','I2C_SDA');d.r('2.2k','+3V3','I2C_SCL')
d.note[d.section]='AP63205 battery buck 5V; AP63203 logic buck 3V3. Feedback on output side of inductors.\nBattery EN divider 100k/27.4k: nominal rising UVLO about 5.6V, NOT cell protection.\n3V3 target 1A total, sensor/expansion budget 150mA. Quiet sensor branch uses ferrite + local caps.'

d.section='Servo Power'
ic('U6','Regulator_Switching','TPS54302','TPS54302DDCR',{'1':'GND','2':'SW_SERVO','3':'VBAT','4':'SERVO_FB','5':'SERVO_EN','6':'SERVO_BOOT'},(45,54),'servo_buck')
d.r('100k','VBAT','SERVO_EN');d.r('27.4k','SERVO_EN','GND');d.c('100nF 16V','SERVO_BOOT','SW_SERVO')
for _ in range(2):d.c('10uF 16V','VBAT','GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61C106KE15L')
d.add('Device','L','10uH',{1:'SW_SERVO',2:'SERVO_BUCK'},'Inductor_SMD:L_Bourns_SRP5030T',mpn='SRP5030T-100M',mfr='Bourns')
d.r('100k','SERVO_BUCK','SERVO_FB');d.r('13.3k','SERVO_FB','GND');d.c('75pF 50V','SERVO_BUCK','SERVO_FB')
for _ in range(2):d.c('22uF 10V','SERVO_BUCK','GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61A226ME44L')
d.conn('J5',['SERVO_EXT_RAW','GND'],'SERVO EXT 5-6V',(35,60),'term');pfet('Q4','SERVO_EXT_RAW','SERVO_EXT')
d.conn('JP1',['SERVO_BUCK','SERVO_SELECTED','SERVO_EXT'],'SERVO SELECT 1-2 BAT / 2-3 EXT',(48,59),'servo',90)
fuse('F4','SERVO_SELECTED','SERVO5');bulk('470uF 16V','SERVO5')
d.note[d.section]='Servo source selector: fit ONE shunt only. Never bridge both supplies.\nTPS54302 nominal Vout = 0.596*(1+100/13.3) = 5.077V. 10uH, 44uF ceramic, 75pF feedforward.\nServo recommendation: 2A total continuous, 3A brief peak ONLY after thermal validation. Four small servos, not four stall currents.'

d.section='Motor Driver'
d.conn('J6',['MOTOR_RAW','GND'],'VM 3-8.4V',(59,60),'term');fuse('F5','MOTOR_RAW','MOTOR_FUSED');pfet('Q5','MOTOR_FUSED','VM')
ic('U7','Driver_Motor','DRV8833PWP','DRV8833PWPR',{'1':'M_SLEEP','2':'MOTOR_A_P','3':'ISENSE_A','4':'MOTOR_A_N','5':'MOTOR_B_N','6':'ISENSE_B','7':'MOTOR_B_P','8':'M_FAULT','9':'M_B1','10':'M_B2','11':'M_VCP','12':'VM','13':'GND','14':'M_VINT','15':'M_A2','16':'M_A1','17':'GND'},(66,48),'motor')
d.c('10nF 25V','M_VCP','VM');d.c('2.2uF 10V','M_VINT','GND');dec('VM');d.c('10uF 16V','VM','GND',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR61C106KE15L');bulk('470uF 16V','VM')
for n in ['ISENSE_A','ISENSE_B']:d.add('Device','R','0.25R 1W',{1:n,2:'GND'},'Resistor_SMD:R_2512_6332Metric',mpn='WSL2512R2500FEA',mfr='Vishay')
d.r('100k','M_SLEEP','GND');d.r('10k','+3V3','M_FAULT')
for n in ['M_A1','M_A2','M_B1','M_B2']:d.r('100k',n,'GND')
d.conn('J7',['MOTOR_A_P','MOTOR_A_N'],'MOTOR A',(76,43),'term',90);d.conn('J8',['MOTOR_B_P','MOTOR_B_N'],'MOTOR B',(76,54),'term',90)
d.note[d.section]='DRV8833PWPR (PowerPAD), not uncooled PW. Rsense=0.25ohm => Itrip typ 0.8A.\nRecommend <=0.6A continuous each; 3-8.4V motor input. Limit is per bridge, not advertised 2A.\nRegenerative braking raises VM; use a sink-capable battery supply. Validate VM stays <10.8V in operation, <12V absolute.\nFit 100nF directly at brushed motor terminals; keep twisted motor leads short.'

d.section='Motion Sensors'
ic('U8','Sensor_Motion','LSM6DS3','LSM6DS3TR-C',{'1':'GND','4':'IMU_INT','5':'+3V3_SENS','6':'GND','7':'GND','8':'+3V3_SENS','12':'+3V3_SENS','13':'I2C_SCL','14':'I2C_SDA'},(40,29),'imu')
dec('+3V3_SENS',2);d.c('1uF 16V','+3V3_SENS','GND')
ic('U9','Sensor_Magnetic','LIS3MDL','LIS3MDLTR',{'1':'I2C_SCL','2':'GND','3':'GND','4':'MAG_C1','5':'+3V3_SENS','6':'+3V3_SENS','9':'GND','10':'+3V3_SENS','11':'I2C_SDA','12':'GND'},(69,9),'mag')
dec('+3V3_SENS',2);d.c('100nF 16V','MAG_C1','GND');d.c('4.7uF 10V','+3V3_SENS','GND')
d.note[d.section]='LSM6DS3TR-C uses installed LSM6DS3 symbol: identical 14-pin mapping, 3x2.5mm LGA footprint.\nIMU I2C 0x6A (SA0=0), INT1 direct GPIO32. Magnetometer I2C 0x1C (SA1=0).\nLIS3MDL reserved pins 2/12 grounded; C1 100nF. IMU SDx/SCx/INT2 intentionally unused.\nCalibrate accelerometer, gyro bias and compass hard/soft iron in the assembled chassis.'

d.section='Environmental Sensors'
ic('U10','Sensor','BME280','BME280',{'1':'GND','2':'+3V3_SENS','3':'I2C_SDA','4':'I2C_SCL','5':'GND','6':'+3V3_SENS','7':'GND','8':'+3V3_SENS'},(59,9),'bme')
dec('+3V3_SENS',2)
ic('U11','RoveCore','VEML7700','VEML7700-TT',{'1':'I2C_SCL','2':'+3V3_SENS','3':'GND','4':'I2C_SDA'},(49,6),'als');dec('+3V3_SENS')
d.note[d.section]='BME280 I2C 0x76; CSB=VDDIO, SDO=GND. VEML7700 fixed 0x10.\nKeep optical/pressure openings clear. Do not wash MEMS/optical sensors without supplier approval.\nBME temperature includes PCB self-heating; characterize board-on offsets under Wi-Fi/motor load.'

d.section='Distance Interfaces'
ic('U12','Sensor_Distance','VL53L1CXV0FY1','VL53L1CXV0FY1',{'1':'+3V3_SENS','2':'GND','3':'GND','4':'GND','5':'TOF_XSHUT','6':'GND','7':'TOF_INT','9':'I2C_SDA','10':'I2C_SCL','11':'+3V3_SENS','12':'GND'},(40,5),'tof')
dec('+3V3_SENS',2);d.c('4.7uF 10V','+3V3_SENS','GND');d.r('10k','+3V3_SENS','TOF_XSHUT');d.r('10k','+3V3_SENS','TOF_INT')
d.conn('J9',['BAT5','US_TRIG5','US_ECHO_RAW','GND'],'ULTRASONIC 5V',(73,24),'gh',90)
ic('U13','74xGxx','74LVC1G17','SN74LVC1G17DBVR',{'2':'US_ECHO_RC','3':'GND','4':'US_ECHO','5':'+3V3'},(66,25),'buffer',fp='Package_TO_SOT_SMD:SOT-23-5');dec()
d.r('1k','US_ECHO_RAW','US_ECHO_RC');d.r('100k','US_ECHO_RC','GND');d.c('100pF 50V','US_ECHO_RC','GND')
# A 5V AHCT buffer guarantees 5V TRIG and servo logic from 3V3 PWM.
ic('U14','74xx','74AHCT125','SN74AHCT125PWR',{'1':'GND','2':'US_TRIG','3':'US_TRIG5','4':'SERVO_OE','5':'SERVO_PWM0','6':'SERVO_SIG0','7':'GND','8':'SERVO_SIG1','9':'SERVO_PWM1','10':'SERVO_OE','11':'SERVO_SIG2','12':'SERVO_PWM2','13':'SERVO_OE','14':'BAT5'},(61,31),'upbuffer',fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm');dec('BAT5')
d.note[d.section]='VL53L1X at 0x29: AVDD=3V3_SENS; program 2V8 IO mode with ST driver.\nXSHUT open-drain control only. DNC pin8 intentionally open. Aperture faces upward: mount board to suit sensing direction.\nUltrasonic VCC is battery-derived BAT5: USB-only operation does not power 5V accessories.\nEcho uses 5.5V-tolerant SN74LVC1G17 input; no direct 5V enters ESP32.'

d.section='Encoder Interfaces'
for idx,xy,labels,raws in [(0,(72,33),['ENC_LA','ENC_LB'],['ENC_LA_RAW','ENC_LB_RAW']),(1,(72,38),['ENC_RA','ENC_RB'],['ENC_RA_RAW','ENC_RB_RAW'])]:
 d.conn('J'+str(10+idx),['+3V3','GND',*raws],'ENC '+('LEFT' if idx==0 else 'RIGHT'),xy,'gh',90)
 for j,(net,raw) in enumerate(zip(labels,raws)):
  ref='U'+str(15+idx*2+j)
  ic(ref,'74xGxx','74LVC1G17','SN74LVC1G17DBVR',{'2':raw+'_RC','3':'GND','4':net,'5':'+3V3'},(64+idx*5,35+j*5),'buffer',fp='Package_TO_SOT_SMD:SOT-23-5');dec()
  d.r('1k',raw,raw+'_RC');d.r('10k','+3V3',raw);d.c('100pF 50V',raw+'_RC','GND')
d.note[d.section]='Encoder connectors supply 3V3; push-pull or open-collector inputs accepted.\nA/B inputs buffer-rated 0-5.5V, with 1k/100pF RC (~100ns) and 10k pullups.\nGPIO36/39 left, GPIO34/35 right. Use ESP32 PCNT; no reliance on missing internal pullups.\nExternal 5V encoder supply allowed only with shared ground and no tie to connector 3V3.'

d.section='Servo PWM'
ic('U19','Driver_LED','PCA9685PW','PCA9685PW,118',{'1':'GND','2':'GND','3':'GND','4':'GND','5':'GND','6':'SERVO_PWM0','7':'SERVO_PWM1','8':'SERVO_PWM2','9':'SERVO_PWM3','14':'GND','23':'SERVO_OE','24':'GND','25':'GND','26':'I2C_SCL','27':'I2C_SDA','28':'+3V3'},(50,38),'pwm');dec()
ic('U20','74xGxx','74LVC1G17','SN74AHCT1G125DBVR',{'2':'SERVO_PWM3','3':'GND','4':'SERVO_SIG3','5':'BAT5'},(54,45),'upbuffer',fp='Package_TO_SOT_SMD:SOT-23-5')
# Replace the single gate with real 74AHCT1G125 symbol (OE pin1).
d.parts[-1]['lib']='74xGxx';d.parts[-1]['name']='74AHCT1G125';d.parts[-1]['nets']['1']='SERVO_OE';dec('BAT5')
for i in range(4):
 d.r('220','SERVO_SIG'+str(i),'SERVO_OUT'+str(i));d.r('100k','SERVO_OUT'+str(i),'GND')
 d.conn('J'+str(12+i),['GND','SERVO5','SERVO_OUT'+str(i)],'SERVO '+str(i+1),(54+i*5.5,17),'servo')
d.note[d.section]='PCA9685 0x40; default all-call 0x70, disable if conflicting extension is installed.\nGPIO15 high disables AHCT output buffers and PCA9685. Set low only after setting valid 50Hz pulses.\nEach servo: GND / servo rail / 5V PWM. Servo supply and BAT5 logic are distinct.\nUnused PWM channels intentionally NC; shared PWM frequency must be respected.'

d.section='GPIO Expansion'
exp={1:'EXP_B0',2:'EXP_B1',3:'EXP_B2',4:'EXP_B3',5:'EXP_B4',6:'EXP_B5',7:'EXP_B6',8:'EXP_B7',9:'+3V3',10:'GND',12:'I2C_SCL',13:'I2C_SDA',15:'GND',16:'GND',17:'GND',18:'EN',21:'M_SLEEP',22:'M_FAULT',23:'TOF_XSHUT',24:'TOF_INT',25:'USER_BTN',26:'RGB_R',27:'RGB_G',28:'RGB_B'}
ic('U21','Interface_Expansion','MCP23017x-x-SS','MCP23017-E/SS',exp,(43,43));dec()
d.conn('J16',['+3V3','GND','I2C_SDA','I2C_SCL'],'I2C 3V3',(43,14),'gh',180)
d.conn('J17',['GND','+3V3','SPI_SCK','SPI_MOSI','SPI_MISO','SPI_CS'],'SPI / LORA',(39,22),'gh')
d.conn('J18',['GND','+3V3','UART_TX','UART_RX'],'GPS / UART',(58,24),'gh')
d.conn('J19',['GND','+3V3','GND','GND','GND',*[f'EXP_B{i}' for i in range(3,8)]],'GPIO EXP 3V3',(77,7),'header')
for ref,net,xy in [('TP1','EXP_B0',(40.2806,39.0703)),('TP2','EXP_B1',(39.4113,39.4811)),('TP3','EXP_B2',(39.377,40.2551))]:
 d.add('Connector','TestPoint',net,{'1':net},'RoveCore:ServicePad_0.5mm',xy,ref=ref,mpn='PCB copper feature',mfr='PCB fabricator',side='B')
# Shared test/header access to every practical controller pin; GPIO12 is reserved.
d.conn('J20',['GND','+3V3','M_A1','M_A2','M_B1','M_B2','IMU_INT','BAT_ADC','US_TRIG','US_ECHO'],'ESP GPIO SHARED',(6,7),'header')
d.conn('J21',['GND','SERVO_OE','BUZZ_PWM','ENC_LA','ENC_LB','ENC_RA','ENC_RB','SPI_CS'],'ESP GPIO INPUTS',(35,8),'header')
d.note[d.section]='MCP23017 fixed 0x20. GPA0 sleep defaults LOW by external resistor; all pins reset as inputs.\nGPA2 must be open-drain emulated: output LOW for shutdown, input for release; never drive HIGH.\nGPB0..7 expansion are 3V3 GPIO; GPB7 also drives onboard load MOSFET.\nGPIO headers expose SHARED nets: disable corresponding onboard function before reuse. GPIO12 not general expansion.'

d.section='Analog Expansion'
ic('U22','Analog_ADC','ADS1115IDGS','ADS1115IDGSR',{'1':'GND','3':'GND','4':'AN0','5':'AN1','6':'AN2','7':'AN3','8':'+3V3_SENS','9':'I2C_SDA','10':'I2C_SCL'},(48,28),'adc');dec('+3V3_SENS')
for i in range(4):
 d.r('4.7k','AN_IN'+str(i),'AN'+str(i));d.c('10nF 25V','AN'+str(i),'GND')
 # BAT54S dual series diode clamps at ground and sensor rail.
 d.add('Diode','BAT54S','BAT54S',{'1':'GND','2':'+3V3_SENS','3':'AN'+str(i)},ref='D'+str(10+i),mpn='BAT54S-7-F',mfr='Diodes Inc.')
d.conn('J22',['+3V3','GND','AN_IN0','AN_IN1','AN_IN2','AN_IN3'],'ANALOG 0-3V3',(59,5),'gh',180)
d.note[d.section]='ADS1115 address 0x48, 860 samples/s aggregate maximum. Choose PGA +/-4.096V.\nInput voltage range remains 0..3.3V; PGA range is NOT input tolerance. 4.7k / 10nF filtering with Schottky clamps.\nSuitable for analog line sensor array. 4 channels sequentially sampled; high-speed line control may need an external ADC.'

d.section='User Interface'
d.parent=None;d.switch('SW3','USER_BTN','GND',(7,18));d.r('10k','+3V3','USER_BTN');d.c('100nF 16V','USER_BTN','GND')
d.r('1k','+3V3','POWER_LED');d.led('D4','POWER_LED','GND',(14,26))
for i,color in enumerate(['R','G','B']):
 d.r('1k','+3V3','LED_'+color);d.led('D'+str(5+i),'LED_'+color,'RGB_'+color,(14+i*3,30))
 d.parts[-1]['value']={'R':'RED','G':'GREEN','B':'BLUE'}[color];d.parts[-1]['mpn']={'R':'LTST-C190KRKT','G':'LTST-C190KGKT','B':'LTST-C193TBKT-5A'}[color]
# Separate R/G/B indicators avoid addressable-LED level and idle-power complications.
ic('Q6','Transistor_FET','AO3400A','AO3400A',{'1':'BUZZ_GATE','2':'GND','3':'BUZZ_LOW'},(23,29));d.r('100','BUZZ_PWM','BUZZ_GATE');d.r('100k','BUZZ_GATE','GND')
d.add('Device','Buzzer','PKLCS1212E4001-R1',{'1':'+3V3','2':'BUZZ_LOW'},'Buzzer_Beeper:Buzzer_Murata_PKLCS1212E',xy=(25,32),ref='BZ1',mpn='PKLCS1212E4001-R1',mfr='Murata');d.r('1k','+3V3','BUZZ_LOW')
ic('Q7','Transistor_FET','AO3400A','AO3400A',{'1':'LOAD_GATE','2':'GND','3':'LOAD_LOW'},(59,42));d.r('100','EXP_B7','LOAD_GATE');d.r('100k','LOAD_GATE','GND');schottky('D8','LOAD_LOW','BAT5')
d.conn('J23',['BAT5','LOAD_LOW'],'LOAD 5V 0.25A',(64,39),'gh')
d.note[d.section]='R/G/B discrete programmable LEDs on expander GPA5..7; use green for Wi-Fi status.\nPiezo buzzer via GPIO2 MOSFET and discharge resistor. User button active LOW on GPA4.\nGPB7 load output 5V/250mA max, diode-protected for small inductive loads. BAT5 accessory budget shared.\nCAN: external 3V3 transceiver may reuse UART16/17 as TWAI RX/TX; GPS/UART then unavailable.'

# Correct exact orderable passive MPNs; capacitor voltage/value maps prevent placeholders.
capmp={'100nF 16V':'GRM188R71C104KA01D','1uF 16V':'GRM188R61C105KA12D','4.7uF 10V':'GRM188R61A475KE15D','10nF 25V':'GRM188R71E103KA01D','2.2uF 10V':'GRM188R61A225KE34D','100pF 50V':'GRM1885C1H101JA01D','75pF 50V':'GRM1885C1H750JA01D'}
for c in d.parts:
 makers={'U1':'Espressif','U2':'Silicon Labs','U3':'STMicroelectronics','U4':'Diodes Inc.','U5':'Diodes Inc.','U6':'Texas Instruments','U7':'Texas Instruments','U8':'STMicroelectronics','U9':'STMicroelectronics','U10':'Bosch Sensortec','U11':'Vishay','U12':'STMicroelectronics','U14':'Texas Instruments','U19':'NXP','U20':'Texas Instruments','U21':'Microchip','U22':'Texas Instruments'}
 if not c['mfr']:c['mfr']=makers.get(c['ref'],'Texas Instruments' if c['name']=='74LVC1G17' else 'onsemi' if c['name']=='MMBT3904' else 'Alpha & Omega Semiconductor' if c['name'] in ['AO3401A','AO3400A'] else 'Murata' if c['name']=='C' else '')
 if c['ref']=='J2':c['mpn']='TYPE-C-31-M-12';c['mfr']='HRO'
 if c['ref']=='U21':c['source']='https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf'
 if c['value'] in capmp:c['mpn']=capmp[c['value']];c['mfr']='Murata'
 if c['name']=='R' and c['value']!='0.25R 1W':
  v=c['value'].lower();tail=''
  for suffix,letter in [('k','K'),('m','M')]:
   if v.endswith(suffix):
    a=v[:-1].split('.');tail=a[0]+letter+(a[1] if len(a)>1 else '');break
  else:tail=v.replace('.','R')+('R' if '.' not in v else '')
  c['mpn']='RC0603FR-07'+tail+'L';c['mfr']='Yageo'
 if c['ref']=='F2':c['mpn']='1812L110/16DR'
 if c['ref']=='F3':c['mpn']='1812L050/24DR'
 if c['ref']=='U20':c['source']='https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf'
 if c['ref'] in ['Q3','Q4','Q5']:c['source']='https://www.aosmd.com/sites/default/files/res/datasheets/AO3401A.pdf'
# Save MCP seed once, never overwrite the edited project as the seed on regeneration.
seed=ROOT/'mcp_seed.kicad_sch'
if not seed.exists():seed.write_text((ROOT/'RoveCore_One.kicad_sch').read_text())
d.schematic();d.save()
print('Built electrical manifest and hierarchical schematic:',len(d.parts),'parts')
