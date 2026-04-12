<script>
    import { onMount, onDestroy } from "svelte";
    import { simState, sceneInitState } from "../lib/stores.js";
    import { SceneManager } from "../lib/three/SceneManager.js";
    import { buildSceneDescription } from "../lib/three/RobotBuilder.js";
    import { get } from 'svelte/store'

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
</script>

<!-- svelte-ignore element_invalid_self_closing_tag -->
<canvas bind:this={canvas} />

<style>
    canvas {
        width: 100%;
        height: 100vh;
        display: block;
    }
</style>
