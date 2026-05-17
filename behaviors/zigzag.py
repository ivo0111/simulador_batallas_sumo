# ============================================================
# ESTRATEGIA: Zigzag de aproximación
#
# En lugar de ir recto al enemigo, se acerca en zigzag para
# ser difícil de empujar de frente. Alterna arcos opuestos
# mientras avanza, manteniendo siempre progresión hacia adelante.
#
# Concepto clave: cada arco siempre tiene una rueda hacia
# adelante (velocidad positiva), así el robot nunca deja de
# avanzar mientras zigzaguea.
# ============================================================

TICKS_GIRO_INICIAL = 400
TICKS_ZIG          = 3000   # duración de cada mitad del zigzag


class Robot:
    def __init__(self):
        self.ticks_total  = 0
        self.fase_zig     = 0    # 0 = arco derecha, 1 = arco izquierda

        self.maniobra_actual = (3.0, -3.0)
        self.ticks_maniobra  = TICKS_GIRO_INICIAL

    def _iniciar_maniobra(self, vel_izq, vel_der, duracion):
        self.maniobra_actual = (vel_izq, vel_der)
        self.ticks_maniobra  = duracion

    def decide(self, sensors):
        line_left  = sensors["line_left"]
        line_right = sensors["line_right"]
        enemy      = sensors["enemy"]
        dist       = sensors["front_ir"]

        self.ticks_total += 1

        # ── Maniobra en curso ──
        if self.ticks_maniobra > 0:
            self.ticks_maniobra -= 1
            if not (line_left or line_right):
                return self.maniobra_actual

        # ── Prioridad 1: línea ──
        if line_left and line_right:
            self._iniciar_maniobra(-4.0, -4.0, duracion=50)
            return self.maniobra_actual
        if line_left:
            self._iniciar_maniobra(-4.0, -1.5, duracion=50)
            return self.maniobra_actual
        if line_right:
            self._iniciar_maniobra(-1.5, -4.0, duracion=50)
            return self.maniobra_actual

        # ── Prioridad 2: enemigo muy cerca → empuje recto ──
        # Al estar muy cerca el zigzag deja de tener sentido,
        # es mejor empujar directo con toda la fuerza
        if enemy and dist < 0.3:
            self._iniciar_maniobra(5.0, 5.0, duracion=100)
            return self.maniobra_actual

        # ── Prioridad 3: enemigo visible → aproximación en zigzag ──
        if enemy:
            # Alternar fase cada TICKS_ZIG ticks
            self.fase_zig = (self.ticks_total // TICKS_ZIG) % 2

            if self.fase_zig == 0:
                # Arco hacia la derecha: rueda izq más rápida
                # Siempre avanzando (ambas velocidades positivas)
                return 12, 7.5
            else:
                # Arco hacia la izquierda: rueda der más rápida
                return 7.5, 12

        # ── Prioridad 4: sin enemigo → buscar girando ──
        # Giro lento sobre el eje para buscar al rival
        return 5, -5
