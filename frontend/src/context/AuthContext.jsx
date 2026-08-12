import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [notifCount, setNotifCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await authAPI.me();
      setUser(data.user);
      setNotifCount(data.notif_count || 0);
    } catch {
      setUser(null);
      setNotifCount(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email, password) => {
    const { data } = await authAPI.login(email, password);
    setUser(data.user);
    setNotifCount(data.notif_count || 0);
    return data;
  };

  const signup = async (formData) => {
    const { data } = await authAPI.signup(formData);
    setUser(data.user);
    return data;
  };

  const logout = async () => {
    await authAPI.logout();
    setUser(null);
    setNotifCount(0);
  };

  return (
    <AuthContext.Provider value={{
      user,
      notifCount,
      loading,
      login,
      signup,
      logout,
      refreshUser,
      setNotifCount,
      isFounder: user?.role?.toLowerCase() === 'founder',
      isInvestor: user?.role?.toLowerCase() === 'investor',
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
