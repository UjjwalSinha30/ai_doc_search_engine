import { useState } from "react";
import {
  X,
  FileText,
  ChevronDown,
  LayoutDashboard,
} from "lucide-react";
import DarkModeToggle from "./DarkModeToggle";
import DocumentList from "./DocumentList";

export default function Sidebar({
  closeSidebar,
  onDocumentSelect,
  documentsVersion = 0,
}) {
  const [showDocuments, setShowDocuments] = useState(true); // default open = better UX

  const mainNavItems = [
    {
      name: "Dashboard",
      icon: LayoutDashboard,
      href: "/",
      active: true, // you can make this dynamic later
    },
    { name: "Documents", icon: FileText, isCollapsible: true },
  ];

  return (
    <aside
      className={`
        w-[280px] h-full
        bg-white dark:bg-gray-950
        border-r border-gray-200 dark:border-gray-800
        flex flex-col
        transition-all duration-300 ease-in-out
        overflow-hidden
      `}
    >
      {/* Header / Brand */}
      <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="
                h-9 w-9 rounded-xl
                bg-indigo-600
                flex items-center justify-center text-white
                font-semibold text-sm
              "
            >
              MV
            </div>

            <h2
              className="
                text-lg font-semibold tracking-tight
                text-gray-900 dark:text-gray-100
              "
            >
              MindVault
            </h2>
          </div>

          {/* Mobile close button */}
          <button
            className="lg:hidden p-2.5 rounded-xl hover:bg-gray-100/80 dark:hover:bg-gray-800/60 transition-colors"
            onClick={closeSidebar}
            aria-label="Close sidebar"
          >
            <X size={22} />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600">
        {mainNavItems.map((item) => {
          const Icon = item.icon;

          if (item.isCollapsible) {
            return (
              <div key={item.name} className="space-y-1">
                {/* Collapsible trigger */}
                <button
                  onClick={() => setShowDocuments(!showDocuments)}
                  className={`
                    group flex items-center justify-between w-full px-3 py-2.5 rounded-lg
                    text-sm font-medium transition-all duration-200
                    ${
                      showDocuments
                        ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300"
                        : "text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-900"
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      size={18}
                      className={`
                        transition-colors
                        ${showDocuments
                          ? "text-indigo-600 dark:text-indigo-400"
                          : "text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400"}
                      `}
                    />
                    <span>{item.name}</span>
                  </div>

                  <ChevronDown
                    size={16}
                    className={`
                      transition-transform duration-300
                      ${showDocuments ? "rotate-180" : ""}
                      ${showDocuments ? "text-indigo-600" : "text-gray-400 group-hover:text-indigo-600"}
                    `}
                  />
                </button>

                {/* Animated documents list */}
                <div
                  className={`
                    overflow-hidden transition-all duration-400 ease-in-out
                    ${showDocuments ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"}
                  `}
                >
                  <div className="ml-4 border-l border-gray-200 dark:border-gray-800 pl-5 pr-2 py-2">
                    <DocumentList
                      onDocumentSelect={onDocumentSelect}
                      documentsVersion={documentsVersion}
                    />
                  </div>
                </div>
              </div>
            );
          }

          return (
            <a
              key={item.name}
              href={item.href}
              className={`
                group flex items-center gap-3 px-3 py-2.5 rounded-lg
                text-sm font-medium transition-all duration-200
                ${
                  item.active
                    ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-300"
                    : "text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-900"
                }
              `}
            >
              <Icon
                size={18}
                className={`
                  transition-colors
                  ${
                    item.active
                      ? "text-indigo-600 dark:text-indigo-400"
                      : "text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400"
                  }
                `}
              />
              <span>{item.name}</span>
            </a>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-800 mt-auto">
        <div className="flex items-center">
          <DarkModeToggle />
        </div>
      </div>
    </aside>
  );
}
