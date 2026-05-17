# ============================================================
# ESTRATEGIA: Agresivo directo
# ============================================================

# Ajustá este valor hasta lograr un giro de ~90° al inicio
TICKS_GIRO_INICIAL = 400

TICKS_BUSQUEDA     = 3000   # ticks girando antes de invertir dirección


class Robot:
    def __init__(self):
        self.ticks_sin_enemigo  = 0
        self.direccion_busqueda = 1

        # Arranca con la maniobra de giro inicial ya cargada
        self.maniobra_actual = (3.0, -3.0)
        self.ticks_maniobra  = TICKS_GIRO_INICIAL

    def _iniciar_maniobra(self, vel_izq, vel_der, duracion):
        self.maniobra_actual = (vel_izq, vel_der)
        self.ticks_maniobra  = duracion

    def decide(self, sensors):
        line_left  = sensors["line_left"]
        line_right = sensors["line_right"]
        enemy      = sensors["enemy"]

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

        # ── Prioridad 2: atacar ──
        if enemy:
            self.ticks_sin_enemigo = 0
            return 20.0, 20.0

        # ── Prioridad 3: buscar girando ──
        self.ticks_sin_enemigo += 1
        if self.ticks_sin_enemigo % TICKS_BUSQUEDA == 0:
            self.direccion_busqueda *= -1

        vel = 3.0 * self.direccion_busqueda
        return vel, -vel