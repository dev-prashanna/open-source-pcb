from cadlib import *
from collections import defaultdict
parts=json.loads((ROOT/'design.json').read_text());byref={c['ref']:c for c in parts}
rows=[
 (0,25,'BOOT','Programming strap; button/J1','Pullup; hold low only for download'),
 (1,35,'U0_TX','USB bridge / J1','Console/programming UART transmit'),
 (2,24,'BUZZ_PWM','Piezo MOSFET / J21','Boot strap; external gate pulldown; ADC2 not used'),
 (3,34,'U0_RX','USB bridge / J1','Console/programming UART receive'),
 (4,26,'US_TRIG','5V buffered ultrasonic trigger / J20','General output; not a 5V-tolerant ESP input'),
 (5,29,'SPI_CS','SPI J17 / J21','Boot strap; pullup; peripheral must not force low during reset'),
 (12,14,'STRAP12','Dedicated 10k pulldown; reserved','Selects flash voltage; not general GPIO; JTAG conflicts'),
 (13,16,'US_ECHO','Buffered echo / J20','3V3 output of echo buffer; do not externally drive shared header'),
 (14,13,'M_B2','Motor bridge B input2 / J20','PWM; JTAG alternate unavailable while motor active'),
 (15,23,'SERVO_OE','Servo disable / J21','Boot strap; external pullup; HIGH disables servo outputs'),
 (16,27,'UART_RX','GPS/UART J18','Can be TWAI RX only when UART/GPS disabled; N8 no PSRAM'),
 (17,28,'UART_TX','GPS/UART J18','Can be TWAI TX only when UART/GPS disabled'),
 (18,30,'SPI_SCK','SPI J17','3V3 SPI clock'),
 (19,31,'SPI_MISO','SPI J17','3V3 SPI receive'),
 (21,33,'I2C_SDA','Onboard bus / J16','2.2k pullup; shared with all onboard I2C parts'),
 (22,36,'I2C_SCL','Onboard bus / J16','2.2k pullup; initially 100kHz, validate 400kHz rise time'),
 (23,37,'SPI_MOSI','SPI J17','3V3 SPI transmit'),
 (25,10,'M_A1','Motor bridge A input1 / J20','PWM; ADC2 not used'),
 (26,11,'M_A2','Motor bridge A input2 / J20','PWM; ADC2 not used'),
 (27,12,'M_B1','Motor bridge B input1 / J20','PWM; ADC2 not used'),
 (32,8,'IMU_INT','IMU INT1 / J20','Direct interrupt; occupied, not free analog input'),
 (33,9,'BAT_ADC','Battery divider / J20','ADC1, WiFi-compatible; occupied by battery sensing'),
 (34,6,'ENC_RA','Encoder right A / J21','INPUT ONLY, no internal pullup; external buffer'),
 (35,7,'ENC_RB','Encoder right B / J21','INPUT ONLY, no internal pullup; external buffer'),
 (36,4,'ENC_LA','Encoder left A / J21','INPUT ONLY, SENSOR_VP, no internal pullup; external buffer'),
 (39,5,'ENC_LB','Encoder left B / J21','INPUT ONLY, SENSOR_VN, no internal pullup; external buffer')]
