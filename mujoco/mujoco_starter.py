import mujoco
import asyncio
import json
import time
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from robots import Sumobot

# Cargar modelo
model = mujoco.MjModel.from_xml_path("scene.xml")
data  = mujoco.MjData(model)

#* IDs de sensores

# Sites Robot A
A_id_line_left  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_line_left")
A_id_line_right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_line_right")
A_id_front_ir   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "A_front_ir")

# Sites Robot B
B_id_line_left  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "B_line_left")
B_id_line_right = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "B_line_right")
B_id_front_ir   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "B_front_ir")

# Dohyo
id_dohyo      = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "dohyo_surface")

mujoco.mj_step(model, data)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
active_ws: WebSocket = None  

robots = [
    Sumobot(model, data, "A_", id_dohyo),
    Sumobot(model, data, "B_", id_dohyo),
]

def controller():
    for robot in robots:
        robot.apply_control()

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

            mesh_name = None
            mesh_file = None
            if gtype == 7:  
                mesh_id = model.geom_dataid[gid]
                if mesh_id >= 0:
                    mesh_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MESH, mesh_id)
                    mesh_file = str.split(mesh_name,'_')[1] + ".stl"

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
                "mesh_file": mesh_file,
            })

        scene["bodies"].append({"name": name, "geoms": geoms})
    return scene

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

def reset_sim():
    """Resetea el estado de MuJoCo y re-instancia los comportamientos."""
    for robot in robots:
        robot.reset()                    # <-- re-instancia la clase Robot
    mujoco.mj_resetData(model, data)
    mujoco.mj_step(model, data)

@app.post("/sim/reset")
async def reset():
    reset_sim()
    mujoco.mj_resetData(model, data)
    mujoco.mj_step(model, data)
    if active_ws:
        await active_ws.send_text(json.dumps({
            "type": "SCENE_INIT",
            "scene": get_scene_description()
        }))
    return {"ok": True}

@app.post("/robot/{robot_id}/code")
async def upload_code(robot_id: str, file: UploadFile = File(...)):
    if robot_id not in ("A", "B"):
        raise HTTPException(status_code=404, detail="Robot no encontrado")

    code = (await file.read()).decode("utf-8")

    # Buscamos el robot por su prefix
    target = next((r for r in robots if r.prefix == f"{robot_id}_"), None)

    try:
        target.load_code(code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SyntaxError as e:
        raise HTTPException(status_code=400, detail=f"Error de sintaxis: {e}")

    reset_sim()
    return {"ok": True, "robot": robot_id}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global active_ws
    await ws.accept()
    active_ws = ws
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