<script>
  import { onMount } from 'svelte'
  import { connectWebSocket } from './lib/websocket.js'
  import SimView from './components/SimView.svelte'

  onMount(() => connectWebSocket())
</script>

<SimView />