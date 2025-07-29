import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../services/api';
import toast from 'react-hot-toast';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      
      login: async (credentials) => {
        set({ isLoading: true });
        try {
          const response = await api.login(credentials);
          const { access_token, user } = response.data;
          
          localStorage.setItem('authToken', access_token);
          
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          toast.success('Login successful!');
          return { success: true };
        } catch (error) {
          set({ isLoading: false });
          const message = error.response?.data?.error || 'Login failed';
          toast.error(message);
          return { success: false, error: message };
        }
      },
      
      register: async (userData) => {
        set({ isLoading: true });
        try {
          const response = await api.register(userData);
          set({ isLoading: false });
          toast.success('Registration successful! Please login.');
          return { success: true };
        } catch (error) {
          set({ isLoading: false });
          const message = error.response?.data?.error || 'Registration failed';
          toast.error(message);
          return { success: false, error: message };
        }
      },
      
      logout: () => {
        localStorage.removeItem('authToken');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
        toast.success('Logged out successfully');
      },
      
      updateProfile: async (profileData) => {
        try {
          const response = await api.getProfile();
          set({ user: response.data });
          return { success: true };
        } catch (error) {
          const message = error.response?.data?.error || 'Profile update failed';
          toast.error(message);
          return { success: false, error: message };
        }
      },
      
      checkAuth: async () => {
        const token = localStorage.getItem('authToken');
        if (!token) {
          return false;
        }
        
        try {
          const response = await api.getProfile();
          set({
            user: response.data,
            token,
            isAuthenticated: true,
          });
          return true;
        } catch (error) {
          localStorage.removeItem('authToken');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
      getStorage: () => localStorage,
    }
  )
);
