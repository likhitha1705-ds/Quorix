import React from "react";
import {
  Sun,
  Moon,
  Server,
  PanelRightOpen,
  PanelRightClose,
  ArrowRight,
} from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import { useTheme } from "@/hooks/useTheme";

export type NavTab = "overview" | "demo" | "evidence" | "comparison" | "architecture";

interface HeaderProps {
  currentNav: NavTab;
  onSelectNav: (tab: NavTab) => void;
  isRightPanelOpen: boolean;
  onToggleRightPanel: () => void;
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentNav,
  onSelectNav,
  isRightPanelOpen,
  onToggleRightPanel,
}) => {
  const { isOnline, isLoading } = useHealth();
  const { theme, toggleTheme } = useTheme();

  const navItems: { id: NavTab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "demo", label: "Demo" },
    { id: "evidence", label: "Evidence" },
    { id: "comparison", label: "Comparison" },
    { id: "architecture", label: "Architecture" },
  ];

  return (
    <header className="h-14 border-b border-[#E5DED3] bg-[#F5F1E8] px-4 sm:px-6 flex items-center justify-between z-20 sticky top-0 transition-colors">
      {/* Left: Branding */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => onSelectNav("overview")}
          className="flex items-center gap-3 text-left cursor-pointer group"
        >
          <div className="h-9 w-9 rounded-xl bg-[#6B2E46] flex items-center justify-center text-white font-bold text-lg tracking-wider group-hover:scale-105 transition-transform shadow-sm">
            Q
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-[#6B2E46] tracking-tight text-base">
                Quorix
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-[#B3BAAC]/25 text-[#6B2E46] border border-[#B3BAAC]/40 hidden sm:inline-block">
                Intelligence Engine
              </span>
            </div>
            <p className="text-[11px] text-[#5E5E5E] hidden xl:block">
              Intelligent Context Selection & Retrieval Optimization
            </p>
          </div>
        </button>
      </div>

      {/* Center: Navigation (Muted Sage Grey background, White active pill) */}
      <nav className="hidden md:flex items-center gap-1 p-1 bg-[#B3BAAC] rounded-xl text-xs font-medium">
        {navItems.map((item) => {
          const isActive = currentNav === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectNav(item.id)}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer font-medium ${
                isActive
                  ? "bg-white text-[#6B2E46] shadow-sm font-semibold"
                  : "text-[#1F1F1F] hover:bg-[#C5CCC0]"
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Right: Controls & Status */}
      <div className="flex items-center gap-2.5">
        {/* Mobile Navigation Dropdown Button */}
        <div className="flex md:hidden">
          <select
            value={currentNav}
            onChange={(e) => onSelectNav(e.target.value as NavTab)}
            className="text-xs bg-[#B3BAAC] border border-[#B3BAAC] rounded-lg px-2 py-1 text-[#1F1F1F]"
          >
            {navItems.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        {/* Backend Status Pill */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-white transition-colors ${
            isLoading
              ? "text-[#5E5E5E] border-[#E5DED3]"
              : isOnline
              ? "text-[#1F1F1F] border-[#E5DED3]"
              : "text-[#6B2E46] border-[#6B2E46]/30"
          }`}
          title={isOnline ? "Backend Connected (FastAPI)" : "Backend Offline"}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              isLoading
                ? "bg-[#B3BAAC] animate-pulse"
                : isOnline
                ? "bg-[#6B2E46]"
                : "bg-rose-500"
            }`}
          />
          <Server className="h-3 w-3 text-[#6B2E46]" />
          <span className="hidden lg:inline">
            {isLoading ? "Checking API..." : isOnline ? "Backend Live" : "API Offline"}
          </span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-[#5E5E5E] hover:text-[#1F1F1F] hover:bg-[#B3BAAC]/20 transition-colors cursor-pointer"
          aria-label="Toggle theme"
          title={`Switch theme`}
        >
          {theme === "dark" ? <Sun className="h-4 w-4 text-[#6B2E46]" /> : <Moon className="h-4 w-4 text-[#6B2E46]" />}
        </button>

        {/* Action Button: Demo Toggle or Launch Demo */}
        {currentNav === "demo" ? (
          <button
            onClick={onToggleRightPanel}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              isRightPanelOpen
                ? "bg-[#6B2E46] text-white shadow-sm"
                : "bg-white border border-[#E5DED3] text-[#6B2E46] hover:bg-[#F5F1E8]"
            }`}
            title="Toggle Pipeline Inspector Panel"
          >
            {isRightPanelOpen ? (
              <>
                <PanelRightClose className="h-4 w-4" />
                <span className="hidden sm:inline">Hide Inspector</span>
              </>
            ) : (
              <>
                <PanelRightOpen className="h-4 w-4" />
                <span className="hidden sm:inline">Inspect Pipeline</span>
              </>
            )}
          </button>
        ) : (
          <button
            onClick={() => onSelectNav("demo")}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#6B2E46] hover:bg-[#57263A] text-white shadow-sm transition-all cursor-pointer group"
          >
            <span>Run Demo</span>
            <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        )}
      </div>
    </header>
  );
};
