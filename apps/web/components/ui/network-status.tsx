"use client";

import React, { useEffect, useState } from "react";
import { WifiOff, Wifi, RefreshCw } from "lucide-react";

export function NetworkStatusBanner() {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [showRestored, setShowRestored] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    setIsOnline(navigator.onLine);

    const handleOnline = () => {
      setIsOnline(true);
      setShowRestored(true);
      const timer = setTimeout(() => setShowRestored(false), 3500);
      return () => clearTimeout(timer);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowRestored(false);
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (isOnline && !showRestored) {
    return null;
  }

  if (showRestored) {
    return (
      <div className="bg-emerald-600 text-white text-xs font-semibold py-2 px-4 text-center flex items-center justify-center gap-2 shadow-md anim-fade-in no-print">
        <Wifi className="w-3.5 h-3.5" />
        <span>Connection Restored &bull; You are back online. Synchronized with MoTA portal.</span>
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="bg-amber-600 text-white text-xs font-medium py-2.5 px-4 text-center flex flex-wrap items-center justify-center gap-2.5 shadow-md anim-fade-in sticky top-0 z-50 no-print"
    >
      <div className="flex items-center gap-2 font-bold">
        <WifiOff className="w-4 h-4 animate-pulse" />
        <span>Working Offline:</span>
      </div>
      <span>No internet connection detected. Forms and document uploads will be stored temporarily.</span>
      <button
        onClick={() => window.location.reload()}
        className="underline font-bold hover:text-amber-100 flex items-center gap-1 ml-2"
      >
        <RefreshCw className="w-3 h-3" /> Check Connection
      </button>
    </div>
  );
}
