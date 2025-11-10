import { io } from 'socket.io-client';

// Automatically detect current host and use port 5001
const getBackendURL = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const hostname = window.location.hostname;
    const backendURL = `${protocol}//${hostname}:5001`;
    console.log('🔗 Backend URL:', backendURL);
    return backendURL;
  }
  return 'http://localhost:5001';
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
    if (this.socket?.connected) {
      console.log('✅ Already connected');
      return;
    }

    console.log('🔌 Connecting to WebSocket:', BACKEND_URL);

    this.socket = io(BACKEND_URL, {
      transports: ['polling', 'websocket'], // Try polling first, then upgrade to websocket
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,
      timeout: 20000,
      autoConnect: true,
      forceNew: false,
      multiplex: true,
      withCredentials: false,
      upgrade: true,
      rememberUpgrade: true,
      path: '/socket.io/'
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket Connected - ID:', this.socket.id);
      this.listeners.connect.forEach(cb => cb());
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket Disconnected:', reason);
      this.listeners.disconnect.forEach(cb => cb());
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ Connection Error:', error.message);
      console.error('Full error:', error);
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('🔄 Reconnected after', attemptNumber, 'attempts');
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('🔄 Reconnection attempt:', attemptNumber);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('❌ Reconnection Error:', error.message);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('❌ Reconnection Failed - giving up');
    });

    this.socket.on('score_update', (data) => {
      console.log('📊 Score update received for:', data.symbol);
      this.listeners.score_update.forEach(cb => cb(data));
    });

    this.socket.on('alert', (data) => {
      console.log('🔔 Alert received:', data.type, 'for', data.symbol);
      this.listeners.alert.forEach(cb => cb(data));
    });
  }

  disconnect() {
    if (this.socket) {
      console.log('🔌 Disconnecting WebSocket');
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event, callback) {
    if (this.listeners[event]) {
      if (!this.listeners[event].includes(callback)) {
        this.listeners[event].push(callback);
      }
    }
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event, data) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('⚠️ Socket not connected, cannot emit:', event);
    }
  }
}

export default new WebSocketService();