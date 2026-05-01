// src/lib/three/RobotBuilder.js

// Tipos de geom de MuJoCo
const GeomType = {
    SPHERE: 2,
    CAPSULE: 3,
    CYLINDER: 5,
    BOX: 6,
    MESH: 7,
}

export function buildSceneDescription(sceneInit) {
    return sceneInit.scene.bodies
        .filter(body => body.name !== "world" && body.name !== "arena")
        .map(body => ({
            id: body.name,
            geoms: body.geoms
                .filter(g => g.type !== 0)  // ignorar planes
                .map(g => parseGeom(g))
        }))
        .filter(body => body.geoms.length > 0)
}

function parseGeom(g) {
    const base = {
        pos: g.pos,
        quat: g.quat,
        rgba: g.rgba,
        material: g.material ?? null,
    }

    switch (g.type) {
        case GeomType.BOX:
            return { ...base, type: "box", size: g.size }

        case GeomType.SPHERE:
            return { ...base, type: "sphere", size: g.size }

        case GeomType.CYLINDER:
            return { ...base, type: "cylinder", size: g.size }

        case GeomType.MESH:
            return { ...base, type: "mesh", src: `http://localhost:8000/assets/${g.mesh_file}` }

        default:
            return { ...base, type: "unknown" }
    }
}