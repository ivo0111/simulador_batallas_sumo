<script>
  import { onMount } from "svelte";
  import { simState } from "./lib/stores";
  import { connectWebSocket } from "./lib/websocket";

  let state;
  simState.subscribe(v => state = v);

  onMount(() => connectWebSocket());
</script>

<main>
  <h1>MuJoCo Sumo</h1>
  <pre>{JSON.stringify(state, null, 2)}</pre>
</main>