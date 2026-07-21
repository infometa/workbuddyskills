import { useState, useEffect, useCallback } from 'react';
import { Session, Message } from '../types';

const STORAGE_KEYS = {
  sessionModels: 'sessionModels',
};

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  
  // 每个会话的模型选择缓存
  const [sessionModels, setSessionModels] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.sessionModels);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // 获取当前会话
  const currentSession = sessions.find(s => s.id === currentSessionId);

  // 从 API 加载会话列表
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      
      if (data.sessions) {
        const loadedSessions: Session[] = data.sessions.map((s: any) => ({
          id: s.id,
          title: s.title,
          model: s.model,
          createdAt: new Date(s.created_at),
          messages: []
        }));
        setSessions(loadedSessions);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  }, []);

  // 加载单个会话的消息
  const loadSessionMessages = useCallback(async (sessionId: string) => {
    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      const data = await res.json();
      
      if (data.messages) {
        const messages: Message[] = data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          model: m.model,
          timestamp: new Date(m.created_at),
          toolCalls: m.tool_calls || undefined
        }));
        
        setSessions(prev => prev.map(s => 
          s.id === sessionId ? { ...s, messages } : s
        ));
      }
    } catch (error) {
      console.error('Failed to load session messages:', error);
    }
  }, []);

  // 删除会话
  const deleteSession = useCallback(async (sessionId: string): Promise<string | null> => {
    try {
      await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      
      let navigateTo: string | null = null;
      
      setSessions(prev => {
        const filtered = prev.filter(s => s.id !== sessionId);
        return filtered;
      });
      
      // 返回需要导航到的位置
      const remaining = sessions.filter(s => s.id !== sessionId);
      if (currentSessionId === sessionId) {
        if (remaining.length > 0) {
          navigateTo = `/chat/${remaining[0].id}`;
          setCurrentSessionId(remaining[0].id);
        } else {
          navigateTo = '/';
          setCurrentSessionId(null);
        }
      }
      
      return navigateTo;
    } catch (error) {
      console.error('Failed to delete session:', error);
      return null;
    }
  }, [sessions, currentSessionId]);

  // 保存每个会话的模型选择到 localStorage
  const updateSessionModel = useCallback((sessionId: string, modelId: string) => {
    setSessionModels(prev => {
      const updated = { ...prev, [sessionId]: modelId };
      localStorage.setItem(STORAGE_KEYS.sessionModels, JSON.stringify(updated));
      return updated;
    });
    setSessions(prev => prev.map(s => 
      s.id === sessionId ? { ...s, model: modelId } : s
    ));
  }, []);

  // 添加新会话
  const addSession = useCallback((session: Session) => {
    setSessions(prev => [session, ...prev]);
    setCurrentSessionId(session.id);
  }, []);

  // 更新会话
  const updateSession = useCallback((sessionId: string, updates: Partial<Session>) => {
    setSessions(prev => prev.map(s => 
      s.id === sessionId ? { ...s, ...updates } : s
    ));
  }, []);

  // 更新会话消息
  const updateSessionMessages = useCallback((sessionId: string, updater: (messages: Message[]) => Message[]) => {
    setSessions(prev => prev.map(s => 
      s.id === sessionId ? { ...s, messages: updater(s.messages) } : s
    ));
  }, []);

  // 当切换会话时，加载该会话的消息
  useEffect(() => {
    if (currentSessionId) {
      const session = sessions.find(s => s.id === currentSessionId);
      if (session && session.messages.length === 0) {
        loadSessionMessages(currentSessionId);
      }
    }
  }, [currentSessionId, sessions, loadSessionMessages]);

  return {
    sessions,
    setSessions,
    currentSessionId,
    setCurrentSessionId,
    currentSession,
    sessionModels,
    fetchSessions,
    loadSessionMessages,
    deleteSession,
    updateSessionModel,
    addSession,
    updateSession,
    updateSessionMessages,
  };
}
