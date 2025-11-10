import { useAuthStore } from '../../stores/authStore';

export function Header() {
  const user = useAuthStore((state) => state.user);

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-white px-6 shadow-sm">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-semibold">Employee Offboarding Management</h2>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-sm">
          <p className="font-medium">{user?.full_name}</p>
          <p className="text-gray-500">{user?.role}</p>
        </div>
      </div>
    </header>
  );
}
