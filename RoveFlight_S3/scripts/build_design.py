"""Original RF-S3-A0 design: explicit, datasheet-checked pin-to-net manifest."""
from cadlib import *
LIB=ROOT/'libraries';LIB.mkdir(exist_ok=True);(LIB/'RoveFlight.pretty').mkdir(exist_ok=True)
custom=[]
def block(name,fp,definitions):
 sym=[S('symbol'),name,[S('pin_names'),[S('offset'),.5]],[S('in_bom'),S('yes')],[S('on_board'),S('yes')],prop('Reference','U',0,15),prop('Value',name,0,12),prop('Footprint',fp,0,0,True)]
 h=max(7.62,math.ceil(len(definitions)/2)*2.54/2+2.54)
 sym.append([S('symbol'),name+'_0_1',[S('rectangle'),[S('start'),-10.16,h],[S('end'),10.16,-h],[S('stroke'),[S('width'),.254],[S('type'),S('default')]],[S('fill'),[S('type'),S('background')]]]])
 b=[S('symbol'),name+'_1_1'];half=math.ceil(len(definitions)/2)
 for i,(num,pname,typ) in enumerate(definitions):
  left=i<half;j=i if left else i-half;y=(half-1)*1.27-j*2.54
  b.append([S('pin'),S(typ),S('line'),[S('at'),-12.7 if left else 12.7,y,0 if left else 180],[S('length'),2.54],[S('name'),pname,eff(.85)],[S('number'),str(num),eff(.85)]])
 sym.append(b);custom.append(sym)
block('BMI270','Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm',[(1,'SDO','tri_state'),(2,'ASDX','bidirectional'),(3,'ASCX','bidirectional'),(4,'INT1','output'),(5,'VDDIO','power_in'),(6,'GNDIO','power_in'),(7,'GND','power_in'),(8,'VDD','power_in'),(9,'INT2','output'),(10,'OCSB','input'),(11,'OSDO','output'),(12,'CSB','input'),(13,'SCK','input'),(14,'SDI','input')])
block('BMP390','RoveFlight:BMP390_LGA10',[(1,'VDDIO','power_in'),(2,'SCK','input'),(3,'GND','power_in'),(4,'SDI','input'),(5,'SDO','tri_state'),(6,'CSB','input'),(7,'INT','output'),(8,'GND','power_in'),(9,'GND','power_in'),(10,'VDD','power_in')])
block('TPS3431','Package_DFN_QFN:Texas_DRB0008A',[(1,'VDD','power_in'),(2,'CWD','passive'),(3,'EN','input'),(4,'GND','power_in'),(5,'SET1','input'),(6,'WDI','input'),(7,'WDO_N','open_collector'),(8,'ENOUT','open_collector'),(9,'EP','power_in')])
block('SN74LVC1G74','Package_SO:VSSOP-8_2.3x2mm_P0.5mm',[(1,'CLK','input'),(2,'D','input'),(3,'Q_N','output'),(4,'GND','power_in'),(5,'Q','output'),(6,'CLR_N','input'),(7,'PRE_N','input'),(8,'VCC','power_in')])
block('DMP2008UFG','Package_SON:Diodes_PowerDI3333-8',[(1,'S','passive'),(2,'S','passive'),(3,'S','passive'),(4,'G','input'),(5,'D','passive')])
block('TSOP75438TT','RoveFlight:TSOP75438TT',[(1,'GND','power_in'),(2,'VS','power_in'),(3,'OUT','output'),(4,'GND','power_in')])
sup=symbol('Power_Supervisor','TPS3808DBV');sup[1]='TPS3808G01'
for unit in nodes(sup,'symbol'):
 unit[1]=str(unit[1]).replace('TPS3808DBV','TPS3808G01')
 for pin in nodes(unit,'pin'):
  if str(atom(pin,'number'))=='1':pin[1]=S('open_collector')
