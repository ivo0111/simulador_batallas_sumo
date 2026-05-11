import mujoco
import numpy as np
import importlib.util
import sys

DEFAULT_BEHAVIOR = """
def decide(sensors):
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

        self.site_left      = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "line_left")
        self.site_right     = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "line_right")
        self.site_front     = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "front_ir")
        self.left_ctrl_idx  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, prefix + "robot_left")
        self.right_ctrl_idx = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, prefix + "robot_right")

        # Cargamos el comportamiento por defecto
        self._decide_fn = self._load_default()

    def _load_default(self):
        """Crea una función decide() desde el comportamiento hardcodeado."""
        ns = {}
        exec(DEFAULT_BEHAVIOR, ns)
        return ns["decide"]

    def load_code(self, code: str):
        """
        Recibe código Python como string, lo valida y reemplaza
        la función decide(). Lanza ValueError si no define 'decide'.
        """
        ns = {}
        exec(compile(code, "<robot_code>", "exec"), ns)
        if "decide" not in ns:
            raise ValueError("El código debe definir una función 'decide(sensors)'")
        self._decide_fn = ns["decide"]

    def read_sensors(self):
        geomid = np.array([-1], dtype=np.int32)
        down   = np.array([0.0, 0.0, -1.0])

        mujoco.mj_ray(self.model, self.data,
                    self.data.site_xpos[self.site_left], down, None, 1, -1, geomid)
        line_left = (geomid[0] != self.id_dohyo)

        mujoco.mj_ray(self.model, self.data,
                    self.data.site_xpos[self.site_right], down, None, 1, -1, geomid)
        line_right = (geomid[0] != self.id_dohyo)

        rot     = self.data.site_xmat[self.site_front].reshape(3, 3)
        forward = -rot[:, 1]
        dist_ir = mujoco.mj_ray(self.model, self.data,
                                self.data.site_xpos[self.site_front],
                                forward, None, 1, -1, geomid)

        return {
            "line_left":  line_left,
            "line_right": line_right,
            "front_ir":   float(dist_ir),
            "enemy":      (0 < dist_ir < 0.9),
        }

    def decide(self):
        sensors = self.read_sensors()
        try:
            result = self._decide_fn(sensors)
            left, right = float(result[0]), float(result[1])
        except Exception as e:
            print(f"[{self.prefix}] Error en decide(): {e}")
            left, right = 0.0, 0.0
        return left, right

    def apply_control(self):
        left, right = self.decide()
        self.data.ctrl[self.left_ctrl_idx] = left
        self.data.ctrl[self.right_ctrl_idx] = right