# ============================================================
# ESTRATEGIA: Espejo
#
# Infiere el movimiento del rival comparando front_ir entre
# ticks consecutivos (derivada del sensor):
#
#   dist actual > dist anterior → rival se aleja o se mueve
#                                  al costado → rotar a seguirlo
#   dist actual < dist anterior → rival se acerca → preparar
#                                  contragolpe o esquive
#   dist estable               → rival está quieto o de frente
#                                  → avanzar directo
#
# Esto es cualitativamente distinto a todos los anteriores:
# en lugar de reaccionar a *dónde está* el rival, reacciona
# a *cómo se está moviendo*.
# ============================================================

TICKS_GIRO_INICIAL = 400

UMBRAL_MOVIMIENTO  = 0.01  # diferencia mínima de dist para considerar movimiento
                            # ajustá si es muy sensible o muy sordo


class Robot:
    def __init__(self):
        self.dist_anterior  = None   # front_ir del tick previo
        self.dir_seguimiento = 1     # 1 = rotar derecha, -1 = rotar izquierda
        self.ticks_contragolpe = 0   # ticks esperando el impacto del rival

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
                self.dist_anterior = dist
                return self.maniobra_actual

        # ── Prioridad 1: línea ──
        if line_left and line_right:
            self._iniciar_maniobra(-4.0, -4.0, duracion=50)
            self.dist_anterior = dist
            return self.maniobra_actual
        if line_left:
            self.dir_seguimiento = 1   # si nos sacaron por la izquierda,
            self._iniciar_maniobra(-2.0, -4.0, duracion=50)  # próximo seguimiento a la derecha
            self.dist_anterior = dist
            return self.maniobra_actual
        if line_right:
            self.dir_seguimiento = -1
            self._iniciar_maniobra(-4.0, -2.0, duracion=50)
            self.dist_anterior = dist
            return self.maniobra_actual

        # ── Prioridad 2: lógica de espejo ──
        if enemy:
            delta = 0.0
            if self.dist_anterior is not None:
                delta = dist - self.dist_anterior   # positivo = se aleja, negativo = se acerca

            self.dist_anterior = dist

            if delta > UMBRAL_MOVIMIENTO:
                # Rival se está alejando o moviéndose al costado
                # → rotar para mantenerlo enfrente
                vel = 2.5 * self.dir_seguimiento
                return vel, -vel

            elif delta < -UMBRAL_MOVIMIENTO:
                # Rival se está acercando → contragolpe explosivo
                # Esperamos a que llegue y empujamos con toda la fuerza
                if dist < 0.4:
                    self._iniciar_maniobra(5.0, 5.0, duracion=120)
                    return self.maniobra_actual
                else:
                    # Todavía lejos, avanzar para acortar distancia
                    return 3.5, 3.5

            else:
                # Rival quieto o moviéndose de frente → avanzar directo
                return 4.0, 4.0

        # ── Prioridad 3: sin enemigo → búsqueda rotando ──
        self.dist_anterior = None   # resetear memoria al perder al rival
        vel = 2.5 * self.dir_seguimiento
        return vel, -vel
