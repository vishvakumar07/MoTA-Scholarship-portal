"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/utils";
import { EmptyState } from "@/components/ui/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  FileText, Search, PlusCircle, AlertTriangle, CheckCircle2,
  Clock, RefreshCw, ShieldCheck, ChevronRight, BookOpen,
  Award, XCircle, ArrowUpRight, Calendar, Filter, Sparkles
} from "lucide-react";

interface ApplicationItem {
  id: string;
  reference_number: string | null;
  status: string;
  scheme_code: string | null;
  scheme_name: string | null;
  created_at: string;
  submitted_at: string | null;
  has_open_deficiency?: boolean;
}

const STATUS_CONFIG: Record<string, { variant: "default" | "secondary" | "destructive" | "urgent" | "success" | "warning" | "motaCSS" | "motaCentralSector"; label: string; icon: React.ElementType; step: string }> = {
  draft: { variant: "secondary", label: "Draft", icon: FileText, step: "Step 1 of 5" },
  submitted: { variant: "motaCSS", label: "Submitted", icon: Clock, step: "Step 2 of 5" },
  document_processing: { variant: "motaCSS", label: "Processing", icon: RefreshCw, step: "Step 2 of 5" },
  document_verification: { variant: "motaCentralSector", label: "Verification", icon: ShieldCheck, step: "Step 3 of 5" },
  deficiency: { variant: "urgent", label: "Action Required", icon: AlertTriangle, step: "Urgent Action" },
  resubmitted: { variant: "warning", label: "Resubmitted", icon: RefreshCw, step: "Step 3 of 5" },
  eligibility_review: { variant: "warning", label: "Eligibility Review", icon: CheckCircle2, step: "Step 4 of 5" },
  eligible: { variant: "success", label: "Eligible", icon: CheckCircle2, step: "Step 4 of 5" },
  ineligible: { variant: "destructive", label: "Ineligible", icon: XCircle, step: "Completed" },
  scrutiny: { variant: "motaCSS", label: "Scrutiny", icon: BookOpen, step: "Step 4 of 5" },
  shortlisted: { variant: "motaCentralSector", label: "Shortlisted", icon: Award, step: "Step 5 of 5" },
  selection_review: { variant: "motaCSS", label: "Committee Review", icon: Clock, step: "Step 5 of 5" },
  selected: { variant: "success", label: "Selected", icon: Award, step: "Sanctioned" },
  not_selected: { variant: "secondary", label: "Not Selected", icon: XCircle, step: "Completed" },
  completed: { variant: "success", label: "Disbursed", icon: CheckCircle2, step: "Completed" },
  withdrawn: { variant: "secondary", label: "Withdrawn", icon: XCircle, step: "Withdrawn" },
};

