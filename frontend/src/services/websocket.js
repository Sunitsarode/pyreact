import { io } from 'socket.io-client';

// Automatically detect current host and use port 5001
const getBackendURL = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol; // http: or https:
    const hostname = window.location.hostname; // 64.227.183.105 or localhost
    return `${protocol}//${hostname}:5001`;
  }
  return 'http://localhost:5001'; // Fallback
};

const BACKEND_URL = getBackendURL();

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

    console.log('🔌 Connecting to WebSocket:', BACKEND_URL);

    this.socket = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      withCredentials: false
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket Connected');
      this.listeners.connect.forEach(cb => cb());
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket Disconnected:', reason);
      this.listeners.disconnect.forEach(cb => cb());
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ Connection Error:', error.message);
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