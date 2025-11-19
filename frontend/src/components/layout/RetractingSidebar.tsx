import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  FiHome,
  FiFileText,
  FiUsers,
  FiPackage,
  FiSettings,
  FiLogOut,
  FiChevronsRight,
} from "react-icons/fi";
import { motion } from "framer-motion";
import { useAuthStore } from "../../stores/authStore";
import { useLogout } from "../../hooks/useAuth";

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}

const navigation: NavigationItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: FiHome },
  { name: "Submissions", href: "/submissions", icon: FiFileText },
  { name: "Exit Interviews", href: "/exit-interviews", icon: FiUsers },
  { name: "Assets", href: "/assets", icon: FiPackage },
];

const adminNavigation: NavigationItem[] = [
  { name: "Admin", href: "/admin", icon: FiSettings, adminOnly: true },
];

export function RetractingSidebar() {
  const [open, setOpen] = useState(true);
  const { user } = useAuthStore();
  const logout = useLogout();

  return (
    <motion.nav
      layout
      className="sticky top-0 h-screen shrink-0 border-r border-gray-700 bg-gray-900 p-2"
      style={{
        width: open ? "240px" : "fit-content",
      }}
    >
      <TitleSection open={open} user={user} />

      <div className="space-y-1">
        {navigation.map((item) => (
          <NavItem
            key={item.name}
            item={item}
            open={open}
          />
        ))}

        {/* Admin Navigation - Only visible to admin users */}
        {user?.role === "admin" && (
          <>
            <div className="border-t border-gray-700 my-2"></div>
            {adminNavigation.map((item) => (
              <NavItem
                key={item.name}
                item={item}
                open={open}
              />
            ))}
          </>
        )}
      </div>

      <LogoutButton open={open} onLogout={logout} />
      <ToggleClose open={open} setOpen={setOpen} />
    </motion.nav>
  );
}

interface NavItemProps {
  item: NavigationItem;
  open: boolean;
}

function NavItem({ item, open }: NavItemProps) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.href}
      className={({ isActive }) =>
        `relative flex h-10 w-full items-center rounded-md transition-colors ${
          isActive
            ? "bg-gray-800 text-white"
            : "text-gray-400 hover:bg-gray-800 hover:text-white"
        }`
      }
    >
      {({ isActive }) => (
        <>
          <motion.div
            layout
            className="grid h-full w-10 place-content-center text-lg"
          >
            <Icon />
          </motion.div>
          {open && (
            <motion.span
              layout
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.125 }}
              className="text-sm font-medium"
            >
              {item.name}
            </motion.span>
          )}
        </>
      )}
    </NavLink>
  );
}

interface TitleSectionProps {
  open: boolean;
  user: any;
}

function TitleSection({ open, user }: TitleSectionProps) {
  return (
    <div className="mb-3 border-b border-gray-700 pb-3">
      <div className="flex cursor-pointer items-center justify-between rounded-md transition-colors hover:bg-gray-800">
        <div className="flex items-center gap-2">
          <Logo />
          {open && (
            <motion.div
              layout
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.125 }}
            >
              <span className="block text-xs font-semibold text-white">
                {user?.full_name || "HR User"}
              </span>
              <span className="block text-xs text-gray-400">
                {user?.role === "admin" ? "Admin" : "HR Team"}
              </span>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

function Logo() {
  return (
    <motion.div
      layout
      className="grid size-10 shrink-0 place-content-center rounded-md bg-gray-700 text-white font-bold text-lg"
    >
      HR
    </motion.div>
  );
}

interface LogoutButtonProps {
  open: boolean;
  onLogout: () => void;
}

function LogoutButton({ open, onLogout }: LogoutButtonProps) {
  return (
    <motion.button
      layout
      onClick={onLogout}
      className="relative flex h-10 w-full items-center rounded-md transition-colors text-gray-400 hover:bg-gray-800 hover:text-white mt-2"
    >
      <motion.div
        layout
        className="grid h-full w-10 place-content-center text-lg"
      >
        <FiLogOut />
      </motion.div>
      {open && (
        <motion.span
          layout
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.125 }}
          className="text-sm font-medium"
        >
          Logout
        </motion.span>
      )}
    </motion.button>
  );
}

interface ToggleCloseProps {
  open: boolean;
  setOpen: (value: boolean | ((prev: boolean) => boolean)) => void;
}

function ToggleClose({ open, setOpen }: ToggleCloseProps) {
  return (
    <motion.button
      layout
      onClick={() => setOpen((pv) => !pv)}
      className="absolute bottom-0 left-0 right-0 border-t border-gray-700 transition-colors hover:bg-gray-800"
    >
      <div className="flex items-center p-2">
        <motion.div
          layout
          className="grid size-10 place-content-center text-lg text-gray-400"
        >
          <FiChevronsRight
            className={`transition-transform ${open && "rotate-180"}`}
          />
        </motion.div>
        {open && (
          <motion.span
            layout
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.125 }}
            className="text-xs font-medium text-gray-400"
          >
            Hide
          </motion.span>
        )}
      </div>
    </motion.button>
  );
}
