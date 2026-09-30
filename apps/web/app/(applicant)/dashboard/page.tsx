"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/utils";
import { getStoredUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  FileText, ArrowRight, Bell, CheckCircle2, AlertTriangle,
  Clock, BookOpen, User, RefreshCw, ShieldCheck, ChevronRight, Award, XCircle
} from "lucide-react";

const STATUS_CONFIG: Record<string, { variant: "default" | "secondary" | "destructive" | "urgent" | "success" | "warning" | "motaCSS" | "motaCentralSector"; label: string; icon: React.ElementType }> = {
  draft: { variant: "secondary", label: "Draft", icon: FileText },
  submitted: { variant: "motaCSS", label: "Submitted", icon: Clock },
  document_processing: { variant: "motaCSS", label: "Processing", icon: RefreshCw },
  document_verification: { variant: "motaCentralSector", label: "Verification", icon: ShieldCheck },
  deficiency: { variant: "urgent", label: "Action Required", icon: AlertTriangle },
  resubmitted: { variant: "warning", label: "Resubmitted", icon: RefreshCw },
  eligibility_review: { variant: "warning", label: "Eligibility Review", icon: CheckCircle2 },
  eligible: { variant: "success", label: "Eligible", icon: CheckCircle2 },
  ineligible: { variant: "destructive", label: "Ineligible", icon: XCircle },
  scrutiny: { variant: "motaCSS", label: "Scrutiny", icon: BookOpen },
  shortlisted: { variant: "motaCentralSector", label: "Shortlisted", icon: Award },
  selected: { variant: "success", label: "Selected", icon: Award },
  not_selected: { variant: "secondary", label: "Not Selected", icon: XCircle },
  completed: { variant: "success", label: "Completed", icon: CheckCircle2 },
  withdrawn: { variant: "secondary", label: "Withdrawn", icon: XCircle },
};

interface Application {
  id: string;
  reference_number: string | null;
  status: string;
  submitted_at: string | null;
  scheme_code: string | null;
  scheme_name: string | null;
}

interface Notification {
  id: string;
  title: string;
  body: string;
  read_at: string | null;
  created_at: string;
}

