<script>
  import { onMount } from "svelte";
  import { matchState } from "./lib/stores";
  import { connectWebSocket } from "./lib/websocket";

  let state;

  const unsubscribe = matchState.subscribe((value) => {
    state = value;
  });

  async function startMatch() {
    await fetch("http://localhost:3000/start", {
      method: "POST",
    });
  }

  onMount(() => {
    connectWebSocket();
  });
</script>

<main>
  <h1>Robot Sumo Tournament</h1>

  <button on:click={startMatch}> Start Match </button>

  <div class="scoreboard">
    <h2>Round {state?.round}</h2>
    <h3>Status: {state?.status}</h3>

    <div class="scores">
      <div>Robot A: {state?.scoreA}</div>
      <div>Robot B: {state?.scoreB}</div>
    </div>

    <div>Last Winner: {state?.lastRoundWinner}</div>
    <div>Match Winner: {state?.matchWinner}</div>
    <div>Elapsed: {state?.elapsed?.toFixed(2)}</div>
  </div>
</main>

<style>
  main {
    font-family: sans-serif;
    padding: 2rem;
  }

  .scoreboard {
    margin-top: 2rem;
    padding: 1rem;
    border: 1px solid #ccc;
  }

  .scores {
    display: flex;
    gap: 2rem;
    font-size: 1.5rem;
  }

  button {
    padding: 0.5rem 1rem;
    font-size: 1rem;
  }
</style>
