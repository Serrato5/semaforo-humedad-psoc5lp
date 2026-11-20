/* ============================================================================
 * Sensor de humedad del suelo con semaforo de LEDs - VERSION ANALOGICA
 * Tarjeta: PSoC 5LP CY8CKIT-059 (PSoC Creator 4.4)
 *
 * La decision NO la toma la CPU: la hacen los bloques analogicos internos.
 *
 *   Sensor (P3[0]) -> Opamp_1 (seguidor) -> Vbuf (P3[1], punto de prueba)
 *        Vbuf -> Comp_Seco   (+)   VDAC_Seco   -> (-)   salida 1 si suelo SECO
 *        Vbuf -> Comp_Humedo (-)   VDAC_Humedo -> (+)   salida 1 si suelo HUMEDO
 *   LED_Rojo     = salida de Comp_Seco
 *   LED_Verde    = salida de Comp_Humedo
 *   LED_Amarillo = NOR(Comp_Seco, Comp_Humedo)   (ni seco ni humedo)
 *
 * La CPU solo: 1) arranca los bloques, 2) carga los umbrales en los VDAC,
 * 3) informa el estado al PC por USB. Si la CPU se detuviera despues de
 * arrancar, los LEDs seguirian funcionando.
 *
 * Componentes en TopDesign.cysch (nombres EXACTOS):
 *   Sensor        Analog pin                         -> P3[0]
 *   Opamp_1       Opamp, modo Follower, potencia Medium
 *   Vbuf          Analog pin (punto de prueba)       -> P3[1]
 *   VDAC_Seco     VDAC8, rango 0-4.080 V (16 mV/bit), fuente CPU
 *   VDAC_Humedo   VDAC8, rango 0-4.080 V (16 mV/bit), fuente CPU
 *   Comp_Seco     Comparator, Hysteresis Enable, Speed Slow, no invertido
 *   Comp_Humedo   Comparator, Hysteresis Enable, Speed Slow, no invertido
 *   NOR_1         Logic -> NOR de 2 entradas
 *   LED_Rojo      Digital output pin, HW connection   -> P2[3]
 *   LED_Amarillo  Digital output pin, HW connection   -> P2[4]
 *   LED_Verde     Digital output pin, HW connection   -> P2[5]
 *   UART_1        UART, solo TX, 115200 8N1           -> P12[7]
 * ==========================================================================*/
#include "project.h"
#include <stdio.h>

/* ---------- Calibracion: medir con multimetro en Vbuf (P3[1]) ------------ */
#define V_SECO_MV        2900   /* tierra seca           (0 %)               */
#define V_MOJADO_MV      1350   /* tierra empapada       (100 %)             */

/* ---------- Umbrales del semaforo, en % de humedad ----------------------- */
#define UMBRAL_SECO        30   /* por debajo de 30 %  -> rojo               */
#define UMBRAL_HUMEDO      60   /* por encima de 60 %  -> verde              */

#define MV_POR_PASO_VDAC   16   /* VDAC8 en rango 0-4.080 V: 16 mV por paso  */
#define PERIODO_MS        500

/* Voltaje que corresponde a un porcentaje de humedad (recta de calibracion).
 * El voltaje BAJA cuando hay mas agua. */
static int32 porcentaje_a_mV(int32 porcentaje)
{
    return V_SECO_MV - ((V_SECO_MV - V_MOJADO_MV) * porcentaje) / 100;
}

/* Codigo del VDAC8 (0 a 255) mas cercano a un voltaje en mV. */
static uint8 mV_a_codigo(int32 mV)
{
    int32 codigo = (mV + MV_POR_PASO_VDAC / 2) / MV_POR_PASO_VDAC;

    if (codigo < 0)   { codigo = 0;   }
    if (codigo > 255) { codigo = 255; }
    return (uint8)codigo;
}

int main(void)
{
    char  texto[96];
    uint8 cod_seco, cod_humedo;
    uint8 seco, humedo;

    /* Umbrales en voltaje: 30 % -> mas alto, 60 % -> mas bajo */
    cod_seco   = mV_a_codigo(porcentaje_a_mV(UMBRAL_SECO));
    cod_humedo = mV_a_codigo(porcentaje_a_mV(UMBRAL_HUMEDO));

    CyGlobalIntEnable;

    /* 1. Arrancar la cadena analogica */
    Opamp_1_Start();
    VDAC_Seco_Start();
    VDAC_Humedo_Start();
    VDAC_Seco_SetValue(cod_seco);
    VDAC_Humedo_SetValue(cod_humedo);
    Comp_Seco_Start();
    Comp_Humedo_Start();

    /* 2. Informe al PC */
    UART_1_Start();
    UART_1_PutString("\r\nSensor de humedad del suelo - PSoC 5LP (analogico)\r\n");
    sprintf(texto, "Umbral SECO   (%d %%): %ld mV, codigo VDAC %u\r\n",
            UMBRAL_SECO, (long)cod_seco * MV_POR_PASO_VDAC, (unsigned)cod_seco);
    UART_1_PutString(texto);
    sprintf(texto, "Umbral HUMEDO (%d %%): %ld mV, codigo VDAC %u\r\n",
            UMBRAL_HUMEDO, (long)cod_humedo * MV_POR_PASO_VDAC, (unsigned)cod_humedo);
    UART_1_PutString(texto);

    /* 3. Los comparadores ya manejan los LEDs. Aqui solo se reporta. */
    for (;;)
    {
        seco   = Comp_Seco_GetCompare();
        humedo = Comp_Humedo_GetCompare();

        if (seco)        { UART_1_PutString("Estado: SECO (rojo)\r\n"); }
        else if (humedo) { UART_1_PutString("Estado: HUMEDO (verde)\r\n"); }
        else             { UART_1_PutString("Estado: SEMIHUMEDO (amarillo)\r\n"); }

        CyDelay(PERIODO_MS);
    }
}

/* [] FIN DEL ARCHIVO */
