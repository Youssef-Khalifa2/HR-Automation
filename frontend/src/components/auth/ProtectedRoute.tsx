import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { MainLayout } from '../layout/MainLayout';

export const ProtectedRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <MainLayout>
      <Outlet />
    </MainLayout>
  );
};
