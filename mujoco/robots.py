from turtle import forward

import mujoco
import numpy as np

DEFAULT_BEHAVIOR = """
class Robot:
    def __init__(self):
        self.ticks = 0

    def decide(self, sensors):
        if sensors["line_left"] or sensors["line_right"]:
            return -1, -1
        if sensors["enemy"]:
            return 2.0, 2.0
        return 0.5, -0.5
"""

class Sumobot:
    def __init__(self, model, data, prefix, id_dohyo):
        self.model = model
        self.data = data
        self.prefix = prefix
        self.id_dohyo = id_dohyo
        self._sensor_cache = {"line_left": False, "line_right": False, "front_ir": -1.0, "enemy": False}
        self._sensor_tick = 0
        self.SENSOR_INTERVAL = 10  # leer sensores cada 10 steps (~100 Hz)

        self.site_left      = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "line_left")
        self.site_right     = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "line_right")
        self.site_front     = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "front_ir")
        self.left_ctrl_idx  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, prefix + "robot_left")
        self.right_ctrl_idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, prefix + "robot_right")

        # Guardamos la clase (no la instancia) para poder re-instanciar en reset()
        self._robot_class    = self._load_default_class()
        self._robot_instance = self._robot_class()

    def _cone_sensor(self, site_id, half_angle_deg=15, num_rays=7):
        """
        Simula un sensor de proximidad cónico.
        Devuelve la distancia mínima detectada (-1 si ningún rayo impacta).
        """
        rot = self.data.site_xmat[site_id].reshape(3, 3)
        forward = -rot[:, 1]
        up      =  rot[:, 2]

        origin = self.data.site_xpos[site_id]
        half_angle = np.radians(half_angle_deg)
        angles = np.linspace(-half_angle, half_angle, num_rays)

        min_dist = -1.0
        geomid = np.array([-1], dtype=np.int32)

        for angle in angles:
            # Rotamos el vector forward alrededor de 'up' en cada ángulo
            # Usamos la fórmula de Rodrigues: v' = v·cos(θ) + (up×v)·sin(θ)
            direction = (forward * np.cos(angle)
                        + np.cross(up, forward) * np.sin(angle))
            direction /= np.linalg.norm(direction)  # normalizar por las dudas

            dist = mujoco.mj_ray(self.model, self.data,
                                origin, direction, None, 1, -1, geomid)

            if dist > 0:  # -1 significa que no impactó nada
                if min_dist < 0 or dist < min_dist:
                    min_dist = dist

        return min_dist

    def _load_default_class(self):
        """Devuelve la clase Robot del comportamiento por defecto."""
        ns = {}
        exec(DEFAULT_BEHAVIOR, ns)
        return ns["Robot"]

    def load_code(self, code: str):
        """
        Compila el código, guarda la clase Robot y crea una instancia fresca.
        Lanza ValueError si no define 'Robot'.
        """
        ns = {}
        exec(compile(code, "<robot_code>", "exec"), ns)
        if "Robot" not in ns:
            raise ValueError("El código debe definir una clase 'Robot' con un método 'decide(self, sensors)'")
        self._robot_class    = ns["Robot"]
        self._robot_instance = self._robot_class()

    def reset(self):
        """
        Re-instancia la clase Robot activa, reseteando todo su estado interno.
        Se llama desde el endpoint /sim/reset antes de resetear MuJoCo.
        """
        self._robot_instance = self._robot_class()

    def read_sensors(self):
        self._sensor_tick += 1
        if self._sensor_tick % self.SENSOR_INTERVAL != 0:
            return self._sensor_cache
        
        geomid = np.array([-1], dtype=np.int32)
        down = np.array([0.0, 0.0, -1.0])

        mujoco.mj_ray(self.model, self.data,
                    self.data.site_xpos[self.site_left], down, None, 1, -1, geomid)
        line_left = (geomid[0] != self.id_dohyo)

        mujoco.mj_ray(self.model, self.data,
                    self.data.site_xpos[self.site_right], down, None, 1, -1, geomid)
        line_right = (geomid[0] != self.id_dohyo)

        #rot = self.data.site_xmat[self.site_front].reshape(3, 3)
        #forward = -rot[:, 1]
        #dist_ir = mujoco.mj_ray(self.model, self.data,
        #                        self.data.site_xpos[self.site_front],
        #                        forward, None, 1, -1, geomid)
        dist_ir = self._cone_sensor(self.site_front, half_angle_deg=20, num_rays=9)
        self._sensor_cache = {
                    "line_left":  line_left,
                    "line_right": line_right,
                    "front_ir":   float(dist_ir),
                    "enemy":      (0 < dist_ir < 0.9),
                }
        return self._sensor_cache

    def decide(self):
        sensors = self.read_sensors()
        try:
            result = self._robot_instance.decide(sensors)
            left, right = float(result[0]), float(result[1])
        except Exception as e:
            print(f"[{self.prefix}] Error en decide(): {e}")
            left, right = 0.0, 0.0
        return left, right

    def apply_control(self):
        left, right = self.decide()
        self.data.ctrl[self.left_ctrl_idx] = left
        self.data.ctrl[self.right_ctrl_idx] = right