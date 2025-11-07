import { io } from 'socket.io-client';

const BACKEND_URL = 'http://localhost:5001';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = {
      score_update: [],
      alert: [],
      connect: [],
      disconnect: []
    };
  }

  connect() {
    if (this.socket?.connected) return;

    this.socket = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket Connected');
      this.listeners.connect.forEach(cb => cb());
    });

    this.socket.on('disconnect', () => {
      console.log('❌ WebSocket Disconnected');
      this.listeners.disconnect.forEach(cb => cb());
    });

    this.socket.on('score_update', (data) => {
      this.listeners.score_update.forEach(cb => cb(data));
    });

    this.socket.on('alert', (data) => {
      this.listeners.alert.forEach(cb => cb(data));
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }
}

export default new WebSocketService();
