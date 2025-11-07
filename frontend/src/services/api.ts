/**
 * API Service for Backend Communication
 * =====================================
 * 
 * Handles all API calls to the FastAPI backend with proper error handling
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
    baseURL: API_URL,
    timeout: 60000, // 60 seconds for generation requests
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: false, // Set to true if using cookies
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        console.log('🚀 API Request:', config.method?.toUpperCase(), config.url);
        return config;
    },
    (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        console.log('✅ API Response:', response.status, response.config.url);
        return response;
    },
    (error: AxiosError) => {
        console.error('❌ Response Error:', error.message);

        if (error.response) {
            // Server responded with error
            console.error('Error Data:', error.response.data);
            console.error('Error Status:', error.response.status);
        } else if (error.request) {
            // Request made but no response
            console.error('No response received:', error.request);
        } else {
            // Error in request setup
            console.error('Request setup error:', error.message);
        }

        return Promise.reject(error);
    }
);

// API Types
export interface GenerateRequest {
    user_id: string;
    modality: 'text' | 'image' | 'music';
    prompt: string;
    style?: string;
    use_rag?: boolean;
    parameters?: Record<string, any>;
}

export interface GenerateResponse {
    generation_id: string;
    content_id: string;
    session_id: string;
    text?: string;
    image_data?: string;
    audio_data?: string;
    rag_enhanced?: boolean;
    rag_info?: any;
    generation_time?: number;
    model_used?: string;
}

export interface FeedbackRequest {
    user_id: string;
    generation_id: string;
    content_id: string;
    modality: string;
    rating: number;
    comment?: string;
}

export interface ImplicitFeedbackRequest {
    user_id: string;
    generation_id: string;
    content_id: string;
    modality: string;
    action_type: 'download' | 'save' | 'share' | 'regenerate' | 'delete';
    metadata?: Record<string, any>;
}

// API Methods
export const apiService = {
    // Health Check
    async healthCheck() {
        const response = await api.get('/health');
        return response.data;
    },

    // Generate Content
    async generateContent(request: GenerateRequest): Promise<GenerateResponse> {
        const response = await api.post<GenerateResponse>('/generate', request);
        return response.data;
    },

    // Generate Content with Streaming
    async generateContentStream(
        request: GenerateRequest,
        onProgress: (event: any) => void
    ): Promise<void> {
        const response = await fetch(`${API_URL}/generate/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
            throw new Error('No reader available');
        }

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());

            for (const line of lines) {
                try {
                    const event = JSON.parse(line);
                    onProgress(event);
                } catch (e) {
                    console.error('Failed to parse event:', e);
                }
            }
        }
    },

    // Submit Explicit Feedback
    async submitFeedback(request: FeedbackRequest) {
        const response = await api.post('/feedback/explicit', request);
        return response.data;
    },

    // Submit Implicit Feedback
    async submitImplicitFeedback(request: ImplicitFeedbackRequest) {
        const response = await api.post('/feedback/implicit', request);
        return response.data;
    },

    // Get User Stats
    async getUserStats(userId: string) {
        const response = await api.get(`/user/${userId}/stats`);
        return response.data;
    },

    // Get Best Content
    async getBestContent(userId: string, modality: string, limit: number = 10) {
        const response = await api.get(`/user/${userId}/best-content/${modality}`, {
            params: { limit },
        });
        return response.data;
    },

    // Start Fine-tuning
    async startFineTuning(userId: string, modality: string, minSamples: number = 20) {
        const response = await api.post('/finetune/start', {
            user_id: userId,
            modality,
            min_samples: minSamples,
        });
        return response.data;
    },

    // Get Fine-tuning Status
    async getFineTuningStatus(jobId: string) {
        const response = await api.get(`/finetune/status/${jobId}`);
        return response.data;
    },

    // Get Configuration
    async getConfig() {
        const response = await api.get('/config');
        return response.data;
    },
};

// WebSocket Connection
export class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;

    connect(onMessage: (data: any) => void, onError?: (error: Event) => void) {
        try {
            this.ws = new WebSocket(WS_URL);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📨 WebSocket message:', data);
                    onMessage(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                if (onError) onError(error);
            };

            this.ws.onclose = () => {
                console.log('❌ WebSocket disconnected');
                this.reconnect(onMessage, onError);
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            if (onError) onError(error as Event);
        }
    }

    private reconnect(onMessage: (data: any) => void, onError?: (error: Event) => void) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Reconnecting... Attempt ${this.reconnectAttempts}`);

            setTimeout(() => {
                this.connect(onMessage, onError);
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }

    send(data: any) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export default api;
