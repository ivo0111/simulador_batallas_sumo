import { simState, sceneInitState } from './stores.js';

let socket = null;

export function connectWebSocket() {
    socket = new WebSocket('ws://localhost:8000/ws');

    socket.onopen = () => console.log('Conectado a MuJoCo');

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'SCENE_INIT') {
            console.log('Bodies en SCENE_INIT:', data.scene.bodies.map(b => b.name))
            sceneInitState.set(data);
        } else if (data.type === 'SIM_STATE') {
            simState.set(data);
        }
    };

    socket.onclose = () => console.log('WebSocket cerrado');
}

export function closeWebSocket() {
    if (socket) socket.close();
}