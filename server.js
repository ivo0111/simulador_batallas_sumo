const express = require('express');
const { spawn } = require('child_process');
const net = require('net');
const WebSocket = require('ws');

const app = express();
app.use(express.json());

const HTTP_PORT = 3000;
const WS_PORT = 3001;

let webotsProcess = null;
let tcpClient = null;
let currentPort = 54000;

const wss = new WebSocket.Server({ port: WS_PORT });

function broadcast(data) {
    const msg = JSON.stringify(data);
    wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(msg);
        }
    });
}

function launchEngine(port) {
    return new Promise((resolve, reject) => {
        const command = `"webots"`; // ruta a webots.exe (o webots si está en PATH)
        const args = [
            '--batch',
            '--mode=fast',
            '--no-rendering',
            '.\\Sumo_webots\\worlds\\Simulador_Peleas_Sumo.wbt', // ruta al .wbt de webots
            `--port=${port}`
        ];

        webotsProcess = spawn(command, args, {
            shell: true,
            windowsHide: true
        });

        webotsProcess.on('exit', (code) => {
            broadcast({ type: 'ENGINE_EXIT', code });
        });

        setTimeout(() => resolve(), 2000);
    });
}

function connectTCP(port) {
    return new Promise((resolve, reject) => {
        tcpClient = new net.Socket();

        tcpClient.connect(port, '127.0.0.1', () => {
            console.log('Connected to engine TCP');
            resolve();
        });

        let buffer = '';

        tcpClient.on('data', (data) => {
            buffer += data.toString();

            let lines = buffer.split('\n');
            buffer = lines.pop();

            for (let line of lines) {
                if (line.trim().length === 0) continue;
                try {
                    const parsed = JSON.parse(line);
                    broadcast({ type: 'MATCH_EVENT', payload: parsed });
                } catch (e) {
                    console.error('Invalid JSON from engine:', line);
                }
            }
        });

        tcpClient.on('close', () => {
            broadcast({ type: 'ENGINE_DISCONNECTED' });
        });

        tcpClient.on('error', (err) => {
            console.error(err);
        });
    });
}

app.post('/start', async (req, res) => {
    try {
        await launchEngine(currentPort);
        await connectTCP(currentPort);

        res.json({ status: 'started' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/stop', (req, res) => {
    if (webotsProcess) {
        webotsProcess.kill();
        webotsProcess = null;
    }

    if (tcpClient) {
        tcpClient.destroy();
        tcpClient = null;
    }

    res.json({ status: 'stopped' });
});

app.listen(HTTP_PORT, () => {
    console.log(`HTTP API running on http://localhost:${HTTP_PORT}`);
});

console.log(`WebSocket running on ws://localhost:${WS_PORT}`);