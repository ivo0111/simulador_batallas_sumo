// src/lib/three/SceneManager.js
import * as THREE from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const MATERIAL_TEXTURES = {
    'dohyo_mat': 'http://localhost:8000/assets/dohyo.PNG'
}

export class SceneManager {
    constructor(canvas) {
        // Renderer — dibuja en el canvas que le pasamos desde Svelte
        this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight)
        this.renderer.shadowMap.enabled = true

        // Escena y cámara
        this.scene = new THREE.Scene()
        this.scene.background = new THREE.Color(0x1a1a2e)

        this.camera = new THREE.PerspectiveCamera(
            45,
            canvas.clientWidth / canvas.clientHeight,
            0.01,
            100
        )
        this.camera.position.set(0, -2.5, 2)
        this.camera.lookAt(0, 0, 0)

        // OrbitControls — permite rotar la cámara con el mouse
        this.controls = new OrbitControls(this.camera, canvas)

        // Iluminación
        const ambient = new THREE.AmbientLight(0xffffff, 0.5)
        const dirLight = new THREE.DirectionalLight(0xffffff, 1)
        dirLight.position.set(2, 2, 4)
        this.scene.add(ambient, dirLight)

        // Map de bodies: id → Group de Three.js
        this.bodies = new Map()

        this._buildDohyo()
        this._startLoop()
    }

    _loadSTL(src, mat, group) {
        const url = `${src}`
        new STLLoader().load(url, geometry => {
            const mesh = new THREE.Mesh(geometry, mat)
            group.add(mesh)
        })
    }

    _buildDohyo() {
        // Cilindro: radiusTop, radiusBottom, height, segments
        const geo = new THREE.CylinderGeometry(0.77, 0.77, 0.05, 64)
        const tex = new THREE.TextureLoader().load('http://localhost:8000/assets/dohyo.PNG')
        const mat = new THREE.MeshStandardMaterial({ map: tex })
        const mesh = new THREE.Mesh(geo, mat)

        // En MuJoCo el cilindro tiene el eje Z hacia arriba
        // En Three.js el cilindro tiene el eje Y hacia arriba — rotamos 90°
        mesh.rotation.x = Math.PI / 2
        mesh.position.set(0, 0, 0.03)

        this.scene.add(mesh)
    }

    _buildGeom(geom,group) {
        let mat
        let geo

        if (geom.material && MATERIAL_TEXTURES[geom.material]) {
            // Tiene textura mapeada
            const tex = new THREE.TextureLoader().load(MATERIAL_TEXTURES[geom.material])
            mat = new THREE.MeshStandardMaterial({ map: tex })
        } else {
            // Sin textura, usar rgba
            const [r, g, b, a] = geom.rgba
            mat = new THREE.MeshStandardMaterial({
                color: new THREE.Color(r, g, b),
                opacity: a,
                transparent: a < 1
            })
        }

        switch (geom.type) {
            case 'box':
                // MuJoCo size = half-sizes → Three.js quiere tamaño completo
                geo = new THREE.BoxGeometry(
                    geom.size[0] * 2,
                    geom.size[1] * 2,
                    geom.size[2] * 2
                )
                return new THREE.Mesh(geo, mat)

            case 'sphere':
                geo = new THREE.SphereGeometry(geom.size[0], 16, 16)
                return new THREE.Mesh(geo, mat)

            case 'cylinder':
                // MuJoCo size = [radio, half-height]
                geo = new THREE.CylinderGeometry(
                    geom.size[0], geom.size[0],
                    geom.size[1] * 2,
                    32
                )
                // Mismo problema de ejes que el dohyo
                const cyl = new THREE.Mesh(geo, mat)
                cyl.rotation.y = Math.PI / 2
                return cyl

            case 'mesh':
                // STL es asíncrono — lo manejamos aparte
                this._loadSTL(geom.src, mat, group)
                console.log("Cargando STL:", geom.src)
                return null

            default:
                console.warn(`SceneManager: tipo desconocido '${geom.type}', ignorando`)
                return null
        }
    }

    _startLoop() {
        const animate = () => {
            requestAnimationFrame(animate)
            this.controls.update()
            this.renderer.render(this.scene, this.camera)
        }
        animate()
    }

    buildBodies(sceneDescription) {
        this.clearBodies()
        for (const body of sceneDescription) {
            const group = new THREE.Group()

            for (const geom of body.geoms) {
                // pos y quat son relativos al body en MuJoCo
                const mesh = this._buildGeom(geom,group)
                if (!mesh) continue

                mesh.position.set(geom.pos[0], geom.pos[1], geom.pos[2])
                // MuJoCo usa quaternion en orden [w, x, y, z]
                // Three.js usa [x, y, z, w] — hay que reordenar
                mesh.quaternion.set(geom.quat[1], geom.quat[3], geom.quat[2], geom.quat[0])
                group.add(mesh)
            }

            this.bodies.set(body.id, group)
            this.scene.add(group)
        }
    }

    updateBodies(bodies) {
        if (!bodies) return
        for (const [id, bodyData] of Object.entries(bodies)) { 
            const group = this.bodies.get(id)
            if (!group) continue

            group.position.set(bodyData.pos[0], bodyData.pos[1], bodyData.pos[2])
            group.quaternion.set(
                bodyData.quat[1],
                bodyData.quat[2],
                bodyData.quat[3],
                bodyData.quat[0]
            )
        }
    }
    clearBodies() {
        for (const group of this.bodies.values()) {
            this.scene.remove(group)
            // Liberar memoria de geometrías y materiales
            group.traverse(obj => {
                if (obj.isMesh) {
                    obj.geometry.dispose()
                    obj.material.dispose()
                }
            })
        }
        this.bodies.clear()
    }
}