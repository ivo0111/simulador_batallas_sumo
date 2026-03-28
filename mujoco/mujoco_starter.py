import mujoco
import mujoco.viewer
import numpy as np
import time

model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# IDs resueltos una sola vez al inicio
id_line_left  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_line_left")
id_line_right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_line_right")
id_front_ir   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_front_ir")
id_dohyo      = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "dohyo_surface")

print(f"line_left site:  {id_line_left}")
print(f"line_right site: {id_line_right}")
print(f"front_ir site:   {id_front_ir}")
print(f"dohyo geom:      {id_dohyo}")

def read_sensors():
    geomid = np.array([-1], dtype=np.int32)
    down   = np.array([0.0, 0.0, -1.0])

    # Line left
    dist_ll = mujoco.mj_ray(model, data, data.site_xpos[id_line_left],down, None, 1, -1, geomid)
    line_left = (geomid[0] != id_dohyo)

    # Line right
    dist_lr = mujoco.mj_ray(model, data, data.site_xpos[id_line_right], down, None, 1, -1, geomid)
    line_right = (geomid[0] != id_dohyo)

    # Front IR
    rot     = data.site_xmat[id_front_ir].reshape(3, 3)
    forward = -rot[:, 1]
    dist_ir = mujoco.mj_ray(model, data, data.site_xpos[id_front_ir], forward, None, 1, -1, geomid)

    return {
        "line_left":  line_left,
        "line_right": line_right,
        "front_ir":   dist_ir,
        "enemy":      (0 < dist_ir < 0.5)
    }

def controller():
    s = read_sensors()

    edge  = s["line_left"] or s["line_right"]
    enemy = s["enemy"]

    if edge:
        data.ctrl[0] = -3
        data.ctrl[1] = -3
    elif enemy:
        data.ctrl[0] =  15
        data.ctrl[1] =  15
    else:
        data.ctrl[0] =  1.5
        data.ctrl[1] = -1.5

with mujoco.viewer.launch_passive(model, data) as viewer:
    real_start = time.time()
    sim_time   = 0.0

    while viewer.is_running():
        real_elapsed = time.time() - real_start

        while sim_time < real_elapsed:
            controller()
            mujoco.mj_step(model, data)
            sim_time += model.opt.timestep

        viewer.sync()