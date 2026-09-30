"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { formatDate, formatDateTime, safeTruncate } from "@/lib/utils";
import { EmptyState } from "@/components/ui/empty-state";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  FileText, ArrowLeft, CheckCircle2, Clock, AlertTriangle,
  Upload, ShieldCheck, ChevronRight, RefreshCw, Eye,
  Lock, Save, Send, Calendar, Award, XCircle, Info,
  Check, HelpCircle, FileCheck, ExternalLink, AlertCircle
} from "lucide-react";

interface FormField {
  id: string;
  field_key: string;
  field_label: string;
  field_type: string;
  is_required: boolean;
  section: string;
  display_order: number;
  options?: any;
  validation_rules?: any;
  help_text?: string;
  conditional_logic?: any;
}

interface OpenDeficiency {
  id: string;
  deficiency_type: string;
  description: string;
  affected_document_type: string | null;
  officer_comment: string | null;
  response_deadline: string | null;
  status: string;
}

interface UploadedDocument {
  id: string;
  document_type: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  malware_scan_status: string;
  uploaded_at: string;
}

interface TimelineItem {
  status: string;
  label: string;
  icon: string;
  description: string;
  reached_at: string;
  change_reason?: string;
  system_note?: string;
  is_current: boolean;
}

const STATUS_CONFIG: Record<string, { color: string; label: string; icon: React.ElementType }> = {
  draft: { color: "bg-slate-100 text-slate-700 border-slate-200", label: "Draft", icon: FileText },
  submitted: { color: "bg-blue-100 text-blue-800 border-blue-200", label: "Submitted", icon: Clock },
  document_processing: { color: "bg-purple-100 text-purple-800 border-purple-200", label: "Document Processing", icon: RefreshCw },
  document_verification: { color: "bg-indigo-100 text-indigo-800 border-indigo-200", label: "Under Verification", icon: ShieldCheck },
  deficiency: { color: "bg-red-100 text-red-800 border-red-200", label: "Deficiency Raised", icon: AlertTriangle },
  resubmitted: { color: "bg-amber-100 text-amber-800 border-amber-200", label: "Resubmitted", icon: RefreshCw },
  eligibility_review: { color: "bg-yellow-100 text-yellow-800 border-yellow-200", label: "Eligibility Review", icon: CheckCircle2 },
  eligible: { color: "bg-emerald-100 text-emerald-800 border-emerald-200", label: "Eligible", icon: CheckCircle2 },
  ineligible: { color: "bg-red-100 text-red-800 border-red-200", label: "Ineligible", icon: XCircle },
  scrutiny: { color: "bg-cyan-100 text-cyan-800 border-cyan-200", label: "Scrutiny", icon: FileText },
  shortlisted: { color: "bg-teal-100 text-teal-800 border-teal-200", label: "Shortlisted", icon: Award },
  selection_review: { color: "bg-blue-100 text-blue-800 border-blue-200", label: "Selection Committee", icon: Clock },
  selected: { color: "bg-green-100 text-green-800 border-green-200", label: "Selected", icon: Award },
  not_selected: { color: "bg-gray-100 text-gray-800 border-gray-200", label: "Not Selected", icon: XCircle },
  completed: { color: "bg-emerald-100 text-emerald-800 border-emerald-200", label: "Disbursed", icon: CheckCircle2 },
  withdrawn: { color: "bg-gray-100 text-gray-700 border-gray-200", label: "Withdrawn", icon: XCircle },
};
export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [application, setApplication] = useState<any>(null);
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [openDeficiencies, setOpenDeficiencies] = useState<OpenDeficiency[]>([]);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [schemeDocuments, setSchemeDocuments] = useState<any[]>([]);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);

  // Navigation tab
  const [activeTab, setActiveTab] = useState<"form" | "documents" | "deficiencies" | "timeline">("form");

  // Form saving / submission state
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [declared, setDeclared] = useState(false);

  // Document upload state
  const [uploadingDoc, setUploadingDoc] = useState<string | null>(null);
  const [docUploadError, setDocUploadError] = useState<string | null>(null);

  // Deficiency response state
  const [deficiencyNotes, setDeficiencyNotes] = useState<Record<string, string>>({});
  const [respondingDeficiency, setRespondingDeficiency] = useState<string | null>(null);
  const [deficiencySuccess, setDeficiencySuccess] = useState<string | null>(null);

  useEffect(() => {
    loadApplicationData();
  }, [id]);

  const loadApplicationData = async () => {
    setLoading(true);
    const [appRes, docsRes, timelineRes] = await Promise.all([
      fetchApi(`/api/v1/applications/${id}`),
      fetchApi(`/api/v1/documents/${id}`),
      fetchApi(`/api/v1/applications/${id}/timeline`),
    ]);

    if (appRes.data) {
      const app = appRes.data.application;
      setApplication(app);
      setFormFields(appRes.data.form_fields || []);
      setOpenDeficiencies(appRes.data.open_deficiencies || []);
      setSchemeDocuments(appRes.data.required_documents || []);

      if (appRes.data.open_deficiencies && appRes.data.open_deficiencies.length > 0) {
        setActiveTab("deficiencies");
      }

      const ansMap: Record<string, any> = {};
      (app.answers || []).forEach((a: any) => {
        ansMap[a.field_key] = a.answer_value?.value ?? a.answer_value;
      });
      setAnswers(ansMap);
    } else {
      setError(appRes.error || "Failed to load application details.");
    }

    if (docsRes.data) {
      setDocuments(docsRes.data.documents || []);
    }

    if (timelineRes.data) {
      setTimeline(timelineRes.data.timeline || []);
    }

    setLoading(false);
  };

  const handleAnswerChange = (fieldKey: string, val: any) => {
    setAnswers((prev) => ({ ...prev, [fieldKey]: val }));
    setSaveSuccess(false);
  };

  const handleSaveDraft = async () => {
    if (saving) return;
    setSaving(true);
    setSaveSuccess(false);
    const answersList = Object.entries(answers).map(([key, val]) => ({
      field_key: key,
      answer_value: { value: val },
    }));

    const res = await fetchApi(`/api/v1/applications/${id}/save`, {
      method: "PUT",
      body: JSON.stringify({ answers: answersList }),
    });

    setSaving(false);
    if (res.data) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } else {
      alert(res.error || "Could not save draft.");
    }
  };

  const handleSubmitApplication = async () => {
    if (submitting) return;
    if (!declared) {
      setSubmitError("Please confirm the applicant declaration before submitting.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);

    const answersList = Object.entries(answers).map(([key, val]) => ({
      field_key: key,
      answer_value: { value: val },
    }));

    const res = await fetchApi(`/api/v1/applications/${id}/submit`, {
      method: "POST",
      body: JSON.stringify({
        answers: answersList,
        declaration_accepted: declared,
      }),
    });

    setSubmitting(false);
    if (res.data) {
      await loadApplicationData();
      setActiveTab("timeline");
    } else {
      setSubmitError(res.error || "Failed to submit application.");
    }
  };

  const handleDocumentUpload = async (docType: string, file: File) => {
    setUploadingDoc(docType);
    setDocUploadError(null);

    const formData = new FormData();
    formData.append("application_id", id);
    formData.append("document_type", docType);
    formData.append("file", file);

    const token = typeof window !== "undefined" ? localStorage.getItem("mota_access_token") : null;
    try {
      const resp = await fetch(`/api/v1/documents/upload`, {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });
      const data = await resp.json();
      if (resp.ok) {
        const docsRes = await fetchApi(`/api/v1/documents/${id}`);
        if (docsRes.data) setDocuments(docsRes.data.documents || []);
      } else {
        setDocUploadError(data.detail || "Document upload failed.");
      }
    } catch (e: any) {
      setDocUploadError(e.message || "Network error uploading file.");
    } finally {
      setUploadingDoc(null);
    }
  };

  const handleRespondDeficiency = async (deficiencyId: string) => {
    const note = deficiencyNotes[deficiencyId];
    if (!note || !note.trim()) {
      alert("Please enter an explanation note for the verification officer.");
      return;
    }

    setRespondingDeficiency(deficiencyId);
    setDeficiencySuccess(null);

    const res = await fetchApi(`/api/v1/applications/${id}/deficiencies/${deficiencyId}/respond`, {
      method: "POST",
      body: JSON.stringify({
        deficiency_id: deficiencyId,
        response_note: note.trim(),
      }),
    });

    setRespondingDeficiency(null);
    if (res.data) {
      setDeficiencySuccess("Your response and documents have been submitted to the scrutiny officer.");
      await loadApplicationData();
    } else {
      alert(res.error || "Could not submit deficiency response.");
    }
  };
  if (loading) {
    return (
      <div className="text-center py-20 bg-white border border-slate-200 rounded-lg shadow-sm">
        <div className="w-9 h-9 border-2 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <div className="text-sm font-semibold text-slate-700">Loading Application Dossier...</div>
        <div className="text-xs text-slate-400 mt-1">Fetching dynamic fields and official status</div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="space-y-4">
        <Link href="/applications">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Applications
          </Button>
        </Link>
        <Alert className="border-red-200 bg-red-50 text-red-800">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <AlertTitle className="text-sm font-bold">Application Error</AlertTitle>
          <AlertDescription className="text-xs mt-1">{error || "Application not found."}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const renderMalwareBadge = (status: string) => {
    switch (status) {
      case "clean":
        return <Badge className="bg-emerald-100 text-emerald-800 text-[10px] border-emerald-200">Malware Scan: Clean</Badge>;
      case "infected":
        return <Badge className="bg-red-100 text-red-800 text-[10px] border-red-200 font-bold">Malware Scan: Infected</Badge>;
      case "failed":
        return <Badge className="bg-red-100 text-red-800 text-[10px] border-red-200">Malware Scan: Failed</Badge>;
      case "unavailable":
        return <Badge className="bg-amber-100 text-amber-800 text-[10px] border-amber-200">Malware Scan: Unavailable (Manual Review)</Badge>;
      default:
        return <Badge className="bg-slate-100 text-slate-700 text-[10px] border-slate-200">Malware Scan: Pending</Badge>;
    }
  };

  const renderOfficerStatusBadge = (status: string) => {
    switch (status) {
      case "processing":
        return <Badge className="bg-purple-100 text-purple-800 text-[10px] border-purple-200">Processing...</Badge>;
      case "processed":
        return <Badge className="bg-blue-100 text-blue-800 text-[10px] border-blue-200">Awaiting Officer Review</Badge>;
      case "verified":
        return <Badge className="bg-emerald-100 text-emerald-800 text-[10px] border-emerald-200">Officer: Verified</Badge>;
      case "rejected":
        return <Badge className="bg-red-100 text-red-800 text-[10px] border-red-200">Officer: Rejected</Badge>;
      case "deficient":
        return <Badge className="bg-red-100 text-red-800 text-[10px] border-red-200 font-bold">Deficiency Raised</Badge>;
      default:
        return <Badge className="bg-blue-50 text-blue-800 text-[10px] border-blue-200 font-medium">Manual Verification Required</Badge>;
    }
  };

  const isDraft = application.status === "draft";
  const statusCfg = STATUS_CONFIG[application.status] || {
    color: "bg-slate-100 text-slate-700 border-slate-200",
    label: application.status,
    icon: FileText,
  };
  const StatusIcon = statusCfg.icon;

  const sections: Record<string, FormField[]> = {};
  formFields.forEach((f) => {
    const s = f.section || "General Information";
    if (!sections[s]) sections[s] = [];
    sections[s].push(f);
  });

  return (
    <div className="space-y-6 break-anywhere">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <Link href="/applications" className="inline-flex items-center gap-1.5 text-xs text-blue-900 font-semibold hover:underline mb-2">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to All Applications
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Application Dossier
            </h1>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${statusCfg.color}`}>
              <StatusIcon className="w-3.5 h-3.5" />
              {statusCfg.label}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-1 font-mono">
            <span>Ref No: <strong className="text-slate-800">{application.reference_number || "Draft (Pending Submission)"}</strong></span>
            {application.submitted_at && (
              <span>Submitted: <strong className="text-slate-800">{formatDateTime(application.submitted_at)}</strong></span>
            )}
          </div>
        </div>

        {isDraft && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveDraft}
              disabled={saving}
              className="text-xs gap-1.5 border-slate-300 hover:bg-slate-50"
            >
              <Save className="w-3.5 h-3.5 text-slate-600" />
              {saving ? "Saving..." : saveSuccess ? "Saved!" : "Save Draft"}
            </Button>
            <Button
              size="sm"
              onClick={() => {
                const el = document.getElementById("submission-declaration-card");
                if (el) el.scrollIntoView({ behavior: "smooth" });
              }}
              className="text-xs gap-1.5 bg-blue-900 hover:bg-blue-800 text-white font-semibold"
            >
              <Send className="w-3.5 h-3.5" />
              Submit Application
            </Button>
          </div>
        )}
      </div>

      {/* Urgent Deficiency Notice */}
      {openDeficiencies.length > 0 && (
        <Alert className="border-red-300 bg-red-50 text-red-900 shadow-sm animate-fade-in">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <div className="flex-1">
            <AlertTitle className="text-sm font-bold text-red-800 flex items-center justify-between">
              <span>Immediate Action Required: Document Deficiency Raised ({openDeficiencies.length})</span>
              <button
                onClick={() => setActiveTab("deficiencies")}
                className="text-xs underline font-semibold text-red-700 hover:text-red-900"
              >
                Go to Resolution &rarr;
              </button>
            </AlertTitle>
            <AlertDescription className="text-xs text-red-700 mt-1 leading-relaxed">
              The verification committee has identified discrepancies or missing certificates in your application.
              Review the requested documents under the <strong>Deficiencies</strong> tab and submit your response promptly.
            </AlertDescription>
          </div>
        </Alert>
      )}

      {/* Submitted locked banner */}
      {!isDraft && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3.5 flex items-start gap-3 text-xs text-blue-900">
          <Lock className="w-4 h-4 text-blue-700 shrink-0 mt-0.5" />
          <div>
            <strong>Application Submitted & Locked.</strong> This record is now under official scrutiny by the Ministry of Tribal Affairs.
            Fields are view-only to maintain strict audit integrity. Any required corrections will be requested via the Deficiencies tab.
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTab("form")}
          className={`px-4 py-2.5 border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === "form"
              ? "border-blue-900 text-blue-900 bg-blue-50/50"
              : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"
          }`}
        >
          <FileText className="w-4 h-4" />
          Application Details
        </button>

        <button
          onClick={() => setActiveTab("documents")}
          className={`px-4 py-2.5 border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === "documents"
              ? "border-blue-900 text-blue-900 bg-blue-50/50"
              : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"
          }`}
        >
          <Upload className="w-4 h-4" />
          Documents & Certificates ({documents.length})
        </button>

        <button
          onClick={() => setActiveTab("deficiencies")}
          className={`px-4 py-2.5 border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === "deficiencies"
              ? "border-red-600 text-red-700 bg-red-50/50"
              : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"
          }`}
        >
          <AlertTriangle className={`w-4 h-4 ${openDeficiencies.length > 0 ? "text-red-600 animate-pulse" : ""}`} />
          Deficiencies & Scrutiny
          {openDeficiencies.length > 0 && (
            <span className="bg-red-600 text-white rounded-full px-1.5 py-0.2 text-[10px] font-bold">
              {openDeficiencies.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("timeline")}
          className={`px-4 py-2.5 border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap ${
            activeTab === "timeline"
              ? "border-blue-900 text-blue-900 bg-blue-50/50"
              : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"
          }`}
        >
          <Clock className="w-4 h-4" />
          Official Tracking Timeline
        </button>
      </div>

      {/* TAB 1: FORM */}
      {activeTab === "form" && (
        <div className="space-y-6 anim-fade-in">
          {Object.entries(sections).map(([sectionTitle, fields]) => (
            <Card key={sectionTitle} className="border-slate-200 bg-white shadow-sm">
              <CardHeader className="bg-slate-50/70 border-b border-slate-100 py-3.5 px-5">
                <CardTitle className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                  <span className="w-1.5 h-3.5 bg-blue-900 rounded-sm"></span>
                  {sectionTitle}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {fields.map((field) => {
                    const value = answers[field.field_key] ?? "";
                    const isRequired = field.is_required;

                    return (
                      <div key={field.id} className={field.field_type === "textarea" ? "sm:col-span-2 space-y-1.5" : "space-y-1.5"}>
                        <div className="flex items-center justify-between">
                          <Label htmlFor={field.field_key} className="text-xs font-semibold text-slate-700">
                            {field.field_label}
                            {isRequired && <span className="text-red-500 ml-1">*</span>}
                          </Label>
                          {field.help_text && (
                            <span className="text-[11px] text-slate-400 italic">
                              {field.help_text}
                            </span>
                          )}
                        </div>

                        {field.field_type === "select" ? (
                          <select
                            id={field.field_key}
                            value={value}
                            disabled={!isDraft}
                            onChange={(e) => handleAnswerChange(field.field_key, e.target.value)}
                            className="w-full h-9 rounded-md border border-slate-300 bg-white px-3 py-1 text-xs shadow-sm focus:border-blue-900 focus:outline-none disabled:bg-slate-100 disabled:text-slate-500"
                          >
                            <option value="">-- Select an option --</option>
                            {(field.options?.choices || field.options || []).map((opt: any) => {
                              const optVal = typeof opt === "string" ? opt : opt.value;
                              const optLabel = typeof opt === "string" ? opt : opt.label;
                              return (
                                <option key={optVal} value={optVal}>
                                  {optLabel}
                                </option>
                              );
                            })}
                          </select>
                        ) : field.field_type === "textarea" ? (
                          <textarea
                            id={field.field_key}
                            value={value}
                            disabled={!isDraft}
                            rows={3}
                            onChange={(e) => handleAnswerChange(field.field_key, e.target.value)}
                            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs shadow-sm focus:border-blue-900 focus:outline-none disabled:bg-slate-100 disabled:text-slate-500"
                            placeholder={`Enter ${field.field_label.toLowerCase()}`}
                          />
                        ) : (
                          <Input
                            id={field.field_key}
                            type={
                              field.field_type === "number"
                                ? "number"
                                : field.field_type === "date"
                                ? "date"
                                : field.field_type === "email"
                                ? "email"
                                : "text"
                            }
                            value={value}
                            disabled={!isDraft}
                            onChange={(e) => handleAnswerChange(field.field_key, e.target.value)}
                            placeholder={`Enter ${field.field_label.toLowerCase()}`}
                            className="h-9 text-xs bg-white border-slate-300 focus:border-blue-900 disabled:bg-slate-100 disabled:text-slate-500"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Declaration Card for Drafts */}
          {isDraft && (
            <Card id="submission-declaration-card" className="border-blue-200 bg-blue-50/30 shadow-sm">
              <CardHeader className="py-3.5 px-5 border-b border-blue-100 bg-blue-50/60">
                <CardTitle className="text-sm font-bold text-blue-900 uppercase tracking-wider flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-blue-800" />
                  Statutory Applicant Declaration (Ministry of Tribal Affairs)
                </CardTitle>
              </CardHeader>
              <CardContent className="p-5 space-y-4">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id="mota-declaration"
                    checked={declared}
                    onChange={(e) => setDeclared(e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-900 focus:ring-blue-900"
                  />
                  <label htmlFor="mota-declaration" className="text-xs text-slate-700 leading-relaxed cursor-pointer">
                    I hereby solemnly declare that I belong to a Scheduled Tribe (ST) community as recognized by the Government of India.
                    All information furnished in this application and certificates uploaded are true, complete, and authentic to the best of my knowledge.
                    I acknowledge that furnishing false declarations or forged certificates constitutes a criminal offense under the Indian Penal Code and
                    will result in immediate disqualification, recovery of scholarship amounts with interest, and permanent debarment.
                  </label>
                </div>

                {submitError && (
                  <Alert className="border-red-300 bg-red-50 text-red-800 text-xs py-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                    <AlertDescription>{submitError}</AlertDescription>
                  </Alert>
                )}

                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-blue-100">
                  <div className="text-[11px] text-slate-500">
                    Once submitted, you will receive an official Reference Number for physical and portal verification.
                  </div>
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSaveDraft}
                      disabled={saving}
                      className="text-xs flex-1 sm:flex-initial"
                    >
                      {saving ? "Saving..." : "Save Draft"}
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSubmitApplication}
                      disabled={submitting || !declared}
                      className="text-xs bg-blue-900 hover:bg-blue-800 text-white font-bold px-6 flex-1 sm:flex-initial"
                    >
                      {submitting ? "Submitting Application..." : "Submit Official Application"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
      {/* TAB 2: DOCUMENTS */}
      {activeTab === "documents" && (
        <div className="space-y-6 anim-fade-in">
          <Card className="border-slate-200 bg-white shadow-sm">
            <CardHeader className="py-4 px-5 border-b border-slate-100">
              <CardTitle className="text-sm font-bold text-slate-800 flex items-center justify-between">
                <span>Required Documents & Enclosures</span>
                <span className="text-xs font-normal text-slate-500">Maximum size: 10MB per document (PDF, JPG, PNG)</span>
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Upload clear scanned copies (DigiLocker Integration Required; manual officer verification applies).
                Each uploaded certificate undergoes separate malware scanning, OCR extraction, and manual verification by MoTA scrutiny officers.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              {docUploadError && (
                <Alert className="border-red-200 bg-red-50 text-red-800 text-xs py-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                  <AlertDescription>{docUploadError}</AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(schemeDocuments.length > 0
                  ? schemeDocuments.map((sd: any) => ({
                      key: sd.document_type_code,
                      title: sd.document_display_name,
                      required: sd.is_mandatory,
                      desc: sd.description || "Official verification document",
                    }))
                  : [
                      { key: "caste_certificate", title: "ST Caste Certificate", required: true, desc: "Issued by competent revenue authority (Tahsildar / SDO / DC)" },
                      { key: "income_certificate", title: "Income Certificate", required: true, desc: "Valid for current financial year from competent revenue authority" },
                      { key: "marksheet", title: "Marksheet / Academic Record", required: true, desc: "Previous qualifying examination marksheet / degree" },
                      { key: "fee_receipt", title: "Fee Receipt / Admission Letter", required: true, desc: "Proof of enrollment from recognized institution" },
                      { key: "bank_passbook", title: "Bank Passbook / Cancelled Cheque", required: false, desc: "Aadhaar-seeded bank account details for DBT disbursement" },
                      { key: "disability_certificate", title: "Disability Certificate (PwD)", required: false, desc: "UDID card or medical board certificate if applicable" },
                    ]
                ).map((docItem: any) => {
                  const existing = documents.filter((d) => d.document_type === docItem.key);
                  const latest = existing[existing.length - 1];

                  return (
                    <div key={docItem.key} className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-3 card-interactive transition-all">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                            {docItem.title}
                            {docItem.required && <span className="text-red-500 font-bold">*</span>}
                          </div>
                          <div className="text-[11px] text-slate-500 mt-0.5">{docItem.desc}</div>
                        </div>
                        {latest ? (
                          <Badge className="bg-slate-100 text-slate-800 text-[10px] font-semibold border-slate-200">
                            Uploaded
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-slate-400 text-[10px]">
                            {docItem.required ? "Required" : "Optional"}
                          </Badge>
                        )}
                      </div>

                      {/* Government Database Status banner */}
                      <div className="text-[10px] text-slate-500 bg-white p-2 rounded border border-slate-200/80 font-mono">
                        Database Integration: <strong className="text-amber-700">Integration Required</strong> (Manual Verification Required by MoTA Officers)
                      </div>

                      {latest && (
                        <div className="bg-white border border-slate-200 rounded p-2.5 text-xs space-y-2">
                          <div className="flex items-center justify-between overflow-hidden">
                            <div className="flex items-center gap-2 truncate">
                              <FileCheck className="w-4 h-4 text-blue-900 shrink-0" />
                              <span className="truncate font-mono text-[11px] text-slate-700 font-semibold">{latest.original_filename}</span>
                            </div>
                            <span className="text-[10px] text-slate-400 shrink-0 font-mono">
                              {(latest.file_size_bytes / 1024).toFixed(0)} KB
                            </span>
                          </div>

                          {/* Distinct 4-part Verification Status Display */}
                          <div className="grid grid-cols-2 gap-1.5 pt-1 border-t border-slate-100">
                            <div>
                              <div className="text-[9px] text-slate-400 uppercase font-semibold">1. Malware Scan</div>
                              <div>{renderMalwareBadge(latest.malware_scan_status)}</div>
                            </div>
                            <div>
                              <div className="text-[9px] text-slate-400 uppercase font-semibold">2. Administrative Review</div>
                              <div>{renderOfficerStatusBadge(latest.status)}</div>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="flex items-center gap-2 pt-1">
                        <input
                          type="file"
                          id={`file-${docItem.key}`}
                          accept=".pdf,.jpg,.jpeg,.png"
                          className="hidden"
                          onChange={(e) => {
                            if (e.target.files?.[0]) {
                              handleDocumentUpload(docItem.key, e.target.files[0]);
                            }
                          }}
                        />
                        <label
                          htmlFor={`file-${docItem.key}`}
                          className={`cursor-pointer inline-flex items-center justify-center gap-1.5 w-full py-1.5 px-3 rounded text-xs font-semibold border transition-colors ${
                            uploadingDoc === docItem.key
                              ? "bg-slate-200 text-slate-500 border-slate-300"
                              : latest
                              ? "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                              : "bg-blue-900 text-white border-blue-900 hover:bg-blue-800"
                          }`}
                        >
                          <Upload className="w-3.5 h-3.5" />
                          {uploadingDoc === docItem.key
                            ? "Uploading..."
                            : latest
                            ? "Replace Document"
                            : "Upload Document"}
                        </label>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Explicit Government Verification Disclaimer */}
              <div className="text-[11px] text-slate-500 bg-amber-50/60 border border-amber-200 rounded p-3 leading-relaxed mt-4">
                <strong>Important Official Notice:</strong> Malware scanning, OCR extraction, and administrative scrutiny are completely distinct processes.
                A clean or pending malware scan does NOT imply that a government officer has verified the document or certified your ST caste or income status.
                All certificates undergo formal manual verification by authorized MoTA scrutiny officers.
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* TAB 3: DEFICIENCIES */}
      {activeTab === "deficiencies" && (
        <div className="space-y-6 anim-fade-in">
          {deficiencySuccess && (
            <Alert className="border-emerald-300 bg-emerald-50 text-emerald-800 shadow-sm">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              <AlertTitle className="text-xs font-bold">Response Submitted</AlertTitle>
              <AlertDescription className="text-xs mt-1">{deficiencySuccess}</AlertDescription>
            </Alert>
          )}

          {openDeficiencies.length === 0 ? (
            <div className="text-center py-16 bg-white border border-slate-200 rounded-lg p-6">
              <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-3 text-emerald-600">
                <Check className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-slate-800">No Open Deficiencies</h2>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                Your application has no pending deficiency notices or scrutiny queries.
                If the verification officer requires additional certificates or clarifications, they will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {openDeficiencies.map((def) => (
                <Card key={def.id} className="border-red-300 bg-white shadow-sm overflow-hidden">
                  <div className="bg-red-50 border-b border-red-200 px-5 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      <span className="text-xs font-bold text-red-900 uppercase tracking-wider">
                        Deficiency Type: {def.deficiency_type}
                      </span>
                    </div>
                    {def.response_deadline && (
                      <span className="text-xs font-semibold text-red-700 bg-red-100 px-2 py-0.5 rounded border border-red-200">
                        Deadline: {formatDate(def.response_deadline)}
                      </span>
                    )}
                  </div>

                  <CardContent className="p-5 space-y-4">
                    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 text-xs">
                      <div className="font-semibold text-slate-700 mb-1">Scrutiny Officer Observation:</div>
                      <div className="text-slate-600 leading-relaxed">{def.description}</div>
                      {def.affected_document_type && (
                        <div className="mt-2 text-[11px] text-blue-900 font-mono font-medium">
                          Affected Document: <strong>{def.affected_document_type}</strong>
                        </div>
                      )}
                    </div>

                    <div className="space-y-2 pt-2">
                      <Label htmlFor={`note-${def.id}`} className="text-xs font-bold text-slate-800">
                        Applicant Clarification / Response Note:
                      </Label>
                      <textarea
                        id={`note-${def.id}`}
                        rows={3}
                        value={deficiencyNotes[def.id] || ""}
                        onChange={(e) =>
                          setDeficiencyNotes((prev) => ({ ...prev, [def.id]: e.target.value }))
                        }
                        placeholder="Provide your clarification or explain the replacement document attached..."
                        className="w-full rounded-md border border-slate-300 p-3 text-xs shadow-sm focus:border-blue-900 focus:outline-none"
                      />
                    </div>

                    {def.affected_document_type && (
                      <div className="border border-dashed border-slate-300 rounded-lg p-3 bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <div className="font-semibold text-slate-800">Attach Corrected Document</div>
                          <div className="text-[11px] text-slate-500">Upload replacement for {def.affected_document_type}</div>
                        </div>
                        <div>
                          <input
                            type="file"
                            id={`def-file-${def.id}`}
                            accept=".pdf,.jpg,.jpeg,.png"
                            className="hidden"
                            onChange={(e) => {
                              if (e.target.files?.[0]) {
                                handleDocumentUpload(def.affected_document_type!, e.target.files[0]);
                              }
                            }}
                          />
                          <label
                            htmlFor={`def-file-${def.id}`}
                            className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-white border border-slate-300 hover:bg-slate-100 text-slate-700"
                          >
                            <Upload className="w-3.5 h-3.5" />
                            Upload Replacement File
                          </label>
                        </div>
                      </div>
                    )}

                    <div className="flex justify-end pt-2">
                      <Button
                        size="sm"
                        onClick={() => handleRespondDeficiency(def.id)}
                        disabled={respondingDeficiency === def.id}
                        className="bg-red-700 hover:bg-red-800 text-white font-bold text-xs px-5 shadow-sm"
                      >
                        {respondingDeficiency === def.id ? "Submitting Response..." : "Submit Official Clarification"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: TIMELINE */}
      {activeTab === "timeline" && (
        <Card className="border-slate-200 bg-white shadow-sm anim-fade-in">
          <CardHeader className="py-4 px-5 border-b border-slate-100">
            <CardTitle className="text-sm font-bold text-slate-800">
              Official Workflow Tracking & Audit History
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Complete traceable timeline of your application lifecycle as recorded by the Ministry of Tribal Affairs engine.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {timeline.length === 0 ? (
              <EmptyState
                title="No Timeline Records Yet"
                description="Official workflow tracking events will be recorded here as your application is processed through verification and scrutiny stages."
              />
            ) : (
              <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pl-6 py-2">
                {timeline.map((item, idx) => {
                  return (
                    <div key={idx} className="relative group">
                      <div
                        className={`absolute -left-[35px] top-0 w-7 h-7 rounded-full flex items-center justify-center text-white text-xs border-2 border-white shadow-sm ${
                          item.is_current
                            ? "bg-blue-900 ring-4 ring-blue-200/80 animate-pulse shadow-md"
                            : "bg-slate-400"
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">{item.label}</span>
                          {item.is_current && (
                            <Badge className="bg-blue-100 text-blue-900 border-blue-200 text-[10px]">
                              Current Stage
                            </Badge>
                          )}
                          <span className="text-[11px] text-slate-400 font-mono">
                            {formatDateTime(item.reached_at)}
                          </span>
                        </div>

                        <p className="text-xs text-slate-600">{item.description}</p>

                        {item.change_reason && (
                          <div className="text-[11px] text-slate-500 italic mt-1 bg-slate-50 p-2 rounded border border-slate-100">
                            Reason: {item.change_reason}
                          </div>
                        )}

                        {item.system_note && (
                          <div className="text-[11px] text-blue-800 font-mono bg-blue-50/50 p-1.5 rounded">
                            Audit Note: {item.system_note}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}