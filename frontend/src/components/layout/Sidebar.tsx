import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Users, Package, LogOut } from 'lucide-react';
import { useLogout } from '../../hooks/useAuth';
import { cn } from '../../lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Submissions', href: '/submissions', icon: FileText },
  { name: 'Exit Interviews', href: '/exit-interviews', icon: Users },
  { name: 'Assets', href: '/assets', icon: Package },
];

export function Sidebar() {
  const logout = useLogout();

  return (
    <div className="flex h-screen w-64 flex-col bg-gray-900 text-white">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-gray-800">
        <h1 className="text-xl font-bold">HR Co-Pilot</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-gray-800 p-4">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-400 transition-colors hover:bg-gray-800 hover:text-white"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </button>
      </div>
    </div>
  );
}
