"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getStoredUser, clearAuth, User } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { BookOpen, User as UserIcon, LogOut, Menu, X, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export function Header() {
  const router   = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]); // re-read on navigation

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Close mobile menu on outside click
  useEffect(() => {
    if (!mobileMenuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMobileMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [mobileMenuOpen]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileMenuOpen]);

  const handleLogout = () => {
    clearAuth();
    setUser(null);
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur shadow-sm" ref={menuRef}>

      {/* ── Government top bar ─────────────────────────────────── */}
      <div className="bg-slate-900 text-slate-200 text-xs py-1.5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-2 truncate">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
            {/* Abbreviated on very small screens */}
            <span className="hidden xs:inline">भारत सरकार | Government of India</span>
            <span className="xs:hidden">Govt. of India</span>
          </div>
          <div className="hidden sm:flex items-center gap-4 text-slate-300 flex-shrink-0">
            <a
              href="https://tribal.nic.in"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-amber-400 transition-colors"
            >
              tribal.nic.in
            </a>
            <span aria-hidden>·</span>
            <a
              href="https://dbttribal.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-amber-400 transition-colors"
            >
              DBT Tribal
            </a>
          </div>
        </div>
      </div>

      {/* ── Main header row ─────────────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16 sm:h-20">

        {/* Logo + title */}
        <Link href="/" className="flex items-center gap-2 sm:gap-3 group min-w-0">
          <div className="w-10 h-10 sm:w-12 sm:h-12 flex-shrink-0 rounded-lg bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-6 h-6 sm:w-7 sm:h-7 text-amber-400" />
          </div>
          <div className="min-w-0">
            {/* Hindi subtitle — hide on very small screens to avoid overflow */}
            <div className="hidden sm:block text-[10px] sm:text-xs font-semibold text-amber-700 tracking-wider uppercase truncate">
              जनजातीय कार्य मंत्रालय
            </div>
            <div className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight leading-tight truncate">
              Ministry of Tribal Affairs
            </div>
            <div className="hidden sm:block text-[10px] text-slate-500 font-medium truncate">
              AI-Enabled Scholarship &amp; Fellowship Management System
            </div>
          </div>
        </Link>

        {/* Desktop navigation (md+) */}
        <nav className="hidden md:flex items-center gap-6">
          <Link
            href="/"
            className="text-sm font-medium text-slate-700 hover:text-blue-900 transition-colors min-h-[44px] flex items-center"
          >
            Home
          </Link>
          <Link
            href="/schemes"
            className="text-sm font-medium text-slate-700 hover:text-blue-900 transition-colors flex items-center gap-1.5 min-h-[44px]"
          >
            <BookOpen className="w-4 h-4" />
            Schemes
          </Link>

          {user ? (
            <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
              <Link href="/dashboard">
                <Button variant="outline" size="sm" className="flex items-center gap-1.5 min-h-[44px]">
                  <UserIcon className="w-4 h-4" />
                  Dashboard
                </Button>
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-red-600 hover:text-red-700 hover:bg-red-50 flex items-center gap-1.5 min-h-[44px]"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
              <Link href="/login">
                <Button variant="outline" size="sm" className="min-h-[44px]">Login</Button>
              </Link>
              <Link href="/register">
                <Button variant="motaPrimary" size="sm" className="min-h-[44px]">Register</Button>
              </Link>
            </div>
          )}
        </nav>

        {/* Mobile hamburger button (< md) */}
        <button
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((o) => !o)}
          className="flex md:hidden items-center justify-center w-11 h-11 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* ── Mobile menu dropdown (< md) ─────────────────────────── */}
      <div
        className={cn(
          "md:hidden border-t bg-white overflow-hidden transition-all duration-200 ease-in-out",
          mobileMenuOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="px-4 py-3 space-y-1">
          <Link
            href="/"
            className="flex items-center h-11 px-3 rounded-lg text-base font-medium text-slate-700 hover:bg-slate-50"
          >
            Home
          </Link>
          <Link
            href="/schemes"
            className="flex items-center h-11 px-3 rounded-lg text-base font-medium text-slate-700 hover:bg-slate-50 gap-2"
          >
            <BookOpen className="w-4 h-4" />
            Schemes
          </Link>

          {user ? (
            <>
              <Link
                href="/dashboard"
                className="flex items-center h-11 px-3 rounded-lg text-base font-medium text-blue-900 hover:bg-blue-50 gap-2"
              >
                <UserIcon className="w-4 h-4" />
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center h-11 px-3 rounded-lg text-base font-medium text-red-600 hover:bg-red-50 gap-2"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </>
          ) : (
            <div className="pt-2 pb-1 flex flex-col gap-2">
              <Link href="/login">
                <Button variant="outline" className="w-full min-h-[44px]">Login</Button>
              </Link>
              <Link href="/register">
                <Button variant="motaPrimary" className="w-full min-h-[44px]">Register</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
