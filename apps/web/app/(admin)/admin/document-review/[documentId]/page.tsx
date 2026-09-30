"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  ShieldAlert, AlertTriangle, CheckCircle2, XCircle, ArrowLeft,
  RefreshCw, Play, FileText, Check, Sparkles, UserCheck, Shield
} from "lucide-react";

interface AIResultsResponse {
  document_id: string;
  document_type: string;
  status: string;
  ai_disclaimer: string;
  extraction?: {
    ai_provider: string;
    model: string;
    processing_time_ms: number;
    extracted_fields: Record<string, any>;
    confidence_scores: Record<string, number>;
    raw_text_available: boolean;
    label: string;
  } | null;
  quality?: {
    is_readable: boolean;
    is_complete: boolean;
    quality_score: number | null;
    anomaly_flags: string[];
    ai_notes: string | null;
    label: string;
  } | null;
  officer_review?: {
    officer_decision: string | null;
    officer_notes: string | null;
    verified_at: string | null;
    reviewed_by_id: string | null;
  } | null;
}

export default function DocumentReviewPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params?.documentId as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AIResultsResponse | null>(null);

  // Officer action state
  const [submitting, setSubmitting] = useState(false);
  const [decision, setDecision] = useState<"accepted" | "rejected" | null>(null);
  const [officerNotes, setOfficerNotes] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Trigger state
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    const res = await fetchApi<AIResultsResponse>(`/api/v1/processing/results/${documentId}`);
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setData(res.data);
      if (res.data.officer_review?.officer_decision) {
        setDecision(res.data.officer_review.officer_decision as "accepted" | "rejected");
        setOfficerNotes(res.data.officer_review.officer_notes || "");
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    if (documentId) {
      loadData();
    }
  }, [documentId]);

  const handleTriggerPipeline = async () => {
    setTriggering(true);
    setTriggerMsg(null);
    const res = await fetchApi<{ message: string }>(`/api/v1/processing/trigger/${documentId}`, {
      method: "POST",
    });
    if (res.error) {
      setError(res.error);
    } else {
      setTriggerMsg(res.data?.message || "AI Document Processing Pipeline triggered successfully.");
      setTimeout(() => {
        loadData();
      }, 2000);
    }
    setTriggering(false);
  };

  const handleSubmitDecision = async () => {
    if (!decision) {
      setError("Please select either Accept or Reject before submitting.");
      return;
    }
    if (decision === "rejected" && !officerNotes.trim()) {
      setError("Officer notes explaining the reason for rejection are required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setActionSuccess(null);

    const res = await fetchApi(`/api/v1/processing/review/${documentId}`, {
      method: "POST",
      body: JSON.stringify({
        decision,
        officer_notes: officerNotes.trim() || undefined,
      }),
    });

    if (res.error) {
      setError(res.error);
    } else {
      setActionSuccess(`Document successfully marked as ${decision.toUpperCase()} by authorised officer.`);
      await loadData();
    }
    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
          <p className="text-sm text-slate-600">Loading document intelligence & review details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Navigation & Header */}
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.back()}
            className="gap-2 text-slate-600 border-slate-300 hover:bg-slate-100"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Application
          </Button>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-xs uppercase">
              DOC ID: {documentId?.slice(0, 8)}...
            </Badge>
            <Badge
              className={
                data?.status === "verified"
                  ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                  : data?.status === "rejected"
                  ? "bg-red-100 text-red-800 border-red-300"
                  : data?.status === "processed"
                  ? "bg-blue-100 text-blue-800 border-blue-300"
                  : "bg-slate-100 text-slate-800 border-slate-300"
              }
            >
              Status: {data?.status?.toUpperCase() || "UNKNOWN"}
            </Badge>
          </div>
        </div>

        {/* MANDATORY AI DISCLAIMER BANNER */}
        <div className="bg-amber-50 border-2 border-amber-300 rounded-lg p-4 text-amber-900 shadow-sm flex items-start gap-3">
          <ShieldAlert className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-sm tracking-wide uppercase text-amber-800">
                AI SUGGESTION — NOT VERIFIED
              </h2>
              <span className="text-xs px-2 py-0.5 bg-amber-200 text-amber-900 font-semibold rounded">
                ASSISTIVE SYSTEM ONLY
              </span>
            </div>
            <p className="text-xs mt-1 text-amber-800 leading-relaxed">
              All OCR extracts, quality assessments, and anomaly signals shown on this page are automated suggestions generated by an AI assistant. 
              They <strong>do not constitute official government verification</strong> and have not been certified by any state authority. 
              The authorised scrutiny/verification officer has sole legal authority to accept or reject this document.
            </p>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {actionSuccess && (
          <Alert className="bg-emerald-50 border-emerald-200 text-emerald-800">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <AlertTitle>Decision Recorded</AlertTitle>
            <AlertDescription>{actionSuccess}</AlertDescription>
          </Alert>
        )}

        {triggerMsg && (
          <Alert className="bg-blue-50 border-blue-200 text-blue-800">
            <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
            <AlertTitle>Pipeline Update</AlertTitle>
            <AlertDescription>{triggerMsg}</AlertDescription>
          </Alert>
        )}

        {/* Trigger Banner if not yet processed */}
        {data?.status !== "processed" && data?.status !== "verified" && data?.status !== "rejected" && (
          <Card className="border-blue-200 bg-blue-50/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-blue-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                Run AI Intelligence Pipeline
              </CardTitle>
              <CardDescription className="text-xs text-blue-700">
                Process this document through malware check, OCR text extraction, structured entity parsing, and quality validation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleTriggerPipeline}
                disabled={triggering}
                className="bg-blue-700 hover:bg-blue-800 text-white gap-2"
              >
                {triggering ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {triggering ? "Dispatching Pipeline..." : "Execute AI Processing Pipeline"}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Grid: Extracted Fields & Quality Analysis */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Left Column: Extracted Fields */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 bg-slate-50/80 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-600" />
                  Extracted Fields
                </CardTitle>
                <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                  AI SUGGESTION — NOT VERIFIED
                </span>
              </div>
              <CardDescription className="text-xs text-slate-500 mt-1">
                {data?.extraction?.model ? `Model: ${data.extraction.model} (${data.extraction.processing_time_ms}ms)` : "No extraction data available"}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {data?.extraction?.extracted_fields && Object.keys(data.extraction.extracted_fields).length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {Object.entries(data.extraction.extracted_fields).map(([key, val]) => {
                    const conf = data.extraction?.confidence_scores?.[key];
                    return (
                      <div key={key} className="py-2.5 flex items-start justify-between text-xs">
                        <div>
                          <span className="font-mono text-slate-500 uppercase tracking-wider text-[11px]">
                            {key.replace(/_/g, " ")}
                          </span>
                          <p className="font-medium text-slate-900 mt-0.5 text-sm">
                            {val !== null && val !== undefined ? String(val) : "—"}
                          </p>
                        </div>
                        <div className="text-right shrink-0 ml-4">
                          {conf !== undefined && (
                            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-semibold ${
                              conf >= 0.85
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : conf >= 0.65
                                ? "bg-amber-50 text-amber-700 border border-amber-200"
                                : "bg-red-50 text-red-700 border border-red-200"
                            }`}>
                              {(conf * 100).toFixed(0)}% conf
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400 text-xs">
                  No extracted fields found. Please trigger the AI pipeline or verify manually.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Right Column: Document Quality & Anomaly Analysis */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="border-b border-slate-100 bg-slate-50/80 pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-slate-600" />
                  Quality & Integrity Analysis
                </CardTitle>
                <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                  AI SUGGESTION — NOT VERIFIED
                </span>
              </div>
              <CardDescription className="text-xs text-slate-500 mt-1">
                Automated heuristics & visual anomaly detection
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-4 text-xs">
              {data?.quality ? (
                <>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2.5 bg-slate-50 rounded border border-slate-100">
                      <p className="text-[11px] text-slate-500 font-medium">Readability</p>
                      <p className={`font-semibold mt-1 ${data.quality.is_readable ? "text-emerald-700" : "text-red-700"}`}>
                        {data.quality.is_readable ? "Readable" : "Unreadable"}
                      </p>
                    </div>

                    <div className="p-2.5 bg-slate-50 rounded border border-slate-100">
                      <p className="text-[11px] text-slate-500 font-medium">Completeness</p>
                      <p className={`font-semibold mt-1 ${data.quality.is_complete ? "text-emerald-700" : "text-amber-700"}`}>
                        {data.quality.is_complete ? "Complete" : "Incomplete"}
                      </p>
                    </div>

                    <div className="p-2.5 bg-slate-50 rounded border border-slate-100">
                      <p className="text-[11px] text-slate-500 font-medium">Quality Score</p>
                      <p className="font-semibold text-slate-900 mt-1 font-mono">
                        {data.quality.quality_score !== null ? `${(data.quality.quality_score * 100).toFixed(0)}%` : "—"}
                      </p>
                    </div>
                  </div>

                  {/* Anomaly Flags */}
                  <div>
                    <h3 className="font-semibold text-slate-700 mb-2">Flagged Anomalies:</h3>
                    {data.quality.anomaly_flags && data.quality.anomaly_flags.length > 0 ? (
                      <div className="space-y-1.5">
                        {data.quality.anomaly_flags.map((flag, idx) => (
                          <div key={idx} className="flex items-start gap-2 bg-amber-50/80 border border-amber-200 text-amber-900 px-2.5 py-1.5 rounded">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                            <span className="text-xs">{flag}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1.5 rounded flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        No anomalies flagged by AI.
                      </p>
                    )}
                  </div>

                  {/* AI Notes */}
                  {data.quality.ai_notes && (
                    <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
                      <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">AI Analysis Notes:</p>
                      <p className="text-slate-700 text-xs leading-relaxed">{data.quality.ai_notes}</p>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-slate-400 text-xs">
                  Quality assessment has not been conducted yet.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* AUTHORITATIVE OFFICER DECISION PANEL */}
        <Card className="border-2 border-indigo-200 shadow-md bg-white">
          <CardHeader className="bg-indigo-50/70 border-b border-indigo-100 pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-indigo-950 flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-indigo-700" />
                Authorised Officer Verification Decision (Human Authority Only)
              </CardTitle>
              <Badge className="bg-indigo-900 text-white font-mono text-[10px]">
                FINAL ADMINISTRATIVE DETERMINATION
              </Badge>
            </div>
            <CardDescription className="text-xs text-indigo-800 mt-1">
              Under MoTA scheme guidelines, only designated government officers hold the authority to approve or reject submitted documents. AI systems do not possess decision-making jurisdiction.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-5">
            {/* Decision selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Select Official Determination *
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setDecision("accepted")}
                  className={`flex items-center justify-center gap-2 p-3.5 rounded-lg border-2 font-medium text-sm transition-all ${
                    decision === "accepted"
                      ? "border-emerald-600 bg-emerald-50 text-emerald-900 shadow-sm"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                  }`}
                >
                  <CheckCircle2 className={`w-5 h-5 ${decision === "accepted" ? "text-emerald-600" : "text-slate-400"}`} />
                  Accept Document (Verified)
                </button>

                <button
                  type="button"
                  onClick={() => setDecision("rejected")}
                  className={`flex items-center justify-center gap-2 p-3.5 rounded-lg border-2 font-medium text-sm transition-all ${
                    decision === "rejected"
                      ? "border-red-600 bg-red-50 text-red-900 shadow-sm"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                  }`}
                >
                  <XCircle className={`w-5 h-5 ${decision === "rejected" ? "text-red-600" : "text-slate-400"}`} />
                  Reject Document (Requires Deficiency/Re-upload)
                </button>
              </div>
            </div>

            {/* Officer Notes */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Official Review Notes {decision === "rejected" ? "(Required for Rejection)*" : "(Optional)"}
              </label>
              <textarea
                rows={3}
                value={officerNotes}
                onChange={(e) => setOfficerNotes(e.target.value)}
                placeholder={
                  decision === "rejected"
                    ? "Specify official reason for rejection (e.g., certificate seal unclear, name spelling mismatch, expired validity)..."
                    : "Enter any administrative verification notes or remarks for the audit trail..."
                }
                className="w-full text-xs p-3 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {/* Existing Officer Review info if already performed */}
            {data?.officer_review?.officer_decision && (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-600 flex items-center justify-between">
                <div>
                  <span className="font-medium text-slate-900">Previous Decision Recorded: </span>
                  <span className="uppercase font-bold">{data.officer_review.officer_decision}</span>
                  {data.officer_review.verified_at && (
                    <span className="text-slate-500 ml-2">
                      on {new Date(data.officer_review.verified_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                {data.officer_review.reviewed_by_id && (
                  <span className="font-mono text-[10px] text-slate-400">
                    Officer ID: {data.officer_review.reviewed_by_id.slice(0, 8)}...
                  </span>
                )}
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-end pt-2">
              <Button
                onClick={handleSubmitDecision}
                disabled={submitting || !decision}
                className="bg-indigo-900 hover:bg-indigo-950 text-white px-6 font-medium gap-2"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Recording Official Decision...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Submit Authoritative Decision
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
