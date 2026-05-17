# ============================================================
# ESTRATEGIA: Errático / impredecible
#
# Mejora clave: estabilidad en las transiciones.
# El problema anterior era que las fases eran cortas y los
# cambios de velocidad bruscos. Ahora:
#   1. Las fases son más largas (en la misma escala que los
#      3000 ticks del agresor, proporcional a timestep=0.001s)
#   2. Las velocidades de fases consecutivas son más cercanas
#      para evitar sacudones
#   3. Se agrega una fase de "transición" entre movimientos
#      muy distintos (ej: avance → giro brusco)
# ============================================================

TICKS_GIRO_INICIAL = 400

# Cada fase: (nombre, duración en ticks, (vel_izq, vel_der))
# Las fases están ordenadas para que las velocidades cambien
# gradualmente entre una y la siguiente.
FASES = [
    ("avanzar_rapido",  800,  (4.0,  4.0)),
    ("transicion_1",    200,  (3.0,  1.0)),   # suaviza el cambio
    ("arco_derecha",    600,  (3.5,  1.5)),
    ("transicion_2",    200,  (2.5,  2.5)),   # suaviza el cambio
    ("avanzar_medio",   600,  (2.5,  2.5)),
    ("transicion_3",    200,  (1.0,  3.0)),   # suaviza el cambio
    ("arco_izquierda",  600,  (1.5,  3.5)),
    ("transicion_4",    200,  (3.0,  3.0)),   # suaviza el cambio
]


class Robot:
    def __init__(self):
        self.fase_idx      = 0
        self.ticks_en_fase = 0
        self.interrumpido  = False

        self.maniobra_actual = (3.0, -3.0)
        self.ticks_maniobra  = TICKS_GIRO_INICIAL

    def _iniciar_maniobra(self, vel_izq, vel_der, duracion):
        self.maniobra_actual = (vel_izq, vel_der)
        self.ticks_maniobra  = duracion

    def _avanzar_fase(self):
        self.fase_idx      = (self.fase_idx + 1) % len(FASES)
        self.ticks_en_fase = 0

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
            self.interrumpido = True
            self._iniciar_maniobra(-4.0, -4.0, duracion=50)
            return self.maniobra_actual
        if line_left:
            self.interrumpido = True
            self._iniciar_maniobra(-3.0, 0.5, duracion=50)
            return self.maniobra_actual
        if line_right:
            self.interrumpido = True
            self._iniciar_maniobra(0.5, -3.0, duracion=50)
            return self.maniobra_actual

        # ── Prioridad 2: enemigo ──
        if enemy:
            self.interrumpido = False
            return 5.0, 5.0

        # Si hubo interrupción, retomar desde la primera fase
        if self.interrumpido:
            self.interrumpido = False
            self.fase_idx      = 0
            self.ticks_en_fase = 0

        # ── Prioridad 3: ciclo de fases estables ──
        _, duracion, (vel_izq, vel_der) = FASES[self.fase_idx]
        self.ticks_en_fase += 1
        if self.ticks_en_fase >= duracion:
            self._avanzar_fase()

        return vel_izq, vel_der