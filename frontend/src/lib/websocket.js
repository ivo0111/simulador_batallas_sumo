import { matchState } from './stores.js';

let socket = null;

export function connectWebSocket() {
    socket = new WebSocket('ws://localhost:3001');

    socket.onopen = () => {
        console.log('Connected to backend');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'MATCH_EVENT') {
            matchState.set(data.payload);
        }
    };

    socket.onclose = () => {
        console.log('WebSocket closed');
    };
}

export function closeWebSocket() {
    if (socket) socket.close();
}