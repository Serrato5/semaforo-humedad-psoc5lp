#!/bin/sh
# Archivos de fabricación para JLCPCB
set -e
H=$HOME; P=$H/mnt/PSoC/Proyecto5_PCBA; K=$P/kicad; O=$P/fabricacion
mkdir -p $O/gerber
cd $K
$H/kcli.sh pcb export gerbers --layers F.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --no-x2 -o $O/gerber/ semaforo_p5.kicad_pcb 2>/dev/null | tail -1
$H/kcli.sh pcb export drill --format excellon --drill-origin absolute --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 -o $O/gerber/ semaforo_p5.kicad_pcb 2>/dev/null | tail -1
$H/kcli.sh pcb export pos --format csv --units mm --side front --exclude-dnp -o $O/posiciones_kicad.csv semaforo_p5.kicad_pcb 2>/dev/null | tail -1
python3 ../scripts/jlc.py ../scripts/spec.json $O/posiciones_kicad.csv $O "${JLCROT:-{\}}"
cd $O/gerber && python3 -c "import zipfile,os;z=zipfile.ZipFile('../GERBER_semaforo_p5.zip','w',zipfile.ZIP_DEFLATED);[z.write(f) for f in sorted(os.listdir('.'))];z.close()"
ls -la $O
