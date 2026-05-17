# ============================================================
# ESTRATEGIA: Evasivo / defensivo
# ============================================================

# Ajustá este valor hasta lograr un giro de ~90° al inicio
TICKS_GIRO_INICIAL = 1500


class Robot:
    def __init__(self):
        self.lado_evasion = 1

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
        dist       = sensors["front_ir"]

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
            self.lado_evasion = -1
            self._iniciar_maniobra(-2.0, -4.0, duracion=50)
            return self.maniobra_actual
        if line_right:
            self.lado_evasion = 1
            self._iniciar_maniobra(-4.0, -2.0, duracion=50)
            return self.maniobra_actual

        # ── Prioridad 2: enemigo muy cerca → ataque directo ──
        if enemy and dist < 0.3:
            self._iniciar_maniobra(5.0, 5.0, duracion=80)
            return self.maniobra_actual

        # ── Prioridad 3: enemigo visible → evadir en arco ──
        if enemy:
            self.lado_evasion *= -1
            if self.lado_evasion == 1:
                self._iniciar_maniobra(4.0, 1.5, duracion=120)
            else:
                self._iniciar_maniobra(1.5, 4.0, duracion=120)
            return self.maniobra_actual

        # ── Prioridad 4: patrulla lenta ──
        return 1.5, 1.5