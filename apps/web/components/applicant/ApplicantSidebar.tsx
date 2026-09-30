"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  BookOpen,
  FileText,
  User,
  Bell,
  LogOut,
  ChevronRight,
  ShieldCheck,
  Menu,
  X,
} from "lucide-react";
import { clearAuth, getStoredUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard",     label: "Dashboard",    icon: LayoutDashboard },
  { href: "/schemes",       label: "Schemes",      icon: BookOpen        },
  { href: "/applications",  label: "Applications", icon: FileText        },
  { href: "/profile",       label: "Profile",      icon: User            },
  { href: "/notifications", label: "Alerts",       icon: Bell, badge: true },
];

export function ApplicantSidebar() {
  const pathname = usePathname();
  const router   = useRouter();
  const user     = getStoredUser();
  const [unread, setUnread] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    fetchApi("/api/v1/notifications").then((res) => {
      if (res.data) setUnread(res.data.unread_count || 0);
    });
  }, []);

  const handleLogout = async () => {
    await fetchApi("/api/v1/auth/logout", { method: "POST" });
    clearAuth();
    router.push("/login");
  };

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(href + "/");

  /* ── Shared sidebar content (used in both desktop & mobile drawer) ── */
  const SidebarContent = () => (
    <>
      {/* Brand */}
      <div className="px-4 py-5 border-b border-blue-800/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-amber-400 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
            <ShieldCheck className="w-5 h-5 text-blue-900" />
          </div>
          <div>
            <div className="text-[11px] font-bold text-amber-300 uppercase tracking-widest leading-none">MoTA</div>
            <div className="text-xs font-semibold text-white leading-tight mt-0.5">Scholar Portal</div>
          </div>
        </div>
      </div>

      {/* User info */}
      <div className="px-4 py-4 border-b border-blue-800/50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-700 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            {user?.full_name?.[0]?.toUpperCase() || "A"}
          </div>
          <div className="min-w-0">
            <div className="text-xs font-semibold text-white truncate">{user?.full_name || "Applicant"}</div>
            <div className="text-[11px] text-blue-300 truncate">{user?.email || ""}</div>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon, badge }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              onClick={() => setDrawerOpen(false)}
              className={cn(
                "flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all duration-150",
                "min-h-[44px]", // touch target
                active
                  ? "bg-amber-400/10 text-amber-300 border border-amber-400/20"
                  : "text-blue-200 hover:bg-blue-800/50 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {badge && unread > 0 && (
                <span className="bg-red-500 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {unread > 9 ? "9+" : unread}
                </span>
              )}
              {active && <ChevronRight className="w-3.5 h-3.5 text-amber-300/60" />}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 pb-safe border-t border-blue-800/50 pt-3">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium text-red-300 hover:bg-red-900/30 hover:text-red-200 transition-colors min-h-[44px]"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
        <div className="mt-3 px-1 text-[10px] text-blue-500 leading-relaxed">
          Ministry of Tribal Affairs<br />
          Government of India
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* ══════════════════════════════════════════
          DESKTOP SIDEBAR (lg+) — always visible
          ════════════════════════════════════════ */}
      <aside className="hidden lg:flex fixed top-0 left-0 h-full w-64 bg-blue-950 flex-col z-40">
        <SidebarContent />
      </aside>

      {/* ══════════════════════════════════════════
          TABLET DRAWER (md–lg) — slide-in on demand
          ════════════════════════════════════════ */}
      {/* Hamburger trigger — shown only on md, hidden on lg */}
      <button
        aria-label="Open navigation"
        className="fixed top-3 left-3 z-50 hidden md:flex lg:hidden items-center justify-center w-11 h-11 bg-blue-900 text-white rounded-lg shadow-lg"
        onClick={() => setDrawerOpen(!drawerOpen)}
      >
        {drawerOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Tablet overlay */}
      {drawerOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 hidden md:block lg:hidden"
          onClick={() => setDrawerOpen(false)}
        />
      )}

      {/* Tablet drawer */}
      <aside
        className={cn(
          "fixed top-0 left-0 h-full w-72 bg-blue-950 flex flex-col z-40 sidebar-transition",
          "hidden md:flex lg:hidden",
          drawerOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>

      {/* ══════════════════════════════════════════
          MOBILE BOTTOM NAV BAR (< md)
          Thumb-first design — controls in thumb zone
          ════════════════════════════════════════ */}
      <nav
        className="bottom-nav fixed bottom-0 left-0 right-0 z-50 flex md:hidden bg-blue-950 border-t border-blue-800/60 pb-safe"
        aria-label="Mobile navigation"
      >
        {NAV_ITEMS.map(({ href, label, icon: Icon, badge }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex-1 flex flex-col items-center justify-center gap-1 pt-2 pb-1 relative",
                "min-h-[56px]", // generous touch target
                active ? "text-amber-400" : "text-blue-400"
              )}
            >
              <div className="relative">
                <Icon className="w-5 h-5" />
                {badge && unread > 0 && (
                  <span className="absolute -top-1 -right-1.5 bg-red-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                    {unread > 9 ? "9+" : unread}
                  </span>
                )}
              </div>
              <span className="text-[10px] font-medium leading-none">{label}</span>
              {active && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-amber-400 rounded-full" />
              )}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
