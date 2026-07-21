// The simplest possible WebSocket client
const WebSocket = require('ws');

console.log('=== STARTING ULTRA SIMPLE WEBSOCKET CLIENT ===');

const ws = new WebSocket('ws://localhost:9080');

ws.on('open', function() {
  console.log('Connected successfully!');
  ws.send('Hello from Node.js client!');
  console.log('Message sent');
});

ws.on('message', function(data) {
  console.log('Received:', data.toString());
  console.log('Test successful! Closing...');
  ws.close();
});

ws.on('error', function(error) {
  console.error('ERROR:', error.message);
});

ws.on('close', function(code, reason) {
  console.log('Connection closed. Code:', code, 'Reason:', reason || 'No reason');
  process.exit(0);
});

console.log('Client initialized, waiting for connection...');

// Exit after 10 seconds if nothing happens
setTimeout(() => {
  console.log('Timeout reached, exiting...');
  process.exit(1);
}, 10000);