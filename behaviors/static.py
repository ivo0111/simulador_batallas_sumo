# ============================================================
# ESTRATEGIA: Circular / flanqueador
# Con estado: mantiene el movimiento en arco de forma continua
# y registra si ya está en ataque para no interrumpirlo.
# ============================================================

class Robot:
    def __init__(self):
        self.fase = "circular"     # circular | atacar | recuperar
        self.ticks_fase = 0
        self.ticks_total = 0

    def _set_fase(self, nueva):
        self.fase = nueva
        self.ticks_fase = 0

    def decide(self, sensors):
        return 0.0, 0.0