custom.append(sup)
(LIB/'RoveFlight.kicad_sym').write_text(sx.dumps([S('kicad_symbol_lib'),[S('version'),20250114],[S('generator'),'kicad_symbol_editor'],*custom]))
def footprint(name,pads,body):
 w,h=body;doc=[S('footprint'),name,[S('version'),20250108],[S('generator'),'pcbnew'],[S('layer'),'F.Cu'],[S('attr'),S('smd')],prop('Reference','REF**',0,-h/2-1),prop('Value',name,0,h/2+1)]
 for item in doc:
  if isinstance(item,list) and item and str(item[0])=='property':item.insert(4,[S('layer'),'F.Fab'])
 for layer,margin in [('F.Fab',0),('F.CrtYd',.25)]:doc.append([S('fp_rect'),[S('start'),-w/2-margin,-h/2-margin],[S('end'),w/2+margin,h/2+margin],[S('stroke'),[S('width'),.05],[S('type'),S('default')]],[S('fill'),S('none')],[S('layer'),layer]])
 for n,x,y,sx_,sy_ in pads:doc.append([S('pad'),str(n),S('smd'),S('rect'),[S('at'),x,y],[S('size'),sx_,sy_],[S('layers'),'F.Cu','F.Paste','F.Mask']])
 (LIB/'RoveFlight.pretty'/f'{name}.kicad_mod').write_text(sx.dumps(doc))
# BMP390 top view: pin 1 upper right; Fig26 nominal pad geometry, mirror bottom view.
footprint('BMP390_LGA10',[(1,.25,-.7625,.25,.275),(2,-.25,-.7625,.25,.275),(3,-.7625,-.5,.275,.25),(4,-.7625,0,.275,.25),(5,-.7625,.5,.275,.25),(6,-.25,.7625,.25,.275),(7,.25,.7625,.25,.275),(8,.7625,.5,.275,.25),(9,.7625,0,.275,.25),(10,.7625,-.5,.275,.25)],(2,2))
footprint('TSOP75438TT',[(i+1,(i-1.5)*1.27,0,.8,1.8) for i in range(4)],(6.8,3.2))
# TSOP TT uses a single pad row along one edge of the body.
irpath=LIB/'RoveFlight.pretty/TSOP75438TT.kicad_mod';irdoc=sx.loads(irpath.read_text())
for rect in nodes(irdoc,'fp_rect'):
 if atom(rect,'layer')=='F.Fab':node(rect,'start')[2]=-3.;node(rect,'end')[2]=.2
 else:node(rect,'start')[2]=-3.25;node(rect,'end')[2]=1.15
irpath.write_text(sx.dumps(irdoc))
footprint('MotorPads',[(1,-1.5,0,2.2,3),(2,1.5,0,2.2,3)],(6,3.4))
footprint('BatteryPads',[(1,-2.5,0,3.5,4),(2,2.5,0,3.5,4)],(9,4.4))
footprint('ProbePad',[(1,0,0,.7,.7)],(.9,.9))
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "RoveFlight") (type "KiCad") (uri "${KIPRJMOD}/libraries/RoveFlight.kicad_sym") (options "") (descr "Datasheet verified flight controller parts")))')
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "RoveFlight") (type "KiCad") (uri "${KIPRJMOD}/libraries/RoveFlight.pretty") (options "") (descr "Project land patterns")))')
d=Design()
def add(ref,lib,name,val,nets,xy=None,fp=None,mpn=None,mfr='',source='',side='F',rot=0):
 d.parent=ref if ref.startswith('U') else d.parent
 return d.add(lib,name,val,nets,fp=fp,xy=xy,rot=rot,ref=ref,mpn=mpn or val,mfr=mfr,source=source,side=side)
def r(val,a,b,xy=None,ref=None,fp=None,mpn=None):
 vals={'0':'0R00','22':'22R0','100':'1000','1k':'1001','2.2k':'2201','5.1k':'5101','10k':'1002','47k':'4702','100k':'1003','1M':'1004','665k':'6653'}
 return d.add('Device','R',val,{'1':a,'2':b},fp=fp or 'Resistor_SMD:R_0402_1005Metric',xy=xy,ref=ref,mpn=mpn or 'RC0402FR-07'+vals.get(val,val)+'L',mfr='Yageo')
