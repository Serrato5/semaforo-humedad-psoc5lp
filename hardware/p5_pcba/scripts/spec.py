#!/usr/bin/env python3
"""Lista de materiales y conexiones del Proyecto 5 (fuente única para esquemático, PCB y BOM)."""
import json, sys
R0805 = 'Resistor_SMD:R_0805_2012Metric'; C0805 = 'Capacitor_SMD:C_0805_2012Metric'; L0805 = 'LED_SMD:LED_0805_2012Metric'
parts = []
def add(ref, lib, val, fp, at, nets, lcsc='', desc='', mpn='', nobom=False):
    parts.append(dict(ref=ref, lib=lib, val=val, fp=fp, at=at, nets=nets, lcsc=lcsc, desc=desc, mpn=mpn, nobom=nobom))

# --- Socket parcial hacia la PSoC: solo los pines que se usan (4 tiras hembra de 2,54 mm)
# KIT = número de pin del CY8CKIT-059 al que corresponde cada pin de la tira
SOCK = {'J1A': ('J1', [4, 5, 6], {'1': 'LED_R', '2': 'LED_A', '3': 'LED_V'}, 'P2[3], P2[4], P2[5]'),
        'J1B': ('J1', [25, 26], {'1': 'GND', '2': None}, 'GND, VDDIO (sin usar)'),
        'J2A': ('J2', [1, 2], {'1': '+5V', '2': 'GND'}, 'VDD, GND'),
        'J2B': ('J2', [22, 23, 24, 25, 26], {'1': 'U_HUM', '2': 'U_SECO', '3': 'VBUF', '4': 'SENS', '5': 'GND'}, 'P3[3], P3[2], P3[1], P3[0], GND')}
for i, (ref, (row, kit, nets, desc)) in enumerate(SOCK.items()):
    n = len(kit)
    add(ref, f'Connector_Generic:Conn_01x0{n}', f'PSoC {row} p{kit[0]}-{kit[-1]}', f'Connector_PinSocket_2.54mm:PinSocket_1x0{n}_P2.54mm_Vertical',
        (40.64, 40.64 + 25.4 * i), nets, desc=f'Tira hembra 1x{n} 2,54 mm a la fila {row} del CY8CKIT-059: {desc} (THT, compra aparte)')
    parts[-1]['kit'] = [row, kit]
