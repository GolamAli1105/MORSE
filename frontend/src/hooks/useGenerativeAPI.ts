/**
 * React Hook for Generative API
 * ==============================
 * 
 * Custom hook for easy API integration with React components
 */

import { useState, useCallback, useEffect } from 'react';
import { apiService, GenerateRequest, WebSocketService } from '../services/api';

export const useGenerativeAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<string>('');

  // Generate Content
  const generateContent = useCallback(async (request: GenerateRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiService.generateContent(request);
      setLoading(false);
      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Generation failed';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  // Generate Content with Streaming
  const generateContentStream = useCallback(async (
    request: GenerateRequest,
    onUpdate?: (event: any) => void
  ) => {
    setLoading(true);
    setError(null);
    setProgress('Starting...');
    
    try {
      await apiService.generateContentStream(request, (event) => {
        setProgress(event.message || '');
        if (onUpdate) onUpdate(event);
        
        if (event.event === 'complete') {
          setLoading(false);
        } else if (event.event === 'error') {
          setError(event.message);
          setLoading(false);
        }
      });
    } catch (err: any) {
      const errorMessage = err.message || 'Streaming failed';
      setError(errorMessage);
      setLoading(false);
      throw new Error(errorMessage);
    }
  }, []);

  // Submit Feedback
  const submitFeedback = useCallback(async (
    generationId: string,
    contentId: string,
    modality: string,
    rating: number,
    userId: string = 'demo_user',
    comment?: string
  ) => {
    try {
      await apiService.submitFeedback({
        user_id: userId,
        generation_id: generationId,
        content_id: contentId,
        modality,
        rating,
        comment,
      });
    } catch (err: any) {
      console.error('Failed to submit feedback:', err);
      throw err;
    }
  }, []);

  // Track Action
  const trackAction = useCallback(async (
    generationId: string,
    contentId: string,
    modality: string,
    actionType: 'download' | 'save' | 'share' | 'regenerate' | 'delete',
    userId: string = 'demo_user'
  ) => {
    try {
      await apiService.submitImplicitFeedback({
        user_id: userId,
        generation_id: generationId,
        content_id: contentId,
        modality,
        action_type: actionType,
      });
    } catch (err: any) {
      console.error('Failed to track action:', err);
    }
  }, []);

  // Get User Stats
  const getUserStats = useCallback(async (userId: string = 'demo_user') => {
    try {
      return await apiService.getUserStats(userId);
    } catch (err: any) {
      console.error('Failed to get user stats:', err);
      throw err;
    }
  }, []);

  return {
    loading,
    error,
    progress,
    generateContent,
    generateContentStream,
    submitFeedback,
    trackAction,
    getUserStats,
  };
};

// WebSocket Hook
export const useWebSocket = (onMessage: (data: any) => void) => {
  const [connected, setConnected] = useState(false);
  const [ws] = useState(() => new WebSocketService());

  useEffect(() => {
    ws.connect(
      (data) => {
        setConnected(true);
        onMessage(data);
      },
      (error) => {
        setConnected(false);
        console.error('WebSocket error:', error);
      }
    );

    return () => {
      ws.disconnect();
    };
  }, [ws, onMessage]);

  const sendMessage = useCallback((data: any) => {
    ws.send(data);
  }, [ws]);

  return { connected, sendMessage };
};
