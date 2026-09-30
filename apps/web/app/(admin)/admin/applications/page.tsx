"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  FileText, ShieldCheck, RefreshCw, Eye, AlertTriangle,
  Search, Sparkles
} from "lucide-react";

interface AppDocumentSummary {
  document_id: string;
  document_type: string;
  original_filename: string;
  status: string;
  has_ai_extraction: boolean;
  has_quality_analysis: boolean;
  officer_decision: string | null;
}

interface ApplicationReviewItem {
  id: string;
  application_number: string;
  scheme_name: string;
  scheme_code: string;
  applicant_name: string;
  status: string;
  submitted_at: string;
  documents: AppDocumentSummary[];
  pending_review_count: number;
}

function renderDecisionBadge(decision: string | null) {
  if (decision === "accepted") {
    return <Badge className="bg-emerald-100 text-emerald-800 text-[10px]">ACCEPTED</Badge>;
  }
  if (decision === "rejected") {
    return <Badge className="bg-red-100 text-red-800 text-[10px]">REJECTED</Badge>;
  }
  return <Badge variant="outline" className="text-amber-800 border-amber-300 bg-amber-50 text-[10px]">PENDING REVIEW</Badge>;
}

export default function OfficerApplicationsListPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [applications, setApplications] = useState<ApplicationReviewItem[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [runningConsistency, setRunningConsistency] = useState<string | null>(null);
  const [consistencyMsg, setConsistencyMsg] = useState<{ id: string; text: string } | null>(null);

  const loadApplications = async () => {
    setLoading(true);
    setError(null);
    const res = await fetchApi<any>("/api/v1/applications?status=submitted&limit=50");
    if (res.error) {
      setError(res.error);
      setApplications([]);
    } else if (res.data) {
      const rawApps = Array.isArray(res.data) ? res.data : (res.data.items || []);
      
      const enhancedApps: ApplicationReviewItem[] = await Promise.all(
        rawApps.map(async (app: any) => {
          const docRes = await fetchApi<any>(`/api/v1/processing/application/${app.id}`);
          const docs: AppDocumentSummary[] = docRes.data?.documents || [];
          const pendingCount = docRes.data?.pending_review_count ?? docs.filter((d: AppDocumentSummary) => !d.officer_decision).length;
          return {
            id: app.id,
            application_number: app.application_number || `APP-${app.id.slice(0, 8).toUpperCase()}`,
            scheme_name: app.scheme_name || app.scheme?.name || "MoTA Scholarship Scheme",
            scheme_code: app.scheme_code || app.scheme?.code || "SCHEME",
            applicant_name: app.applicant_name || app.applicant?.full_name || "Applicant",
            status: app.status || "submitted",
            submitted_at: app.submitted_at || app.created_at,
            documents: docs,
            pending_review_count: pendingCount,
          };
        })
      );
      setApplications(enhancedApps);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const handleRunConsistency = async (appId: string) => {
    setRunningConsistency(appId);
    setConsistencyMsg(null);
    const res = await fetchApi<{ anomalies_flagged: number; anomaly_details: string[]; message: string }>(
      `/api/v1/processing/consistency/${appId}`,
      { method: "POST" }
    );
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setConsistencyMsg({
        id: appId,
        text: `Cross-Document Analysis: ${res.data.anomalies_flagged} anomalies flagged across documents. ${res.data.message}`,
      });
    }
    setRunningConsistency(null);
  };

  const filteredApps = applications.filter((app) =>
    app.application_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.applicant_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.scheme_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-7 h-7 text-indigo-900" />
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Document Intelligence & Officer Review Portal
              </h1>
            </div>
            <p className="text-xs text-slate-600 mt-1">
              Review AI document entity extractions, anomaly detections, and issue official verification determinations.
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadApplications}
            disabled={loading}
            className="gap-2 text-slate-700 self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Queue
          </Button>
        </div>

        {/* AI Principle Notice */}
        <div className="bg-amber-50 border border-amber-300 rounded-md p-3.5 text-xs text-amber-900 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider text-amber-950">Official Scrutiny Note:</span>
            <p className="mt-0.5 leading-relaxed">
              All automated readings and cross-document anomaly signals are non-authoritative AI suggestions designed to assist scrutiny officers. 
              Only human scrutiny and verification officers possess legal jurisdiction to record official determinations.
            </p>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Notice</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Search bar */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by application #, applicant name, or scheme..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          />
        </div>

        {/* Applications List */}
        {loading ? (
          <div className="text-center py-12 space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin text-indigo-900 mx-auto" />
            <p className="text-xs text-slate-500">Loading applications and processing statuses...</p>
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-slate-200 p-8">
            <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No applications awaiting review</p>
            <p className="text-xs text-slate-500 mt-1">Any newly submitted applications with uploaded documents will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredApps.map((app) => (
              <Card key={app.id} className="border border-slate-200 hover:border-slate-300 transition-all shadow-sm bg-white">
                <CardHeader className="p-4 pb-2 bg-slate-50/60 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-indigo-950">
                        {app.application_number}
                      </span>
                      <Badge variant="outline" className="text-[11px] font-medium bg-white text-slate-700">
                        {app.scheme_name}
                      </Badge>
                      <Badge className="bg-slate-200 text-slate-800 text-[10px] font-mono">
                        {app.status.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">
                      Applicant: <strong className="text-slate-900">{app.applicant_name}</strong> | Submitted: {new Date(app.submitted_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={runningConsistency === app.id}
                      onClick={() => handleRunConsistency(app.id)}
                      className="text-xs gap-1.5 text-indigo-900 border-indigo-200 hover:bg-indigo-50"
                    >
                      <Sparkles className={`w-3.5 h-3.5 text-indigo-600 ${runningConsistency === app.id ? "animate-spin" : ""}`} />
                      {runningConsistency === app.id ? "Checking Consistency..." : "Cross-Doc Check"}
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="p-4 space-y-3">
                  {consistencyMsg && consistencyMsg.id === app.id && (
                    <div className="p-2.5 bg-blue-50 border border-blue-200 rounded text-xs text-blue-900 flex items-start gap-2">
                      <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                      <span>{consistencyMsg.text}</span>
                    </div>
                  )}

                  <div>
                    <h3 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                      Uploaded Documents & Scrutiny State ({app.documents.length})
                    </h3>
                    
                    {app.documents.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No documents uploaded for this application.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {app.documents.map((doc) => (
                          <div
                            key={doc.document_id}
                            className="flex items-center justify-between p-2.5 rounded border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors text-xs"
                          >
                            <div className="min-w-0 pr-2">
                              <p className="font-medium text-slate-900 truncate">
                                {doc.document_type.replace(/_/g, " ").toUpperCase()}
                              </p>
                              <p className="text-[11px] text-slate-500 truncate mt-0.5">
                                {doc.original_filename}
                              </p>
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                              {renderDecisionBadge(doc.officer_decision)}

                              <Link href={`/admin/document-review/${doc.document_id}`}>
                                <Button size="sm" variant="ghost" className="h-7 px-2 text-indigo-700 hover:text-indigo-900 hover:bg-indigo-50 gap-1">
                                  <Eye className="w-3.5 h-3.5" />
                                  Review
                                </Button>
                              </Link>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
