import mujoco
import mujoco.viewer

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
    t = 0
    while viewer.is_running():
        t += model.opt.timestep

        if t < 2.0:
            # Avanza recto
            data.ctrl[0] = 8.0
            data.ctrl[1] = 8.0
        else:
            # Gira
            data.ctrl[0] = 8.0
            data.ctrl[1] = -8.0

        mujoco.mj_step(model, data)
        viewer.sync()