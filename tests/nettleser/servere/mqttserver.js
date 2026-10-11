// Lokal MQTT-megler over WebSocket for nettlesertestene (i stedet for HiveMQ), til romlisten.
// Port: MQTT_PORT (standard 8883). Nettsiden bruker den med ?mqtt=ws://127.0.0.1:8883/mqtt&mqttv=4.
const aedes = require('aedes')();
const http = require('http');
const { WebSocketServer, createWebSocketStream } = require('ws');
const port = Number(process.env.MQTT_PORT || 8883);
const server = http.createServer();
const wss = new WebSocketServer({ server, path: '/mqtt' });
wss.on('connection', (ws) => aedes.handle(createWebSocketStream(ws)));
server.listen(port, '127.0.0.1', () => console.log('mqtt ws paa 127.0.0.1:' + port));
