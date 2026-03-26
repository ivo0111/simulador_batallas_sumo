import mujoco
import mujoco.viewer
import time

with open("scene.xml") as f:
    xml = f.read()

model = mujoco.MjModel.from_xml_string(xml)
data = mujoco.MjData(model)

mujoco.mj_saveLastXML("scene_compiled.xml", model)

for i in range(model.njnt):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
    dof_adr = model.jnt_dofadr[i]
    print(f"Joint {i}: '{name}' → DOF {dof_adr}")

with mujoco.viewer.launch_passive(model, data) as viewer:
    sim_time = 0.0
    real_start = time.time()

    while viewer.is_running():
        # Cuánto tiempo real pasó
        real_elapsed = time.time() - real_start
        
        # Correr steps hasta alcanzar el tiempo real
        while sim_time < real_elapsed:
            data.ctrl[0] = 5
            data.ctrl[1] = 5
            mujoco.mj_step(model, data)
            sim_time += model.opt.timestep

        viewer.sync()