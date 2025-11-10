import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import type { LoginRequest, LoginResponse } from '../lib/types';
import { useAuthStore } from '../stores/authStore';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

export const useLogin = () => {
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const { data } = await api.post<LoginResponse>('/api/auth/login', credentials);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.access_token);
      toast.success('Login successful!');
      navigate('/dashboard');
    },
    onError: () => {
      toast.error('Invalid credentials. Please try again.');
    },
  });
};

export const useLogout = () => {
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  return () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };
};
