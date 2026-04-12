# viewer.py
import mujoco
import mujoco.viewer
import time

model = mujoco.MjModel.from_xml_path("scene.xml")
data  = mujoco.MjData(model)

with mujoco.viewer.launch_passive(model, data) as viewer:
    real_start = time.time()
    sim_time   = 0.0

    while viewer.is_running():
        real_elapsed = time.time() - real_start

        while sim_time < real_elapsed:
            mujoco.mj_step(model, data)
            sim_time += model.opt.timestep

        viewer.sync()