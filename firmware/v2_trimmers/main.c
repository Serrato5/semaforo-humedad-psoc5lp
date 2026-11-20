/* ============================================================================
 * Sensor de humedad del suelo con semaforo de LEDs - VERSION ANALOGICA v2
 * Tarjeta: PSoC 5LP CY8CKIT-059 (PSoC Creator 4.4)
 *
 * Cambio v2 (por la entrevista E01): los umbrales ya NO salen de dos VDAC,
 * salen de dos potenciometros en la plaquita. Asi el docente ajusta los
 * rangos de cada practica girando una perilla, sin reprogramar.
 *
 *   Sensor (P3[0]) -> Opamp_1 (seguidor) -> Vbuf (P3[1], punto de prueba)
 *   Umbral_Seco   (pot. 1, P3[2]) -> Comp_Seco   (-)   Vbuf -> Comp_Seco (+)
 *   Umbral_Humedo (pot. 2, P3[3]) -> Comp_Humedo (+)   Vbuf -> Comp_Humedo (-)
 *   LED_Rojo = Comp_Seco, LED_Verde = Comp_Humedo,
 *   LED_Amarillo = NOR(Comp_Seco, Comp_Humedo)
 *
 * La CPU solo arranca los bloques y reporta el estado por USB (UART_1,
 * pin Tx_1 = P12[7], 115200 8N1). No participa en la decision.
 *
 * REGLA: Umbral_Seco siempre debe quedar MAYOR que Umbral_Humedo.
 * Si se invierten, prenden rojo y verde a la vez y el programa avisa.
 * ==========================================================================*/
#include "project.h"

#define PERIODO_MS 500

int main(void)
{
    uint8 seco;
    uint8 humedo;

    CyGlobalIntEnable;

    /* Cadena analogica */
    Opamp_1_Start();
    Comp_Seco_Start();
    Comp_Humedo_Start();

    /* Informe al PC */
    UART_1_Start();
    UART_1_PutString("\r\nSensor de humedad del suelo - PSoC 5LP (analogico v2)\r\n");
    UART_1_PutString("Umbrales ajustables con potenciometros: medir P3[2] y P3[3]\r\n");

    for (;;)
    {
        seco   = Comp_Seco_GetCompare();
        humedo = Comp_Humedo_GetCompare();

        if (seco && humedo)
        {
            UART_1_PutString("ERROR: umbrales invertidos (Umbral_Seco debe ser mayor que Umbral_Humedo)\r\n");
        }
        else if (seco)   { UART_1_PutString("Estado: SECO (rojo)\r\n"); }
        else if (humedo) { UART_1_PutString("Estado: HUMEDO (verde)\r\n"); }
        else             { UART_1_PutString("Estado: SEMIHUMEDO (amarillo)\r\n"); }

        CyDelay(PERIODO_MS);
    }
}

/* [] FIN DEL ARCHIVO */
