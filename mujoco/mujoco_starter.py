import mujoco
import numpy as np
import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.staticfiles import StaticFiles

# Cargar modelo
model = mujoco.MjModel.from_xml_path("scene.xml")
data  = mujoco.MjData(model)

# IDs de sensores
id_line_left  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_line_left")
id_line_right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_line_right")
id_front_ir   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_front_ir")
id_dohyo      = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "dohyo_surface")

mujoco.mj_step(model, data)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

def get_scene_description():
    scene = {"bodies": []}
    for i in range(model.nbody):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
        if not name or name == "world":
            continue

        geoms = []
        for gid in range(model.ngeom):
            if model.geom_bodyid[gid] != i:
                continue

            gtype = model.geom_type[gid]
            if gtype == 0:  # ignorar planes
                continue

            gname  = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid)
            gsize  = model.geom_size[gid].tolist()
            gpos   = model.geom_pos[gid].tolist()
            gquat  = model.geom_quat[gid].tolist()
            rgba   = model.geom_rgba[gid].tolist()

            # Nombre del material si tiene
            mat_id   = model.geom_matid[gid]
            mat_name = None
            if mat_id >= 0:
                mat_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MATERIAL, mat_id)

            geoms.append({
                "name":     gname,
                "type":     int(gtype),
                "size":     gsize,
                "pos":      gpos,
                "quat":     gquat,
                "rgba":     rgba,
                "material": mat_name,
            })

        scene["bodies"].append({"name": name, "geoms": geoms})

    return scene

def read_sensors():
    geomid = np.array([-1], dtype=np.int32)
    down   = np.array([0.0, 0.0, -1.0])

    mujoco.mj_ray(model, data, data.site_xpos[id_line_left], down, None, 1, -1, geomid)
    line_left = (geomid[0] != id_dohyo)

    mujoco.mj_ray(model, data, data.site_xpos[id_line_right], down, None, 1, -1, geomid)
    line_right = (geomid[0] != id_dohyo)

    rot     = data.site_xmat[id_front_ir].reshape(3, 3)
    forward = -rot[:, 1]
    dist_ir = mujoco.mj_ray(model, data, data.site_xpos[id_front_ir], forward, None, 1, -1, geomid)

    return {
        "line_left":  line_left,
        "line_right": line_right,
        "front_ir":   float(dist_ir),
        "enemy":      (0 < dist_ir < 0.5)
    }

def controller():
    s = read_sensors()
    edge  = s["line_left"] or s["line_right"]
    enemy = s["enemy"]

    if edge:
        data.ctrl[0] = -0.1
        data.ctrl[1] = -0.1
    elif enemy:
        data.ctrl[0] =  2
        data.ctrl[1] =  2
    else:
        data.ctrl[0] =  0.04
        data.ctrl[1] = -0.04

def get_state():
    bodies = {}
    for i in range(model.nbody):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
        if name:
            bodies[name] = {
                "pos":  data.xpos[i].tolist(),
                "quat": data.xquat[i].tolist(),
            }

    return {
        "type":   "SIM_STATE",
        "bodies": bodies,
    }

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Cliente conectado")

    # Primer mensaje: descripción completa de la escena
    await ws.send_text(json.dumps({
        "type":  "SCENE_INIT",
        "scene": get_scene_description()
    }))

    sim_time   = 0.0
    real_start = time.time()

    try:
        while True:
            real_elapsed = time.time() - real_start

            while sim_time < real_elapsed:
                controller()
                mujoco.mj_step(model, data)
                sim_time += model.opt.timestep

            await ws.send_text(json.dumps(get_state()))
            await asyncio.sleep(1 / 60)

    except WebSocketDisconnect:
        print("Cliente desconectado")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)