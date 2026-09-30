"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  BookOpen, ExternalLink, CheckCircle2, XCircle, AlertTriangle,
  FileText, ChevronRight, ArrowLeft, Shield, Calendar,
  Info, HelpCircle,
} from "lucide-react";

export default function SchemeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const code = params?.code as string;

  const [scheme, setScheme] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkAnswers, setCheckAnswers] = useState<Record<string, any>>({});
  const [checkResult, setCheckResult] = useState<any>(null);
  const [checking, setChecking] = useState(false);
  const [showCheck, setShowCheck] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi(`/api/v1/schemes/${code}`).then((res) => {
      if (res.data) setScheme(res.data);
      else setError(res.error || "Scheme not found.");
      setLoading(false);
    });
  }, [code]);

  const handleEligibilityCheck = async () => {
    if (!scheme?.active_version?.id) return;
    setChecking(true); setCheckResult(null);
    const res = await fetchApi("/api/v1/applications/eligibility-check", {
      method: "POST",
      body: JSON.stringify({ scheme_version_id: scheme.active_version.id, answers: checkAnswers }),
    });
    setChecking(false);
    if (res.data) setCheckResult(res.data);
  };

  const handleStartApplication = async () => {
    if (!scheme?.active_version?.id) return;
    setStarting(true); setStartError(null);
    const res = await fetchApi("/api/v1/applications/start", {
      method: "POST",
      body: JSON.stringify({ scheme_version_id: scheme.active_version.id }),
    });
    setStarting(false);
    if (res.data) router.push(`/applications/${res.data.application_id}`);
    else setStartError(res.error || "Could not start application.");
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[40vh]">
      <div className="w-8 h-8 border-2 border-blue-900 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="max-w-xl space-y-4">
      <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
      <Link href="/schemes"><Button variant="outline">Back to Schemes</Button></Link>
    </div>
  );

  const version = scheme?.active_version;
  const accepting = version?.is_accepting_applications;

  const overallStyle: Record<string, string> = {
    likely_eligible: "bg-emerald-50 border-emerald-300 text-emerald-900",
    likely_ineligible: "bg-red-50 border-red-300 text-red-900",
    requires_verification: "bg-amber-50 border-amber-300 text-amber-900",
  };
  const overallLabel: Record<string, string> = {
    likely_eligible: "Likely Eligible",
    likely_ineligible: "Likely Ineligible",
    requires_verification: "Requires Verification",
  };

  return (
    <div className="max-w-4xl space-y-6">
      <Link href="/schemes" className="inline-flex items-center gap-1.5 text-sm text-blue-700 hover:underline font-medium">
        <ArrowLeft className="w-4 h-4" /> Back to Schemes
      </Link>

      {/* Hero */}
      <div className="bg-gradient-to-br from-blue-950 to-indigo-900 rounded-2xl p-6 text-white shadow-xl">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 bg-amber-400/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-7 h-7 text-amber-300" />
          </div>
          <div className="flex-1">
            <div className="text-[11px] font-mono text-blue-300 mb-1">{scheme.code}</div>
            <h1 className="text-xl sm:text-2xl font-extrabold leading-tight">{scheme.name}</h1>
            {scheme.description && <p className="text-sm text-blue-200 mt-2 leading-relaxed">{scheme.description}</p>}
            <div className="flex flex-wrap gap-2 mt-3">
              {scheme.official_url && (
                <a href={scheme.official_url} target="_blank" rel="noopener noreferrer"
                   className="inline-flex items-center gap-1.5 text-xs text-amber-300 hover:text-amber-200 bg-amber-400/10 border border-amber-400/20 px-3 py-1.5 rounded-full transition-colors">
                  <ExternalLink className="w-3 h-3" /> Official Source
                </a>
              )}
              <span className={`text-xs px-3 py-1.5 rounded-full font-semibold ${accepting ? "bg-emerald-400/20 text-emerald-300 border border-emerald-400/20" : "bg-slate-700 text-slate-400"}`}>
                {accepting ? "Applications Open" : "Not Accepting"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {startError && (
        <Alert variant="destructive">
          <AlertTriangle className="w-4 h-4" />
          <AlertTitle>Could Not Start Application</AlertTitle>
          <AlertDescription>{startError}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-5">
          {/* Version Info */}
          {version && (
            <Card className="border-slate-200">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-blue-700" /> Application Period
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 grid grid-cols-2 gap-4 text-xs">
                <div><span className="text-slate-500">Academic Year</span><div className="font-semibold mt-0.5 text-slate-800">{version.academic_year || "Not specified"}</div></div>
                <div><span className="text-slate-500">Version</span><div className="font-semibold mt-0.5 text-slate-800">{version.version_number}</div></div>
                <div><span className="text-slate-500">Effective From</span><div className="font-semibold mt-0.5 text-slate-800">{version.effective_from}</div></div>
                <div><span className="text-slate-500">Effective To</span><div className="font-semibold mt-0.5 text-slate-800">{version.effective_to || "Open-ended"}</div></div>
                {version.source_document_title && (
                  <div className="col-span-2">
                    <span className="text-slate-500">Source Document</span>
                    <div className="font-semibold mt-0.5">
                      {version.source_document_url
                        ? <a href={version.source_document_url} target="_blank" rel="noopener noreferrer" className="text-blue-700 hover:underline flex items-center gap-1">
                            {version.source_document_title} <ExternalLink className="w-3 h-3" />
                          </a>
                        : <span className="text-slate-800">{version.source_document_title}</span>}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Eligibility Rules */}
          {version?.rules && version.rules.length > 0 && (
            <Card className="border-slate-200">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-700" /> Eligibility Criteria
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2">
                {version.rules.map((rule: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                    <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-semibold text-slate-800">{rule.display_label}</div>
                      {rule.description && <div className="text-slate-500 mt-0.5">{rule.description}</div>}
                      {rule.source_url && (
                        <a href={rule.source_url} target="_blank" rel="noopener noreferrer"
                           className="text-blue-600 hover:underline flex items-center gap-1 mt-1">
                          <ExternalLink className="w-3 h-3" />
                          {rule.source_document_title || "Official Source"}
                          {rule.source_section && ` — ${rule.source_section}`}
                        </a>
                      )}
                      {!rule.is_official_source_confirmed && (
                        <div className="text-amber-600 mt-1 font-medium flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> Official source not yet confirmed
                        </div>
                      )}
                    </div>
                    {rule.is_mandatory && (
                      <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-bold flex-shrink-0">MANDATORY</span>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Required Documents */}
          {version?.required_documents && version.required_documents.length > 0 && (
            <Card className="border-slate-200">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-700" /> Required Documents
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2">
                {[...version.required_documents].sort((a: any, b: any) => a.display_order - b.display_order).map((doc: any, idx: number) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-bold ${doc.is_mandatory ? "bg-red-100 text-red-700" : "bg-slate-200 text-slate-600"}`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-slate-800">{doc.document_display_name}</div>
                      {doc.description && <div className="text-slate-500 mt-0.5">{doc.description}</div>}
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        {doc.accepted_formats?.map((fmt: string) => (
                          <span key={fmt} className="text-[10px] bg-blue-50 text-blue-700 border border-blue-100 px-1.5 py-0.5 rounded uppercase font-mono">{fmt}</span>
                        ))}
                        {doc.max_size_mb && <span className="text-[10px] text-slate-500">Max: {doc.max_size_mb} MB</span>}
                      </div>
                    </div>
                    {!doc.is_mandatory && (
                      <span className="text-[10px] bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded font-semibold flex-shrink-0">Optional</span>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Sidebar */}
        <div className="space-y-4">
          <Card className={`border-2 ${accepting ? "border-blue-200 bg-blue-50" : "border-slate-200 bg-slate-50"} sticky top-4`}>
            <CardContent className="pt-5 space-y-3">
              <h3 className="font-bold text-blue-900 text-sm">Apply for this Scheme</h3>
              {accepting ? (
                <>
                  <p className="text-xs text-blue-700 leading-relaxed">
                    Applications are currently open. Complete your profile and check eligibility before applying.
                  </p>
                  <Button
                    onClick={() => setShowCheck(!showCheck)}
                    variant="outline"
                    className="w-full border-blue-300 text-blue-800 hover:bg-blue-100 text-xs font-semibold"
                  >
                    <HelpCircle className="w-3.5 h-3.5 mr-1.5" />
                    {showCheck ? "Hide Pre-Check" : "Eligibility Pre-Check"}
                  </Button>
                  <Button
                    onClick={handleStartApplication}
                    disabled={starting}
                    className="w-full bg-blue-900 hover:bg-blue-800 text-white font-bold text-sm"
                  >
                    {starting ? "Starting..." : "Start Application →"}
                  </Button>
                  <p className="text-[10px] text-blue-500 text-center leading-relaxed">
                    Drafts are auto-saved. You can return anytime before the deadline.
                  </p>
                </>
              ) : (
                <div className="text-xs text-slate-600 bg-white rounded-lg p-3 border border-slate-200 text-center">
                  This scheme is not currently accepting applications.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Eligibility Pre-check Panel */}
          {showCheck && version && (
            <Card className="border-amber-200 bg-amber-50">
              <CardHeader className="pb-2 border-b border-amber-100">
                <CardTitle className="text-sm font-bold text-amber-900 flex items-center gap-2">
                  <HelpCircle className="w-4 h-4" /> Quick Eligibility Check
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-3 space-y-3">
                <div className="text-[11px] text-amber-700 bg-white/60 rounded p-2 border border-amber-200 leading-relaxed">
                  This is a preliminary automated assessment only. Final eligibility is determined by authorised MoTA officers.
                </div>
                {[
                  { key: "caste_category", label: "Caste Category", type: "select", options: ["ST", "SC", "OBC", "General"] },
                  { key: "annual_family_income", label: "Annual Family Income (₹)", type: "number" },
                  { key: "age", label: "Age (years)", type: "number" },
                ].map(({ key, label, type, options }) => (
                  <div key={key} className="space-y-1">
                    <label className="text-[11px] font-semibold text-amber-800">{label}</label>
                    {type === "select" ? (
                      <select className="w-full text-xs border border-amber-200 rounded px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-amber-400"
                        value={checkAnswers[key] || ""} onChange={(e) => setCheckAnswers((p) => ({ ...p, [key]: e.target.value }))}>
                        <option value="">Select...</option>
                        {(options || []).map((o) => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : (
                      <input type={type} className="w-full text-xs border border-amber-200 rounded px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-amber-400"
                        value={checkAnswers[key] || ""} onChange={(e) => setCheckAnswers((p) => ({ ...p, [key]: e.target.value }))} placeholder={label} />
                    )}
                  </div>
                ))}
                <Button onClick={handleEligibilityCheck} disabled={checking}
                  className="w-full bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold">
                  {checking ? "Checking..." : "Run Eligibility Check"}
                </Button>
                {checkResult && (
                  <div className={`p-3 rounded-lg border text-xs ${overallStyle[checkResult.overall]}`}>
                    <div className="font-bold text-sm">{overallLabel[checkResult.overall]}</div>
                    <div className="mt-1">
                      ✓ {checkResult.passed_count} passed · ✗ {checkResult.failed_count} failed · ? {checkResult.pending_count} pending
                    </div>
                    <div className="mt-2 text-[10px] opacity-75 leading-relaxed">{checkResult.disclaimer}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}