export default function DashboardPage() {
  const user = getStoredUser();
  const [applications, setApplications] = useState<Application[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchApi("/api/v1/applications"),
      fetchApi("/api/v1/notifications"),
      fetchApi("/api/v1/applicant/profile"),
    ]).then(([appsRes, notifsRes, profileRes]) => {
      if (appsRes.data) setApplications(appsRes.data.applications || []);
      if (notifsRes.data) {
        setNotifications((notifsRes.data.notifications || []).slice(0, 3));
        setUnread(notifsRes.data.unread_count || 0);
      }
      if (profileRes.data) setProfile(profileRes.data);
      setLoading(false);
    });
  }, []);

  const activeApps = applications.filter((a) => !["completed", "withdrawn", "not_selected"].includes(a.status));
  const deficiencies = applications.filter((a) => a.status === "deficiency");
  const pendingActions = deficiencies.length + (profile && !profile.is_profile_complete ? 1 : 0);



  return (
    <div className="space-y-6 break-anywhere">
      {/* Welcome Banner - Hero Entrance */}
      <div className="anim-fade-in relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-950 via-blue-900 to-indigo-900 text-white p-6 sm:p-8 shadow-xl transition-all">
        <div className="absolute -right-8 -top-8 w-44 h-44 bg-white/5 rounded-full pointer-events-none blur-sm" />
        <div className="absolute -right-4 top-20 w-28 h-28 bg-amber-400/10 rounded-full pointer-events-none blur-sm" />

        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2.5 max-w-2xl">
            <div className="inline-flex items-center gap-2 text-xs font-semibold text-amber-300 bg-amber-400/10 border border-amber-400/25 rounded-full px-3 py-1 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              MoTA National Tribal Scholar Portal &bull; Verified Session
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Namaste, {user?.full_name || "Applicant"}
            </h1>
            <p className="text-sm text-blue-100/90 leading-relaxed">
              Manage your Ministry of Tribal Affairs scholarship and fellowship applications. All communications and documentation are secured with institutional-grade data privacy.
            </p>
          </div>
          <div className="flex flex-wrap sm:flex-nowrap gap-3 shrink-0">
            <Link href="/schemes">
              <Button className="bg-amber-400 text-blue-950 hover:bg-amber-300 font-bold shadow-md hover:shadow-lg flex items-center gap-2 w-full sm:w-auto">
                Explore Schemes <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="/applications">
              <Button variant="outline" className="border-blue-400/30 text-white hover:bg-white/10 font-semibold w-full sm:w-auto text-sm backdrop-blur-sm">
                My Applications
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Row - Staggered entrance */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3.5 sm:gap-4 anim-fade-in delay-1">
        {[
          { label: "Active Applications", value: activeApps.length, icon: FileText, color: "text-blue-600", bg: "bg-blue-50/70 border-blue-100/80" },
          { label: "Pending Actions", value: pendingActions, icon: AlertTriangle, color: pendingActions > 0 ? "text-red-600" : "text-slate-500", bg: pendingActions > 0 ? "bg-red-50/80 border-red-200/80" : "bg-slate-50/70 border-slate-200/80", urgent: pendingActions > 0 },
          { label: "Unread Alerts", value: unread, icon: Bell, color: unread > 0 ? "text-amber-600" : "text-slate-500", bg: unread > 0 ? "bg-amber-50/80 border-amber-200/80" : "bg-slate-50/70 border-slate-200/80" },
          { label: "Total Applications", value: applications.length, icon: BookOpen, color: "text-emerald-600", bg: "bg-emerald-50/70 border-emerald-100/80" },
        ].map(({ label, value, icon: Icon, color, bg, urgent }) => (
          <Card key={label} className={`border ${bg} card-interactive transition-all`}>
            <CardContent className="p-4 sm:p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {loading ? (
                      <span className="inline-block w-8 h-7 bg-slate-200 animate-pulse rounded" />
                    ) : (
                      value
                    )}
                  </div>
                  <div className="text-xs font-medium text-slate-600 mt-1 flex items-center gap-1.5">
                    {label}
                    {urgent && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />}
                  </div>
                </div>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${bg}`}>
                  <Icon className={`w-5 h-5 ${color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Action Advisories */}
      {!loading && profile && !profile.is_profile_complete && (
        <Alert className="border-amber-300 bg-amber-50/90 text-amber-950 anim-fade-in delay-2 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <AlertTitle className="text-amber-900 font-bold text-sm">Action Required &bull; Complete Your Profile</AlertTitle>
          <AlertDescription className="text-amber-800 text-xs mt-1 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span>Your applicant profile is incomplete. Profile verification is required before final submission of scheme applications.</span>
            <Link href="/profile" className="font-bold underline text-amber-950 hover:text-amber-700 shrink-0 inline-flex items-center gap-1">
              Complete Profile <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </AlertDescription>
        </Alert>
      )}

      {!loading && deficiencies.length > 0 && (
        <Alert className="border-red-300 bg-red-50/90 text-red-950 anim-fade-in delay-2 shadow-xs">
          <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <AlertTitle className="text-red-900 font-bold text-sm">
            Urgent Deficiency Advisory &bull; {deficiencies.length} Application{deficiencies.length > 1 ? "s" : ""} Require Attention
          </AlertTitle>
          <AlertDescription className="text-red-800 text-xs mt-1 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span>The scrutiny officer has requested document re-upload or clarification. Timely response prevents application cancellation.</span>
            <Link href="/applications" className="font-bold underline text-red-950 hover:text-red-700 shrink-0 inline-flex items-center gap-1">
              Review Deficiencies <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Grid: Applications & Side Cards */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 anim-fade-in delay-3">
        {/* Applications Column */}
        <div className="xl:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">My Applications</h2>
              <p className="text-xs text-slate-500">Recent scholarship & fellowship submissions</p>
            </div>
            <Link href="/applications" className="text-xs text-blue-700 font-bold hover:text-blue-900 flex items-center gap-1 transition-colors">
              View all ({applications.length}) <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="border-slate-200">
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 animate-pulse" />
                    <div className="space-y-2 flex-1">
                      <div className="h-4 bg-slate-200 rounded w-1/3 animate-pulse" />
                      <div className="h-3 bg-slate-100 rounded w-1/2 animate-pulse" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : applications.length === 0 ? (
            <Card className="border-dashed border-2 border-slate-200 bg-slate-50/50">
              <CardContent className="p-10 text-center space-y-4">
                <div className="w-14 h-14 bg-white shadow-sm border border-slate-200 rounded-full mx-auto flex items-center justify-center text-slate-400">
                  <FileText className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800">No Applications Found</h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    Browse available MoTA scholarship and fellowship schemes to begin your institutional application.
                  </p>
                </div>
                <Link href="/schemes">
                  <Button className="bg-blue-900 hover:bg-blue-800 text-white font-semibold text-xs shadow-sm">
                    Browse Available Schemes
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {applications.slice(0, 5).map((app) => {
                const cfg = STATUS_CONFIG[app.status] || { variant: "secondary", label: app.status, icon: FileText };
                const Icon = cfg.icon;
                const isUrgent = app.status === "deficiency";

                return (
                  <Link key={app.id} href={`/applications/${app.id}`} className="block group">
                    <Card className={`border transition-all card-interactive ${
                      isUrgent
                        ? "border-red-300 bg-red-50/20 hover:border-red-400"
                        : "border-slate-200 hover:border-blue-300"
                    }`}>
                      <CardContent className="p-4 sm:p-5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3.5 min-w-0">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                              isUrgent ? "bg-red-100 text-red-700" : "bg-blue-50 text-blue-800"
                            }`}>
                              <Icon className="w-5 h-5" />
                            </div>
                            <div className="min-w-0">
                              <div className="font-bold text-slate-900 text-sm truncate group-hover:text-blue-900 transition-colors">
                                {app.scheme_name || "MoTA Scholarship Scheme"}
                              </div>
                              <div className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
                                <span className="font-mono font-medium text-slate-700">
                                  {app.reference_number || "Draft (Not Submitted)"}
                                </span>
                                <span>&bull;</span>
                                <span>Submitted: {formatDate(app.submitted_at)}</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <Badge variant={cfg.variant} pulse={isUrgent}>
                              {cfg.label}
                            </Badge>
                            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-5">
          {/* Profile Summary Card */}
          <Card className="border-slate-200 shadow-xs">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center text-blue-700">
                    <User className="w-4 h-4" />
                  </div>
                  <CardTitle className="text-sm font-bold text-slate-900">Profile Summary</CardTitle>
                </div>
                {profile?.is_profile_complete ? (
                  <Badge variant="success" className="text-[10px] font-bold">Verified</Badge>
                ) : (
                  <Badge variant="warning" className="text-[10px] font-bold">Incomplete</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              {loading ? (
                <div className="space-y-2.5 animate-pulse">
                  {[1, 2, 3].map((i) => <div key={i} className="h-3.5 bg-slate-200 rounded w-full" />)}
                </div>
              ) : (
                <>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Full Name</span>
                    <span className="font-semibold text-slate-800 text-right max-w-[160px] truncate">{user?.full_name || "--"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Community</span>
                    <span className="font-semibold text-slate-800">Scheduled Tribe (ST)</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Domicile State</span>
                    <span className="font-semibold text-slate-800">{profile?.state_of_domicile || "--"}</span>
                  </div>
                  <Link href="/profile" className="block pt-2">
                    <Button variant="outline" className="w-full text-xs font-semibold border-slate-300 text-slate-700 hover:bg-slate-50">
                      View & Edit Profile
                    </Button>
                  </Link>
                </>
              )}
            </CardContent>
          </Card>

          {/* Quick Notifications Preview */}
          <Card className="border-slate-200 shadow-xs">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center text-amber-700">
                    <Bell className="w-4 h-4" />
                  </div>
                  <CardTitle className="text-sm font-bold text-slate-900">Communications</CardTitle>
                </div>
                {unread > 0 && (
                  <span className="bg-amber-500 text-white text-[10px] font-bold rounded-full px-2 py-0.5 notif-dot">
                    {unread} unread
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-3 space-y-2.5">
              {loading ? (
                <div className="space-y-2 animate-pulse">
                  {[1, 2].map((i) => <div key={i} className="h-12 bg-slate-100 rounded-lg" />)}
                </div>
              ) : notifications.length === 0 ? (
                <div className="text-center py-6 text-slate-400">
                  <Bell className="w-6 h-6 mx-auto mb-1.5 opacity-40" />
                  <p className="text-xs text-slate-500">No pending alerts</p>
                </div>
              ) : (
                <>
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`p-3 rounded-lg text-xs transition-all ${
                        n.read_at
                          ? "bg-slate-50/80 border border-slate-100 text-slate-600"
                          : "bg-blue-50/60 border border-blue-200/70 text-slate-800 shadow-xs"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-bold truncate text-slate-900">{n.title}</span>
                        {!n.read_at && <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0" />}
                      </div>
                      <p className="text-slate-600 mt-1 line-clamp-2 leading-relaxed text-[11px]">{n.body}</p>
                    </div>
                  ))}
                  <Link href="/notifications" className="block pt-1">
                    <Button variant="ghost" className="w-full text-xs text-blue-800 hover:bg-blue-50 font-semibold">
                      Open Notification Center &rarr;
                    </Button>
                  </Link>
                </>
              )}
            </CardContent>
          </Card>

          {/* Institutional Trust & Compliance Badge */}
          <div className="rounded-xl border border-blue-200/80 bg-gradient-to-br from-blue-50 to-indigo-50/60 p-4 text-xs text-blue-900 shadow-xs space-y-1.5">
            <div className="flex items-center gap-2 font-bold text-blue-950 text-xs">
              <ShieldCheck className="w-4 h-4 text-blue-700 shrink-0" />
              Government Trust & Security
            </div>
            <p className="text-[11px] text-blue-800/90 leading-relaxed">
              Aadhaar numbers are stored as SHA-256 salted hashes. DBT mandates are processed via verified PFMS/NPCI rails in compliance with GoI security directives.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
