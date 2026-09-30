import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Award,
  BookOpen,
  CheckCircle2,
  FileText,
  ArrowRight,
  Sparkles,
  ExternalLink,
  Users,
  GraduationCap,
  Globe2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* â”€â”€ Hero Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="relative overflow-hidden bg-gradient-to-b from-slate-900 via-blue-950 to-slate-900 text-white py-20 lg:py-28 px-4 sm:px-6 lg:px-8">
        {/* Decorative background grid and glowing circles */}
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-xs font-medium text-amber-300 shadow-sm backdrop-blur">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Digital India â€¢ Smart India Hackathon Prototype</span>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
            AI-Enabled Scholarship & Fellowship Management System
          </h1>

          <p className="max-w-3xl mx-auto text-base sm:text-xl text-slate-300 font-normal leading-relaxed">
            A secure, configurable, and transparent digital platform administering official Ministry of Tribal Affairs (MoTA) scholarship schemes for Scheduled Tribe students across India.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link href="/schemes">
              <Button size="lg" variant="motaAccent" className="w-full sm:w-auto font-semibold flex items-center space-x-2">
                <BookOpen className="w-5 h-5" />
                <span>Explore Official Schemes</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
            <Link href="/register">
              <Button size="lg" variant="outline" className="w-full sm:w-auto bg-slate-800/60 border-slate-700 text-white hover:bg-slate-700 hover:text-white font-semibold">
                Register as Applicant
              </Button>
            </Link>
          </div>

          {/* Quick Metrics Bar */}
          <div className="pt-10 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto border-t border-slate-800/80 text-left">
            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
              <div className="text-2xl font-bold text-amber-400">5</div>
              <div className="text-xs text-slate-400 mt-0.5">Core Official Schemes</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
              <div className="text-2xl font-bold text-emerald-400">265</div>
              <div className="text-xs text-slate-400 mt-0.5">Top-Class Institutes</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
              <div className="text-2xl font-bold text-blue-400">750/yr</div>
              <div className="text-xs text-slate-400 mt-0.5">NFST Fellowship Slots</div>
            </div>
            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
              <div className="text-2xl font-bold text-indigo-400">17</div>
              <div className="text-xs text-slate-400 mt-0.5">State Workflow Engine</div>
            </div>
          </div>
        </div>
      </section>

      {/* â”€â”€ Official Schemes Highlights â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-16 bg-slate-50 px-4 sm:px-6 lg:px-8 border-b">
        <div className="max-w-7xl mx-auto space-y-10">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <Badge variant="motaOfficial" className="text-xs font-semibold">
              Official MoTA Schemes
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Administered Schemes & Criteria
            </h2>
            <p className="text-sm text-slate-600">
              Data sourced directly from{" "}
              <a
                href="https://tribal.nic.in/ScholarshiP.aspx"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-700 font-medium hover:underline inline-flex items-center space-x-0.5"
              >
                <span>tribal.nic.in</span>
                <ExternalLink className="w-3 h-3 ml-0.5" />
              </a>
              . No estimated or fabricated criteria.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Pre & Post Matric */}
            <Card className="hover:shadow-md transition-shadow border-slate-200">
              <CardHeader className="space-y-2">
                <div className="flex justify-between items-start">
                  <Badge variant="motaCSS">Centrally Sponsored (CSS)</Badge>
                  <span className="text-xs font-semibold text-slate-500">Class IXâ€“PG</span>
                </div>
                <CardTitle className="text-lg font-bold text-slate-900">
                  Pre & Post-Matric Scholarships
                </CardTitle>
                <CardDescription className="text-xs">
                  Financial assistance to ST students studying from Class IX through secondary and post-matriculation courses.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-slate-600">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Family Income Limit:</span>
                  <span className="font-semibold text-slate-800">â‰¤ â‚¹2,50,000 / year</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Category:</span>
                  <span className="font-semibold text-slate-800">Scheduled Tribe (ST)</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Implementation:</span>
                  <span className="font-semibold text-slate-800">States & UTs via NSP</span>
                </div>
              </CardContent>
            </Card>

            {/* Top Class */}
            <Card className="hover:shadow-md transition-shadow border-slate-200">
              <CardHeader className="space-y-2">
                <div className="flex justify-between items-start">
                  <Badge variant="motaCentralSector">Central Sector (100%)</Badge>
                  <span className="text-xs font-semibold text-emerald-700">Higher Education</span>
                </div>
                <CardTitle className="text-lg font-bold text-slate-900">
                  National Scholarship â€” Top Class
                </CardTitle>
                <CardDescription className="text-xs">
                  Full financial support for meritorious ST students admitted to 265 notified premier institutions (IITs, NITs, IIMs, NLUs, etc.).
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-slate-600">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Family Income Limit:</span>
                  <span className="font-semibold text-slate-800">â‰¤ â‚¹6,00,000 / year</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Coverage:</span>
                  <span className="font-semibold text-slate-800">Tuition, Living & Books</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Institutions:</span>
                  <span className="font-semibold text-slate-800">265 Identified Institutes</span>
                </div>
              </CardContent>
            </Card>

            {/* Fellowship & Overseas */}
            <Card className="hover:shadow-md transition-shadow border-slate-200">
              <CardHeader className="space-y-2">
                <div className="flex justify-between items-start">
                  <Badge variant="motaCentralSector">Central Sector (100%)</Badge>
                  <span className="text-xs font-semibold text-indigo-700">Research & Global</span>
                </div>
                <CardTitle className="text-lg font-bold text-slate-900">
                  NFST & Overseas Scholarships
                </CardTitle>
                <CardDescription className="text-xs">
                  Fellowships for M.Phil / Ph.D. scholars in India (750 seats/yr) and National Overseas Scholarships for studies abroad (20 slots/yr).
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-slate-600">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">NFST Slots:</span>
                  <span className="font-semibold text-slate-800">750 Fellowships / year</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">NOS Slots:</span>
                  <span className="font-semibold text-slate-800">20 Awards / year</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">NOS Income Limit:</span>
                  <span className="font-semibold text-slate-800">â‰¤ â‚¹6,00,000 / year</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="text-center pt-4">
            <Link href="/schemes">
              <Button variant="outline" className="font-semibold">
                View All Scheme Guidelines & Required Documents
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* â”€â”€ Key Technical Pillars â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-16 bg-white px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Intelligent Platform Architecture
            </h2>
            <p className="text-sm text-slate-600">
              Engineered specifically for Smart India Hackathon standards with privacy, security, and auditability at its foundation.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
            <div className="space-y-3 p-6 rounded-xl border border-slate-100 bg-slate-50/50">
              <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-800 flex items-center justify-center font-bold">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Aadhaar & Banking Privacy</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Raw Aadhaar numbers are never stored; only cryptographically salted SHA-256 hashes are retained. Bank account numbers are protected with AES-256-GCM column encryption.
              </p>
            </div>

            <div className="space-y-3 p-6 rounded-xl border border-slate-100 bg-slate-50/50">
              <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center font-bold">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">AI Document Intelligence</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Multimodal classification, OCR text extraction, and cross-document anomaly detection with Google Gemini. Operates with automatic graceful fallback when API keys are absent.
              </p>
            </div>

            <div className="space-y-3 p-6 rounded-xl border border-slate-100 bg-slate-50/50">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Rule-Based Eligibility</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Clear deterministic validation. Scheme eligibility evaluates strictly according to official MoTA criteriaâ€”never leaving statutory benefit decisions to black-box heuristics.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

