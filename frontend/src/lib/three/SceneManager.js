// src/lib/three/SceneManager.js
import * as THREE from 'three'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

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