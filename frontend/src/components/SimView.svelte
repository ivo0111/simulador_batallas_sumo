<script>
    import { onMount, onDestroy } from "svelte";
    import { simState, sceneInitState } from "../lib/stores.js";
    import { SceneManager } from "../lib/three/SceneManager.js";
    import { buildSceneDescription } from "../lib/three/RobotBuilder.js";
    import { get } from 'svelte/store'
    import CodeUploader from "./CodeUploader.svelte";

    let canvas;
    let sceneManager;

    // Cuando llega SCENE_INIT, construimos la escena una sola vez
    const unsubscribeInit = sceneInitState.subscribe((data) => {
        if (!data?.scene || !sceneManager) return;
        const description = buildSceneDescription(data);
        sceneManager.buildBodies(description);
    });

    // Cuando llega SIM_STATE, actualizamos posiciones cada frame
    const unsubscribeSim = simState.subscribe((data) => {
        if (!data?.bodies || !sceneManager) return;
        sceneManager.updateBodies(data.bodies);
    });

    onMount(() => {
        sceneManager = new SceneManager(canvas);

        const data = get(sceneInitState)
        if (data?.scene) {
            sceneManager.buildBodies(buildSceneDescription(data))
        }
    });

    onDestroy(() => {
        unsubscribeInit();
        unsubscribeSim();
    });

    async function resetSim() {
        await fetch("http://localhost:8000/sim/reset", { method: "POST" });
    }
</script>

<div class="layout">
    <canvas bind:this={canvas} ></canvas>
    <div class="panel">
        <CodeUploader robotId="A" color="#cc2200" />
        <CodeUploader robotId="B" color="#0044cc" />
        <button class="reset-btn" on:click={resetSim}>↺ Reiniciar</button>
    </div>
</div>

<style>
    canvas {
        flex: 1;
        display: block;
        width: 100%;
        height: 100vh;
        display: block;
    }
    .layout {
        display: flex;
        width: 100%;
        height: 100vh;
    }
    .panel {
        width: 220px;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
        background: #111;
    }
    .reset-btn {
        margin-top: auto;
        padding: 0.6em;
        background: #333;
        color: white;
        border: 1px solid #555;
        border-radius: 6px;
        cursor: pointer;
        font-size: 1em;
    }
    .reset-btn:hover {
        background: #444;
        border-color: #888;
    }
</style>