text='# P-TIWARI GPIO allocation\n\nESP32-WROOM-32E-N8, no PSRAM. All ESP32 logic is 3.3 V. GPIO6–11 are used by module flash; GPIO20/24/28–31/37/38 are unavailable in this module. GPIO34/35/36/39 are input-only. ADC2 is unavailable for ordinary simultaneous Wi-Fi ADC use; onboard battery sensing uses ADC1 and external analog uses ADS1115.\n\n| GPIO | Module pad | Net | Connection | Constraint |\n|---:|---:|---|---|---|\n'
for row in rows:text+='| '+' | '.join(map(str,row))+' |\n'
text+='\nExpansion headers expose allocated signals for probing and alternate firmware use. They do not create extra independent GPIO or disconnect onboard drivers. Do not configure a buffered encoder/echo net as an output or externally drive an IMU interrupt. GPIO12 is deliberately not presented as unrestricted expansion.\n\n## Expander and PWM allocation\n\n| Device pin | Function | Firmware rule |\n|---|---|---|\n| MCP GPA0 | Motor sleep | External pulldown; set HIGH only after safe motor controls |\n| MCP GPA1 | Motor nFAULT | Input, active LOW; pullup fitted |\n| MCP GPA2 | ToF XSHUT | Emulate open drain: LOW output / released input |\n| MCP GPA3 | ToF interrupt | Input, pullup fitted |\n| MCP GPA4 | User button | Input, active LOW |\n| MCP GPA5/6/7 | Red/green/blue LEDs | LOW turns on; GPA7 output-only |\n| MCP GPB0..2 | TP1..TP3 local service pads | 3V3 GPIO, accessible solder/probe pads |\n| MCP GPB3..6 | J19 expansion | 3V3 GPIO; poll or arrange external interrupt support |\n| MCP GPB7 | J19 / load MOSFET | OUTPUT ONLY; also turns load on when HIGH |\n| PCA9685 LED0..3 | Servo1..4 | Shared nominal 50Hz, external 5V buffers |\n\nThe MCP23017 INTA/B outputs are intentionally unconnected; fast encoder counting and the IMU interrupt do not use the expander. Current manufacturer documentation specifies GPA7/GPB7 as output-only: [Microchip datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf).\n'
(ROOT/'docs/GPIO_Mapping.md').write_text(text)
with (ROOT/'GPIO_Mapping.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['ESP32_GPIO','Module_Pad','Net','Connection','Constraint']);w.writerows(rows)

limits={'J1':'3V3 service logic only','J2':'USB 5V sink, full-speed data, no PD','J3':'Protected 2S 6.4–8.4V; no onboard charging','J4':'Regulated external 5V logic input','J5':'External 5–6V servo input','J6':'Separate motor input 3–8.4V','J7':'Motor A, <=0.6A continuous target','J8':'Motor B, <=0.6A continuous target','J9':'5V accessories require battery BAT5; ECHO input buffered','J10':'Encoder power 3V3; A/B buffer inputs accept <=5.5V','J11':'Encoder power 3V3; A/B buffer inputs accept <=5.5V','J16':'3V3 I2C, shared pullups, short cable','J17':'3V3 SPI; CS boot strap must remain high at reset','J18':'3V3 UART/GPS; alternate external CAN transceiver replaces UART','J19':'3V3 GPB3..7; pins3..5 are ground returns; B7 output-only/shared load','J20':'Shared controller signals; BAT_ADC and IMU_INT are inputs','J21':'Shared controller signals; encoder pins input-only','J22':'0–3V3 analog, ADS1115 total <=860samples/s','J23':'5V switched load, <=250mA, battery BAT5 required','JP1':'ONE shunt:1-2 battery servo,2-3 external servo'}
for i in range(12,16):limits['J'+str(i)]='GND / servo supply / 5V signal; aggregate servo current limit applies'
with (ROOT/'Connector_Pinouts.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Connector','Label','Pin','Signal','Interface_limit'])
 for c in parts:
  if c['ref'].startswith(('J','TP')):
   for pin,net in c['nets'].items():w.writerow([c['ref'],c['value'],pin,net,limits.get(c['ref'],'3V3 logic')])
text='# P-TIWARI connector reference\n\nPin numbers follow the KiCad footprint and the square/marked pin-1 pad, viewed from the component side. Cable drawings can mirror this view: verify mating orientation before making a harness. Never infer wire colors or JST motor polarity from unrelated breakout boards.\n\n'
for c in parts:
 if not c['ref'].startswith(('J','TP')):continue
 text+='## '+c['ref']+' — '+c['value']+'\n\n'+limits.get(c['ref'],'')+'\n\n'
 text+='| Pin | Signal |\n|---|---|\n'+''.join('| '+pin+' | '+net+' |\n' for pin,net in c['nets'].items())+'\n'
text+='USB SBU pads A8/B8 are intentionally unused; shell is grounded. Connector signals containing RAW or FUSED are named before or after protection and are not regulated outputs. For each servo connector, pin1 is GND, pin2 is the selected servo supply, pin3 is PWM. Power domains are not interchangeable.\n'
(ROOT/'docs/Connector_Pinouts.md').write_text(text)
groups=defaultdict(list)
for c in parts:groups[(c['mpn'],c['value'],c['fp'],c['mfr'])].append(c['ref'])
with (ROOT/'BOM_Grouped.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Quantity','References','Value','MPN','Manufacturer','Footprint'])
 for (mpn,value,fp,mfr),refs in groups.items():w.writerow([len(refs),','.join(refs),value,mpn,mfr,fp])
# Firmware pin contract is deliberately framework-independent.
(ROOT/'firmware').mkdir(exist_ok=True)
hdr='// P-TIWARI A.0; pin contract only, not validated application firmware.\n#pragma once\nnamespace p_tiwari {\n'
for gpio,pad,net,_,_ in rows:hdr+='constexpr int PIN_'+net+' = '+str(gpio)+';\n'
hdr+='constexpr unsigned IMU_ADDR=0x6A, MAG_ADDR=0x1C, BME_ADDR=0x76, ALS_ADDR=0x10;\nconstexpr unsigned TOF_ADDR=0x29, PWM_ADDR=0x40, EXP_ADDR=0x20, ADC_ADDR=0x48;\n}\n'
(ROOT/'firmware/board_pins.h').write_text(hdr)
print('GPIO, connector and grouped BOM references generated')
