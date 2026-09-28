import { useState } from "react";
import { LogOut, ChevronDown } from "lucide-react";
import { useAuth } from "../context/AuthContext"; // adjust path

export default function HeaderWithUserProfile({ user }) {
  const { logout } = useAuth();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const getInitials = () => {
    if (!user) return "??";
    const name = user.name || user.email || "";
    const parts = name.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : (name.charAt(0) || "?").toUpperCase();
  };
  

  const displayName = user?.name || user?.email?.split('@')[0] || 'User';

  return (
    <header className="sticky top-0 z-30 w-full border-b border-gray-200/80 dark:border-gray-800/50 
                       bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl shadow-sm">
      <div className="flex items-center justify-between px-6 py-3.5">
        {/* Left side - Logo/Title (optional) */}
        <div className="flex items-center gap-3">
          <h1 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            MindVault
          </h1>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-3">
          {/* User Profile Menu */}
          <div className="relative">
            <button
              onClick={() => {
                setShowProfileMenu(!showProfileMenu);
              }}
              className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-100 
                         dark:hover:bg-gray-800/80 transition-all duration-200 group"
            >
              <div className="w-9 h-9 rounded-xl bg-indigo-600
                             flex items-center justify-center text-white font-semibold text-sm shadow-lg 
                             shadow-indigo-500/25 ring-2 ring-white/20 dark:ring-white/10">
                {getInitials()}
              </div>
              <span className="hidden sm:inline font-medium text-gray-700 dark:text-gray-200 
                             group-hover:text-gray-900 dark:group-hover:text-white transition-colors">
                {displayName}
              </span>
              <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 
                                     ${showProfileMenu ? 'rotate-180' : ''}`} />
            </button>

            {/* Profile Dropdown */}
            {showProfileMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-900 rounded-xl 
                             shadow-2xl border border-gray-200 dark:border-gray-800 overflow-hidden
                             animate-in fade-in slide-in-from-top-2 duration-200">
                {/* User Info */}
                <div className="p-4 border-b border-gray-200 dark:border-gray-800">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-indigo-600
                                   flex items-center justify-center text-white font-semibold shadow-lg 
                                   shadow-indigo-500/25 ring-2 ring-white/20 dark:ring-white/10">
                      {getInitials()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                        {displayName}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                        {user?.email}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Logout */}
                <div className="p-2">
                  <button
                    onClick={() => logout()}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg 
                             hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors 
                             text-red-600 dark:text-red-400 group"
                  >
                    <LogOut className="w-4 h-4" strokeWidth={2} />
                    <span className="text-sm font-medium">Sign out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
