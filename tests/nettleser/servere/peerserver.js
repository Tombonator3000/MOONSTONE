// Lokal PeerJS-server for nettlesertestene (i stedet for PeerJS Cloud).
// Port: PEER_PORT (standard 9000). Nettsiden bruker den med ?peer=127.0.0.1:9000.
const http = require('http');
const express = require('express');
const { ExpressPeerServer } = require('peer');
const port = Number(process.env.PEER_PORT || 9000);
const app = express();
const server = http.createServer(app);
app.use('/', ExpressPeerServer(server, { path: '/', allow_discovery: false }));
server.listen(port, '127.0.0.1', () => console.log('peer-server paa 127.0.0.1:' + port));
