import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './stores/authStore';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import SubmissionsPage from './pages/SubmissionsPage';
import ExitInterviewsPage from './pages/ExitInterviewsPage';
import AssetsPage from './pages/AssetsPage';
import PublicSubmissionPage from './pages/PublicSubmissionPage';
import AdminPage from './pages/AdminPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true, // Auto-refresh when switching tabs
      retry: 1,
      staleTime: 30 * 1000, // 30 seconds - reduced for better freshness
    },
  },
});

function App() {
  const initAuth = useAuthStore((state) => state.initAuth);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/submit" element={<PublicSubmissionPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/submissions" element={<SubmissionsPage />} />
            <Route path="/exit-interviews" element={<ExitInterviewsPage />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}

export default App;
