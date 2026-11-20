#!/bin/sh
# Flujo completo del P5: esquemático -> ERC -> PCB -> autorrutado (Freerouting) -> planos GND -> DRC
# Uso: ROW=20.32 FLIP=0 sh build.sh
set -e
H=$HOME; P=$H/mnt/PSoC/Proyecto5_PCBA; K=$P/kicad
cd $P/scripts
python3 spec.py spec.json
KLIB=$H/squashfs-root/share/kicad/symbols python3 gen_sch.py $K/semaforo_p5.kicad_sch spec.json
cd $K
$H/kcli.sh sch erc --severity-all -o erc.rpt semaforo_p5.kicad_sch 2>/dev/null | tail -1
$H/kpy.sh ../scripts/gen_pcb.py place ../scripts/spec.json semaforo_p5.kicad_sch.ids.json semaforo_p5.kicad_pcb 2>/dev/null
cp semaforo_p5.dsn /tmp/r.dsn; rm -f /tmp/r.ses
(cd /tmp && $H/jre/bin/java -Djava.awt.headless=true -jar $H/freerouting.jar -de /tmp/r.dsn -do /tmp/r.ses -mp 40 2>&1 | grep -o "Auto-routing stage completed.*violations)" )
cp /tmp/r.ses semaforo_p5.ses
$H/kpy.sh ../scripts/gen_pcb.py finish semaforo_p5.kicad_pcb semaforo_p5.ses 2>/dev/null
sed -i "s|Potentiometer_Bourns_TC33X_Vertical.step|Potentiometer_Bourns_3314J_Vertical.step|" semaforo_p5.kicad_pcb
$H/kcli.sh pcb drc --schematic-parity --severity-all -o drc.rpt semaforo_p5.kicad_pcb 2>/dev/null | tail -3