add('J3', 'Connector_Generic:Conn_01x03', 'Sensor (GND, VCC, AOUT)', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical', (101.6, 50.8), {'1': 'GND', '2': '+5V', '3': 'AOUT'}, desc='Header macho 1x3 para el sensor capacitivo v1.2 (THT)')

# --- Protección de entrada
add('R1', 'Device:R', '1k', R0805, (139.7, 50.8), {'1': 'AOUT', '2': 'SENS'}, 'C17513', 'Resistencia 1 kΩ 1 % 0805', '0805W8F1001T5E')
add('D1', 'Device:D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', (165.1, 45.72), {'1': '+5V', '2': 'SENS'}, 'C8598', 'Schottky 40 V 1 A SOD-123 (recorta sobre 5 V)', 'B5819W')
add('D2', 'Device:D_Schottky', 'B5819W', 'Diode_SMD:D_SOD-123', (165.1, 60.96), {'1': 'SENS', '2': 'GND'}, 'C8598', 'Schottky 40 V 1 A SOD-123 (recorta bajo 0 V)', 'B5819W')
add('C3', 'Device:C', '100n', C0805, (190.5, 50.8), {'1': 'SENS', '2': 'GND'}, 'C49678', 'Condensador 100 nF X7R 50 V 0805', 'CC0805KRX7R9BB104')

# --- Umbrales ajustables
add('R5', 'Device:R', '3.3k', R0805, (139.7, 96.52), {'1': '+5V', '2': 'RV2_H'}, 'C26010', 'Resistencia 3,3 kΩ 1 % 0805', '0805W8F3301T5E')
add('RV2', 'Device:R_Potentiometer_Trim', '10k', 'Potentiometer_SMD:Potentiometer_Bourns_TC33X_Vertical', (165.1, 101.6), {'1': 'RV2_H', '2': 'U_SECO', '3': 'RV2_L'}, 'C719176', 'Trimmer 10 kΩ SMD 3 mm', 'TC33X-2-103E')
add('R6', 'Device:R', '3.3k', R0805, (139.7, 111.76), {'1': 'RV2_L', '2': 'GND'}, 'C26010', 'Resistencia 3,3 kΩ 1 % 0805', '0805W8F3301T5E')
add('C4', 'Device:C', '100n', C0805, (190.5, 101.6), {'1': 'U_SECO', '2': 'GND'}, 'C49678', 'Condensador 100 nF X7R 50 V 0805', 'CC0805KRX7R9BB104')
add('R7', 'Device:R', '3.3k', R0805, (139.7, 137.16), {'1': '+5V', '2': 'RV3_H'}, 'C26010', 'Resistencia 3,3 kΩ 1 % 0805', '0805W8F3301T5E')
add('RV3', 'Device:R_Potentiometer_Trim', '10k', 'Potentiometer_SMD:Potentiometer_Bourns_TC33X_Vertical', (165.1, 142.24), {'1': 'RV3_H', '2': 'U_HUM', '3': 'RV3_L'}, 'C719176', 'Trimmer 10 kΩ SMD 3 mm', 'TC33X-2-103E')
add('R8', 'Device:R', '3.3k', R0805, (139.7, 152.4), {'1': 'RV3_L', '2': 'GND'}, 'C26010', 'Resistencia 3,3 kΩ 1 % 0805', '0805W8F3301T5E')
add('C5', 'Device:C', '100n', C0805, (190.5, 142.24), {'1': 'U_HUM', '2': 'GND'}, 'C49678', 'Condensador 100 nF X7R 50 V 0805', 'CC0805KRX7R9BB104')

# --- Semáforo
for i, (net, col, lc) in enumerate([('LED_R', 'rojo', 'C84256'), ('LED_A', 'amarillo', 'C2296'), ('LED_V', 'verde', 'C2297')]):
    y = 96.52 + i * 22.86
    add(f'R{2+i}', 'Device:R', '1k', R0805, (241.3, y), {'1': net, '2': f'{net}_LED'}, 'C17513', 'Resistencia 1 kΩ 1 % 0805', '0805W8F1001T5E')
    add(f'D{3+i}', 'Device:LED', f'LED {col}', L0805, (271.78, y), {'1': 'GND', '2': f'{net}_LED'}, lc, f'LED {col} 0805', {'rojo': 'KT-0805R', 'amarillo': 'KT-0805Y', 'verde': 'KT-0805G'}[col])

# --- Alimentación
add('C1', 'Device:C', '100n', C0805, (241.3, 50.8), {'1': '+5V', '2': 'GND'}, 'C49678', 'Condensador 100 nF X7R 50 V 0805', 'CC0805KRX7R9BB104')
add('C2', 'Device:C', '10u', C0805, (261.62, 50.8), {'1': '+5V', '2': 'GND'}, 'C15850', 'Condensador 10 µF X5R 25 V 0805', 'CL21A106KAYNNNE')

# --- Puntos de prueba (pads de cobre, sin componente) y agujeros de montaje
for i, net in enumerate(['VBUF', 'U_SECO', 'U_HUM', '+5V', 'GND']):
    add(f'TP{i+1}', 'Connector:TestPoint', net.replace('+', ''), 'TestPoint:TestPoint_Pad_D1.5mm', (304.8 + 15.24 * (i % 3), 50.8 + 22.86 * (i // 3)), {'1': net}, desc='Punto de prueba', nobom=True)
for i in range(4):
    add(f'H{i+1}', 'Mechanical:MountingHole', 'M3', 'MountingHole:MountingHole_3.2mm_M3', (304.8 + 12.7 * i, 111.76), {}, desc='Agujero de montaje 3,2 mm', nobom=True)

texts = [(25.4, 25.4, 'Socket parcial para la PSoC 5LP (CY8CKIT-059): solo los pines usados', 2.5),
         (127, 33.02, 'Entrada del sensor y protección (Schottky a 5 V y GND)', 2.5),
         (127, 83.82, 'Umbrales ajustables: 0,99 V a 4,01 V', 2.5),
         (228.6, 83.82, 'Semáforo (salidas P2[3..5])', 2.5),
         (228.6, 33.02, 'Desacople de 5 V', 2.5),
         (292.1, 33.02, 'Puntos de prueba y montaje', 2.5)]
json.dump(dict(title='Semáforo de humedad - tarjeta para PSoC 5LP (P5)', parts=parts, texts=texts), open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print(len(parts), 'partes')
