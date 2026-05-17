# ============================================================
# ESTRATEGIA: Circular / flanqueador
#
# Mejora clave: los sensores de línea se usan de dos formas:
#   1. Emergencia: si los dos están activos → retroceder
#   2. Guía: si solo uno está activo → el robot está cerca
#      del borde, que es exactamente donde quiere estar.
#      En ese caso corrige levemente el arco sin detenerse.
#
# Esto hace que el robot "siga" el borde del dohyo en lugar
# de alejarse de él cada vez que lo detecta.
# ============================================================

# Radio del arco: cuanto mayor la diferencia entre ruedas,
# más cerrado es el giro. Ajustá para cambiar el radio.
VEL_RAPIDA = 25.0
VEL_LENTA  = 11.5


class Robot:
    def __init__(self):
        self.ticks_total    = 0
        self.sentido        = 1    # 1 = arco a la derecha, -1 = a la izquierda

        # Maniobra de emergencia (retroceso)
        self.maniobra_actual = (10.0, 10.0)
        self.ticks_maniobra  = 300

    def _iniciar_maniobra(self, vel_izq, vel_der, duracion):
        self.maniobra_actual = (vel_izq, vel_der)
        self.ticks_maniobra  = duracion

    def _arco(self, sentido):
        """Devuelve velocidades para un arco según el sentido."""
        if sentido == 1:
            return VEL_RAPIDA, VEL_LENTA   # arco a la derecha
        else:
            return VEL_LENTA, VEL_RAPIDA   # arco a la izquierda

    def decide(self, sensors):
        line_left  = sensors["line_left"]
        line_right = sensors["line_right"]
        enemy      = sensors["enemy"]
        dist       = sensors["front_ir"]

        self.ticks_total += 1

        # ── Maniobra de emergencia en curso ──
        if self.ticks_maniobra > 0:
            print("En maniobra")
            self.ticks_maniobra -= 1
            if not (line_left and line_right):
                return self.maniobra_actual

        # ── Prioridad 1: emergencia (los dos sensores activos) ──
        # Ambos sensores en línea = robot muy cerca del borde o saliendo
        if line_left and line_right:
            print("¡Emergencia! Retrocediendo")
            self._iniciar_maniobra(-20.0, -20.0, duracion=1000)
            return self.maniobra_actual

        # ── Prioridad 2: ataque ──
        if enemy:
            print("Atacando enemigo")
            self._iniciar_maniobra(20.0, 20.0, duracion=400)
            return self.maniobra_actual

        # ── Prioridad 3: guía por línea (un solo sensor activo) ──
        # En lugar de detenerse, corrige el arco sutilmente.
        # Si detecta línea a la izquierda, el arco se abre hacia la derecha
        # (rueda derecha más lenta) para alejarse del borde sin perder velocidad.
        if line_left:
            print("Corrección por línea izquierda")
            self.sentido = 1
            return VEL_RAPIDA, VEL_LENTA * 0.5   # corrección suave hacia adentro

        if line_right:
            print("Corrección por línea derecha")
            self.sentido = -1
            return VEL_LENTA * 0.5, VEL_RAPIDA   # corrección suave hacia adentro

        # ── Prioridad 4: movimiento circular base ──
        print("Movimiento circular")
        return self._arco(self.sentido)