import mujoco
import numpy as np

class Sumobot:
    def __init__(self, model, data, prefix, left_ctrl_idx, right_ctrl_idx, id_dohyo):
        self.model = model
        self.data = data
        self.prefix = prefix
        self.left_ctrl_idx = left_ctrl_idx
        self.right_ctrl_idx = right_ctrl_idx
        self.id_dohyo = id_dohyo

        self.site_left = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "line_left")
        self.site_right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "line_right")
        self.site_front = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, prefix + "front_ir")

    def read_sensors(self):
        geomid = np.array([-1], dtype=np.int32)
        down = np.array([0.0, 0.0, -1.0])

        mujoco.mj_ray(self.model, self.data, self.data.site_xpos[self.site_left], down, None, 1, -1, geomid)
        line_left = (geomid[0] != self.id_dohyo)

        mujoco.mj_ray(self.model, self.data, self.data.site_xpos[self.site_right], down, None, 1, -1, geomid)
        line_right = (geomid[0] != self.id_dohyo)

        rot = self.data.site_xmat[self.site_front].reshape(3, 3)
        forward = -rot[:, 1]
        dist_ir = mujoco.mj_ray(
            self.model,
            self.data,
            self.data.site_xpos[self.site_front],
            forward,
            None,
            1,
            -1,
            geomid,
        )

        return {
            "line_left": line_left,
            "line_right": line_right,
            "front_ir": float(dist_ir),
            "enemy": (0 < dist_ir < 0.5),
        }

    def decide(self):
        s = self.read_sensors()
        if s["line_left"] or s["line_right"]:
            return -0.1, -0.1
        if s["enemy"]:
            return 2.0, 2.0
        return 0.04, -0.04

    def apply_control(self):
        left, right = self.decide()
        self.data.ctrl[self.left_ctrl_idx] = left
        self.data.ctrl[self.right_ctrl_idx] = right