def c(val,a,b='GND',xy=None,fp=None,mpn=None):
 mp={'100nF':'GRM155R71C104KA88D','1uF':'GRM155R61A105KE15D','10uF':'GRM188R60J106ME47D','22uF':'GRM21BR60J226ME39L','1nF':'GRM1555C1H102JA01D','10nF':'GRM155R71H103KA88D'}
 return d.add('Device','C',val,{'1':a,'2':b},fp=fp or ('Capacitor_SMD:C_0805_2012Metric' if val=='22uF' else 'Capacitor_SMD:C_0603_1608Metric' if val=='10uF' else 'Capacitor_SMD:C_0402_1005Metric'),xy=xy,mpn=mpn or mp[val],mfr='Murata')
def ic(ref,lib,name,nets,xy,**kw):
 d.parent=ref
 return add(ref,lib,name,kw.pop('val',name),nets,xy,**kw)
ESP='https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf'
d.section='ESP32S3 Controller'
n={'1':'GND','2':'+3V3','3':'EN','4':'PWM_M1','5':'PWM_M2','6':'PWM_M3','7':'PWM_M4','8':'IR_RX','9':'TOF_INT','10':'TOF_XSHUT','11':'I2C_SCL','12':'I2C_SDA','13':'USB_DM','14':'USB_DP','17':'IMU_INT','18':'IMU_CS','19':'SPI_MOSI','20':'SPI_SCK','21':'SPI_MISO','22':'BARO_CS','23':'STATUS_LED','24':'FLOW_CS','25':'FLOW_INT','27':'BOOT','31':'ARM_CLK','32':'WD_HEARTBEAT','33':'KILL_OD','34':'RC_RX','35':'RC_TX','36':'DEBUG_RX','37':'DEBUG_TX','38':'BAT_ADC','39':'CURRENT_ADC','40':'GND','41':'GND'}
ic('U1','RF_Module','ESP32-S3-WROOM-1',n,(22.5,6),val='ESP32-S3-WROOM-1-N8R2',fp='RoveFlight:ESP32-S3-WROOM-1_Overhang',mfr='Espressif',source=ESP)
c('100nF','+3V3');c('10uF','+3V3');c('22uF','+3V3');r('10k','+3V3','EN');c('1uF','EN');r('10k','+3V3','BOOT')
for ref,net,xy in [('SW1','EN',(5,19)),('SW2','BOOT',(10,19)),('SW3','SAFE_CLR_N',(39,28))]:add(ref,'Switch','SW_Push',{'SW1':'RESET','SW2':'BOOT','SW3':'KILL'}[ref],{'1':net,'2':'GND'},xy,fp='Button_Switch_SMD:SW_Push_1P1T-SH_NO_CK_KMR2xxG',mpn='KMR221GLFS',mfr='C&K',side='B' if ref=='SW3' else 'F')
r('100k','ARM_CLK','GND');r('100k','WD_HEARTBEAT','GND');r('10k','+3V3','IMU_CS');r('10k','+3V3','BARO_CS');r('10k','+3V3','FLOW_CS')
d.note[d.section]='N8R2: 8MB Quad SPI flash, 2MB Quad PSRAM. Do not substitute Octal PSRAM variants.\nGPIO19/20 dedicated USB. GPIO0/3/45/46 are straps; GPIO35/36/37 unused.\nGPIO38 arming clock; GPIO39 watchdog; GPIO40 open-drain KILL. Motor PWM GPIO4..7.'
d.section='USB Programming'
usb={'A1':'GND','A4':'USB_VBUS','A5':'USB_CC1','A6':'USB_DP_CONN','A7':'USB_DM_CONN','A9':'USB_VBUS','A12':'GND','B1':'GND','B4':'USB_VBUS','B5':'USB_CC2','B6':'USB_DP_CONN','B7':'USB_DM_CONN','B9':'USB_VBUS','B12':'GND','SH':'GND'}
add('J1','Connector','USB_C_Receptacle_USB2.0_16P','USB-C',usb,(3.5,25),fp='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',mpn='TYPE-C-31-M-12',mfr='HRO',rot=270)
r('5.1k','USB_CC1','GND');r('5.1k','USB_CC2','GND');r('22','USB_DP_CONN','USB_DP');r('22','USB_DM_CONN','USB_DM')
ic('U2','Power_Protection','USBLC6-2SC6',{'1':'USB_DP_CONN','6':'USB_DP_CONN','3':'USB_DM_CONN','4':'USB_DM_CONN','2':'GND','5':'USB_VBUS'},(8.5,25),mfr='STMicroelectronics',source='https://www.st.com/resource/en/datasheet/usblc6-2.pdf')
c('1uF','USB_VBUS');d.note[d.section]='Native ESP32-S3 USB Serial/JTAG, no UART bridge. USB VBUS powers logic through diode OR.\nUSB insertion independently asserts the motor latch clear. No battery charging.'
d.section='Battery Power'
add('J2','Connector_Generic','Conn_01x02','1S BATTERY',{'1':'BAT_RAW','2':'GND'},(22.5,42),fp='RoveFlight:BatteryPads',mpn='PCB_SOLDER_PADS_20AWG',mfr='PCB')
add('F1','Device','Fuse','5A fuse',{'1':'BAT_RAW','2':'BAT_FUSED'},(17,38),fp='Fuse:Fuse_1206_3216Metric',mpn='0467005.NR',mfr='Littelfuse')
ic('Q1','RoveFlight','DMP2008UFG',{'1':'BAT_PROTECTED','2':'BAT_PROTECTED','3':'BAT_PROTECTED','4':'GND','5':'BAT_FUSED'},(22.5,36),val='DMP2008UFG-7',mfr='Diodes Inc.',source='https://www.diodes.com/datasheet/download/DMP2008UFG.pdf')
add('R100','Device','R','5mOhm 1% 0.25W',{'1':'BAT_PROTECTED','2':'VM'},(27.5,37),fp='Resistor_SMD:R_1206_3216Metric',mpn='WSL1206R0050FEA',mfr='Vishay')
for ref,a,xy in [('D1','VM',(30,34)),('D2','USB_VBUS',(12,30))]:add(ref,'Device','D_Schottky','SS14',{'1':'SYS_IN','2':a},xy,fp='Diode_SMD:D_SMA',mpn='SS14-13-F',mfr='Diodes Inc.')
# Small gate pads are not on motor bus: current returns go directly to common ground plane.
d.parent=None
c('22uF','SYS_IN',xy=(14,34));c('100nF','SYS_IN',xy=(15,36))
ic('U3','Regulator_Switching','TPS63001',{'1':'+3V3','2':'REG_L2','3':'GND','4':'REG_L1','5':'SYS_IN','6':'SYS_IN','7':'SYS_IN','8':'REG_VINA','9':'GND','10':'+3V3','11':'GND'},(13,37),val='TPS63001DRCR',mfr='Texas Instruments',source='https://www.ti.com/lit/ds/symlink/tps63000.pdf')
r('100','SYS_IN','REG_VINA');c('100nF','REG_VINA');c('22uF','+3V3');c('22uF','+3V3');add('L1','Device','L','2.2uH 3A',{'1':'REG_L1','2':'REG_L2'},(12,41),fp='Inductor_SMD:L_Vishay_IFSC-1515AH_4x4x1.8mm',mpn='IFSC1515AHER2R2M01',mfr='Vishay')
# Analog sensor filter, not a separate ground island.
add('FB1','Device','FerriteBead','600R@100MHz',{'1':'+3V3','2':'+3V3_SENS'},(18,27),fp='Inductor_SMD:L_0603_1608Metric',mpn='BLM18AG601SN1D',mfr='Murata');d.parent='FB1';c('10uF','+3V3_SENS');c('100nF','+3V3_SENS')
d.parent=None
for ref,xy in [('C100',(32,39)),('C101',(37,19))]:add(ref,'Device','C_Polarized','100uF 6.3V polymer',{'1':'VM','2':'GND'},xy,fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B',mpn='T520B107M006ATE070',mfr='KEMET')
d.note[d.section]='1S LiPo 3.1-4.2V; 4A continuous aggregate motor current, stall pulses separately qualified.\nQ1 reverse-polarity protection, F1 catastrophic fault backup; EXTERNAL protected pack required.\nTPS63001 fixed 3V3, forced PWM. SYS_IN diode OR cannot charge battery. No charger fitted.'
add('C102','Device','C_Polarized','100uF 6.3V logic bulk',{'1':'+3V3','2':'GND'},(17,14),fp='Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B',mpn='T520B107M006ATE070',mfr='KEMET',side='B')
d.section='Motor Safety Interlock'
ic('U4','RoveFlight','TPS3431',{'1':'+3V3','2':'WD_TIMING','3':'+3V3','4':'GND','5':'+3V3','6':'WD_HEARTBEAT','7':'SAFE_CLR_N','9':'GND'},(32,29),val='TPS3431SDRBR',mfr='Texas Instruments',source='https://www.ti.com/lit/ds/symlink/tps3431.pdf');c('100nF','+3V3');c('1nF','WD_TIMING')
ic('U5','RoveFlight','TPS3808G01',{'1':'SAFE_CLR_N','2':'GND','3':'EN','4':'UV_DELAY','5':'UV_SENSE','6':'+3V3'},(34,34),val='TPS3808G01DBVR',mfr='Texas Instruments',source='https://www.ti.com/lit/ds/symlink/tps3808.pdf');c('100nF','+3V3');c('10nF','UV_DELAY');r('665k','VM','UV_SENSE');r('100k','UV_SENSE','GND');c('10nF','UV_SENSE')
ic('U6','RoveFlight','SN74LVC1G74',{'1':'ARM_CLK','2':'+3V3','3':'ARMED_N','4':'GND','5':'ARMED','6':'SAFE_CLR_N','7':'+3V3','8':'+3V3'},(30,24),val='SN74LVC1G74DCUR',mfr='Texas Instruments',source='https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf');c('100nF','+3V3');r('10k','+3V3','SAFE_CLR_N')
# Firmware kill is open-drain; series resistor prevents destructive push-pull contention.
r('1k','KILL_OD','SAFE_CLR_N')
ic('Q2','Transistor_FET','2N7002',{'1':'USB_KILL_GATE','2':'GND','3':'SAFE_CLR_N'},(29,29),mfr='Nexperia');r('100k','USB_VBUS','USB_KILL_GATE');r('1M','USB_KILL_GATE','GND')
add('JP1','Connector_Generic','Conn_01x02','REMOVE TO DISARM',{'1':'ARMED_N','2':'MOTOR_OE_N'},(40,33),fp='Connector_PinHeader_1.27mm:PinHeader_1x02_P1.27mm_Vertical',mpn='20021111-00002T4LF',mfr='Amphenol');r('10k','+3V3','MOTOR_OE_N')
buf={'1':'MOTOR_OE_N','2':'PWM_M1','3':'BUF_M1','4':'MOTOR_OE_N','5':'PWM_M2','6':'BUF_M2','7':'GND','8':'BUF_M3','9':'PWM_M3','10':'MOTOR_OE_N','11':'BUF_M4','12':'PWM_M4','13':'MOTOR_OE_N','14':'+3V3'}
ic('U7','74xx','74LVC125',buf,(37,24),val='SN74LVC125APWR',fp='Package_SO:TSSOP-14_4.4x5mm_P0.65mm',mfr='Texas Instruments',source='https://www.ti.com/lit/ds/symlink/sn74lvc125a.pdf');c('100nF','+3V3')
d.note[d.section]='SAFE_CLR_N is wired-OR: watchdog, VM undervoltage, USB, KILL button, firmware OD.\nAsync clear latches disarmed. A NEW rising ARM_CLK is required after every fault.\nJP1 physically disconnects enable. PWM gates high impedance when disarmed, with 10k gate pulldowns.\nWatchdog 1nF: 132.4ms nominal, falling-edge heartbeat <20ms required from healthy control task.'
for i,xy in enumerate([(3.7,12),(41.3,12),(41.3,41),(3.7,41)],1):
 d.section=f'Motor M{i}';d.parent=None
 add(f'J{i+2}','Connector_Generic','Conn_01x02',f'M{i} MOTOR',{'1':'VM','2':f'M{i}_NEG'},xy,fp='RoveFlight:MotorPads',mpn='PCB_SOLDER_PADS_24AWG',mfr='PCB')
 qxy=[(5,15.5),(40,15.5),(40,37),(5,37)][i-1]
 ic(f'Q{i+2}','Transistor_FET','AO3400A',{'1':f'GATE_M{i}','2':'GND','3':f'M{i}_NEG'},qxy,mfr='Alpha & Omega',source='https://www.aosmd.com/res/data_sheets/AO3400A.pdf')
 r('100',f'BUF_M{i}',f'GATE_M{i}');r('10k',f'GATE_M{i}','GND');r('100k',f'PWM_M{i}','GND')
 add(f'D{i+2}','Device','D_Schottky','SS24',{'1':'VM','2':f'M{i}_NEG'},[ (4,8),(41,8),(40,34),(5,34)][i-1],fp='Diode_SMD:D_SMA',mpn='SS24-13-F',mfr='Diodes Inc.')
 c('100nF','VM');d.note[d.section]='1S BRUSHED ONLY. Pin1 VM+, pin2 switched motor negative. 1A running / 2A brief stall target.\n100R gate resistor; 10k gate-source pulldown; SS24 flyback cathode VM, anode drain.\nFit additional 100nF directly at motor terminals; twist leads. Rotation is set by motor wiring.'
d.section='SPI Flight Sensors'
ic('U8','RoveFlight','BMI270',{'1':'SPI_MISO','4':'IMU_INT','5':'+3V3_SENS','6':'GND','7':'GND','8':'+3V3_SENS','12':'IMU_CS','13':'SPI_SCK','14':'SPI_MOSI'},(22.5,23),mfr='Bosch Sensortec',source='https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmi270-ds000.pdf');c('100nF','+3V3_SENS');c('100nF','+3V3_SENS');c('1uF','+3V3_SENS')
ic('U9','RoveFlight','BMP390',{'1':'+3V3_SENS','2':'SPI_SCK','3':'GND','4':'SPI_MOSI','5':'SPI_MISO','6':'BARO_CS','8':'GND','9':'GND','10':'+3V3_SENS'},(12,21),side='B',mfr='Bosch Sensortec',source='https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bmp390-ds002.pdf');c('100nF','+3V3_SENS');c('100nF','+3V3_SENS')
d.note[d.section]='BMI270 primary 4-wire SPI, INT1 data ready. Auxiliary/OIS pins intentionally NC.\nBMP390 on shared SPI with independent CS; INT unused. Pressure port faces underside.\nNo compass: motor conductors are too close for a defensible uncalibrated onboard heading.'
d.section='Optical and IR'
ic('U10','Sensor_Distance','VL53L1CXV0FY1',{'1':'+3V3_SENS','2':'GND','3':'GND','4':'GND','5':'TOF_XSHUT','6':'GND','7':'TOF_INT','9':'I2C_SDA','10':'I2C_SCL','11':'+3V3_SENS','12':'GND'},(22.5,28),val='VL53L1CXV0FY/1',side='B',mfr='STMicroelectronics',source='https://www.st.com/resource/en/datasheet/vl53l1x.pdf');c('100nF','+3V3_SENS');c('4.7uF','+3V3_SENS',fp='Capacitor_SMD:C_0603_1608Metric',mpn='GRM188R60J475KE19D');r('10k','+3V3_SENS','TOF_XSHUT');r('10k','+3V3_SENS','TOF_INT');r('2.2k','+3V3_SENS','I2C_SDA');r('2.2k','+3V3_SENS','I2C_SCL')
ic('U11','RoveFlight','TSOP75438TT',{'1':'GND','2':'IR_VS','3':'IR_RX','4':'GND'},(7,29),side='B',mfr='Vishay',source='https://www.vishay.com/docs/82494/tsop752.pdf');r('100','+3V3','IR_VS');c('1uF','IR_VS');c('100nF','IR_VS')
d.note[d.section]='VL53L1X faces DOWN, I2C 0x29. Firmware must enable 2V8 I/O mode for 3V3 supply.\nUse near-ground ranging only; sunlight, reflective floors, tilt and prop wash limit reliability.\nTSOP75438TT is a 38kHz receiver, not proximity sensing. Optical flow is an external SPI module.'
d.section='Battery Monitoring'
ic('U12','Amplifier_Current','INA180A2',{'1':'CURRENT_RAW','2':'GND','3':'BAT_PROTECTED','4':'VM','5':'+3V3'},(28,33),val='INA180A2IDBVR',mfr='Texas Instruments',source='https://www.ti.com/lit/ds/symlink/ina180.pdf');c('100nF','+3V3');r('1k','CURRENT_RAW','CURRENT_ADC');c('100nF','CURRENT_ADC');r('100k','VM','BAT_DIV');r('100k','BAT_DIV','GND');r('1k','BAT_DIV','BAT_ADC');c('100nF','BAT_ADC')
d.note[d.section]='Kelvin sense R1, 5mOhm. INA180A2 gain50: 0.25V/A. ADC1 GPIO1.\nBattery ADC1 GPIO2, 1:2 divider, RC filter. Calibrate ADC offset/gain in firmware.\nFuse is backup short-circuit protection; firmware must implement current and low-battery shutdown.'
d.section='Receiver Expansion and Indicators';d.parent=None
for ref,label,nn,xy,side in [('J7','RC 3V3',['GND','+3V3','RC_RX','RC_TX'],(40,20),'B'),('J8','OPTICAL FLOW SPI',['GND','+3V3','SPI_SCK','SPI_MOSI','SPI_MISO','FLOW_CS','FLOW_INT'],(22,19),'B'),('J9','DEBUG UART',['GND','+3V3','DEBUG_TX','DEBUG_RX','EN','BOOT'],(31,20),'B'),('J10','I2C 3V3',['GND','+3V3_SENS','I2C_SDA','I2C_SCL'],(31,9),'B')]:
 add(ref,'Connector_Generic',f'Conn_01x{len(nn):02}',label,{str(i+1):v for i,v in enumerate(nn)},xy,fp=f'Connector_JST:JST_SH_SM{len(nn):02}B-SRSS-TB_1x{len(nn):02}-1MP_P1.00mm_Horizontal',mpn=f'SM{len(nn):02}B-SRSS-TB(LF)(SN)',mfr='JST',side=side)
add('D7','Device','LED','GREEN',{'1':'GND','2':'LED_A'},(32,20),fp='LED_SMD:LED_0402_1005Metric',mpn='150040GS73240',mfr='Wurth');r('1k','STATUS_LED','LED_A')
for i,(net,xy) in enumerate([('+3V3',(27,20)),('GND',(28,20)),('VM',(29,20)),('I2C_SDA',(31,11)),('I2C_SCL',(31,12)),('SPI_SCK',(25,25)),('SPI_MOSI',(25,26)),('SPI_MISO',(25,27)),('DEBUG_TX',(31,17)),('DEBUG_RX',(32,17)),('PWM_M1',(33,21)),('PWM_M2',(34,21)),('PWM_M3',(35,21)),('PWM_M4',(36,21)),('SAFE_CLR_N',(32,25)),('ARMED',(33,25))],1):add(f'TP{i}','Connector','TestPoint',net,{'1':net},xy,fp='RoveFlight:ProbePad',mpn='PCB_TEST_PAD',mfr='PCB',side='B')
d.note[d.section]='Receiver: 3V3 UART CRSF/iBUS only, no 5V tolerance or onboard SBUS inverter.\nExternal PMW3901 breakout must include its required regulator/level compatibility and lens.\nSPI test pads/flow connector are 3V3; sensor SPI max10MHz, initial firmware 1MHz.'
d.save();d.schematic();print('Constructed',len(d.parts),'electrical entries')
