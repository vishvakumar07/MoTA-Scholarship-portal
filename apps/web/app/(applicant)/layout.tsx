"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import { ApplicantSidebar } from "@/components/applicant/ApplicantSidebar";

export default function ApplicantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
    } else {
      setAuthorized(true);
    }
  }, [router]);

  if (!authorized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-900 border-t-transparent rounded-full animate-spin" />
          <div className="text-sm text-slate-500">Verifying session...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <ApplicantSidebar />

      {/*
        Content offset strategy:
        - Mobile  (< md): no left offset; bottom padding clears the bottom nav bar
        - Tablet  (md–lg): small left padding for the hamburger button; bottom nav gone
        - Desktop (lg+):  left offset by sidebar width (64 = 256px)
      */}
      <div className="lg:pl-64">
        <main
          className={[
            "max-w-6xl mx-auto",
            "px-4 sm:px-5 lg:px-6",           // horizontal padding
            "py-4 sm:py-6 lg:py-8",            // vertical padding
            "pt-4 md:pt-14 lg:pt-8",           // tablet: extra top for hamburger
            "pb-bottom-nav md:pb-8",            // mobile: clear bottom nav; desktop: normal
          ].join(" ")}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