export default function ApplicationsListPage() {
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterTab, setFilterTab] = useState<"all" | "draft" | "review" | "deficiency" | "completed">("all");

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    setLoading(true);
    const res = await fetchApi("/api/v1/applications");
    if (res.data) {
      setApplications(res.data.applications || []);
    } else {
      setError(res.error || "Failed to load applications.");
    }
    setLoading(false);
  };

  const deficienciesCount = applications.filter((a) => a.status === "deficiency").length;
  const inReviewCount = applications.filter((a) =>
    ["submitted", "document_processing", "document_verification", "resubmitted", "eligibility_review", "scrutiny", "shortlisted", "selection_review"].includes(a.status)
  ).length;
  const completedCount = applications.filter((a) =>
    ["selected", "not_selected", "completed", "ineligible", "withdrawn"].includes(a.status)
  ).length;
  const draftCount = applications.filter((a) => a.status === "draft").length;

  const filtered = applications.filter((app) => {
    const matchesSearch =
      (app.reference_number || "").toLowerCase().includes(search.toLowerCase()) ||
      (app.scheme_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (app.scheme_code || "").toLowerCase().includes(search.toLowerCase());

    if (!matchesSearch) return false;

    if (filterTab === "draft") return app.status === "draft";
    if (filterTab === "deficiency") return app.status === "deficiency";
    if (filterTab === "review") {
      return ["submitted", "document_processing", "document_verification", "resubmitted", "eligibility_review", "scrutiny", "shortlisted", "selection_review"].includes(app.status);
    }
    if (filterTab === "completed") {
      return ["selected", "not_selected", "completed", "ineligible", "withdrawn"].includes(app.status);
    }
    return true;
  });

  return (
    <div className="space-y-6 break-anywhere">
      {/* Header Banner */}
      <div className="anim-fade-in flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-blue-900 tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            Ministry of Tribal Affairs &bull; Scholarship Portal
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">My Scholarship Applications</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Track submission status, review official timelines, and respond to document scrutiny notices.
          </p>
        </div>
        <Link href="/schemes">
          <Button className="bg-blue-900 hover:bg-blue-800 text-white font-medium shadow-md flex items-center gap-2">
            <PlusCircle className="w-4 h-4" />
            Apply for Scheme
          </Button>
        </Link>
      </div>

      {/* Deficiency Urgent Banner if any */}
      {deficienciesCount > 0 && (
        <Alert className="anim-fade-in border-red-300 bg-red-50/90 text-red-900 shadow-sm">
          <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <AlertTitle className="text-sm font-bold text-red-800 flex items-center gap-2">
              Action Required: Document Deficiency Notice ({deficienciesCount})
            </AlertTitle>
            <AlertDescription className="text-xs text-red-700 mt-1 leading-relaxed">
              Verification officers have raised a deficiency request on {deficienciesCount} of your applications.
              Please submit the required clarification or documents before the stipulated deadline to avoid cancellation.
            </AlertDescription>
          </div>
        </Alert>
      )}

      {/* Stat Cards - Staggered entrance */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 anim-fade-in delay-1">
        <Card className="border-slate-200 bg-white card-interactive shadow-xs transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total</span>
              <FileText className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-2">{loading ? "--" : applications.length}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Submitted & drafts</div>
          </CardContent>
        </Card>

        <Card className="border-blue-100 bg-blue-50/40 card-interactive shadow-xs transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider">Under Review</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-blue-900 mt-2">{loading ? "--" : inReviewCount}</div>
            <div className="text-[11px] text-blue-600/70 mt-0.5">Scrutiny / Verification</div>
          </CardContent>
        </Card>

        <Card className={`card-interactive shadow-xs transition-all ${deficienciesCount > 0 ? "border-red-300 bg-red-50/60" : "border-slate-200 bg-white"}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className={`text-xs uppercase tracking-wider ${deficienciesCount > 0 ? "text-red-700 font-bold" : "text-slate-500 font-medium"}`}>
                Action Needed
              </span>
              <AlertTriangle className={`w-4 h-4 ${deficienciesCount > 0 ? "text-red-600 animate-pulse" : "text-slate-400"}`} />
            </div>
            <div className={`text-2xl font-bold mt-2 ${deficienciesCount > 0 ? "text-red-700" : "text-slate-900"}`}>
              {loading ? "--" : deficienciesCount}
            </div>
            <div className={`text-[11px] mt-0.5 ${deficienciesCount > 0 ? "text-red-600 font-medium" : "text-slate-400"}`}>
              {deficienciesCount > 0 ? "Pending responses" : "Zero pending"}
            </div>
          </CardContent>
        </Card>

        <Card className="border-emerald-100 bg-emerald-50/40 card-interactive shadow-xs transition-all">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Completed</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-emerald-900 mt-2">{loading ? "--" : completedCount}</div>
            <div className="text-[11px] text-emerald-600/70 mt-0.5">Sanctioned & disbursed</div>
          </CardContent>
        </Card>
      </div>

      {/* Search & Tabs Controls */}
      <div className="anim-fade-in delay-2 flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-medium">
          {[
            { id: "all", label: `All (${applications.length})` },
            { id: "review", label: `In Review (${inReviewCount})` },
            { id: "deficiency", label: `Deficiencies (${deficienciesCount})`, urgent: deficienciesCount > 0 },
            { id: "draft", label: `Drafts (${draftCount})` },
            { id: "completed", label: `Finalized (${completedCount})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterTab(tab.id as any)}
              className={`px-3 py-1.5 rounded-md transition-all duration-150 flex items-center gap-1.5 ${
                filterTab === tab.id
                  ? "bg-blue-900 text-white font-semibold shadow-xs"
                  : tab.urgent
                  ? "bg-red-100 text-red-800 hover:bg-red-200 font-bold"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {tab.label}
              {tab.urgent && <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-ping" />}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ref or scheme..."
            className="pl-8 text-xs h-9 input-enhanced"
          />
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="space-y-3 anim-fade-in">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-5 border border-slate-200 rounded-xl bg-white space-y-3">
              <div className="flex justify-between">
                <div className="h-4 bg-slate-200 rounded w-1/3 animate-pulse" />
                <div className="h-4 bg-slate-200 rounded w-16 animate-pulse" />
              </div>
              <div className="h-3 bg-slate-100 rounded w-1/2 animate-pulse" />
            </div>
          ))}
        </div>
      ) : error ? (
        <Alert className="border-red-200 bg-red-50 text-red-800 anim-fade-in">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <AlertTitle className="text-xs font-semibold">Error Loading Applications</AlertTitle>
          <AlertDescription className="text-xs mt-1">{error}</AlertDescription>
        </Alert>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-xl p-6 anim-fade-in">
          <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
            <FileText className="w-6 h-6" />
          </div>
          <h2 className="text-base font-semibold text-slate-800">No applications match criteria</h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            {search
              ? "Try adjusting your search query or reset the filter tab."
              : "You have not submitted any applications in this category."}
          </p>
        </div>
      ) : (
        <div className="space-y-3 anim-fade-in delay-3">
          {filtered.map((app) => {
            const cfg = STATUS_CONFIG[app.status] || { variant: "secondary", label: app.status, icon: FileText, step: "" };
            const Icon = cfg.icon;
            const isUrgent = app.status === "deficiency";

            return (
              <Link key={app.id} href={`/applications/${app.id}`} className="block group">
                <Card className={`border card-interactive transition-all ${
                  isUrgent
                    ? "border-red-300 bg-red-50/20 hover:border-red-400 shadow-xs"
                    : "border-slate-200 bg-white hover:border-blue-300"
                }`}>
                  <CardContent className="p-4 sm:p-5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-start gap-3.5 min-w-0">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                          isUrgent ? "bg-red-100 text-red-700" : "bg-blue-50 text-blue-800"
                        }`}>
                          <Icon className="w-5 h-5" />
                        </div>

                        <div className="space-y-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm group-hover:text-blue-900 transition-colors truncate">
                              {app.scheme_name || "MoTA Scholarship Scheme"}
                            </span>
                            {app.scheme_code && (
                              <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                                {app.scheme_code}
                              </span>
                            )}
                          </div>

                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 font-mono">
                            <span>Ref: <strong className="text-slate-800">{app.reference_number || "Draft (Pending Submission)"}</strong></span>
                            <span>&bull;</span>
                            <span>Created: {formatDate(app.created_at)}</span>
                            {app.submitted_at && (
                              <>
                                <span>&bull;</span>
                                <span>Submitted: {formatDate(app.submitted_at)}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                        <div className="text-right hidden sm:block">
                          <Badge variant={cfg.variant} pulse={isUrgent}>
                            {cfg.label}
                          </Badge>
                          <div className="text-[10px] text-slate-400 font-mono mt-1">{cfg.step}</div>
                        </div>
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
  );
}
