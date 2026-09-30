"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  BookOpen, ExternalLink, Calendar, FileText, ChevronRight,
  Search, Info, CheckCircle2, Clock, Shield,
} from "lucide-react";

interface Scheme {
  id: string;
  code: string;
  name: string;
  short_name: string;
  scheme_type: string;
  status: string;
  official_url: string | null;
  portal_url: string | null;
  description: string | null;
  display_order: number;
}

const TYPE_COLORS: Record<string, string> = {
  pre_matric: "bg-blue-100 text-blue-800",
  post_matric: "bg-indigo-100 text-indigo-800",
  top_class: "bg-purple-100 text-purple-800",
  research: "bg-amber-100 text-amber-800",
  overseas: "bg-teal-100 text-teal-800",
  fellowship: "bg-emerald-100 text-emerald-800",
};

const TYPE_LABELS: Record<string, string> = {
  pre_matric: "Pre-Matric",
  post_matric: "Post-Matric",
  top_class: "Top Class",
  research: "Research / NFS",
  overseas: "Overseas / NOS",
  fellowship: "Fellowship",
};

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sourceNote, setSourceNote] = useState("");

  useEffect(() => {
    fetchApi("/api/v1/schemes").then((res) => {
      if (res.data) {
        setSchemes(res.data.schemes || []);
        setSourceNote(res.data.source_note || "");
      } else if (res.error) {
        setError(res.error);
      }
      setLoading(false);
    });
  }, []);

  const filtered = schemes.filter((s) =>
    search === "" ||
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.code.toLowerCase().includes(search.toLowerCase()) ||
    (s.description || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Scheme Discovery</h1>
        <p className="text-sm text-slate-500 mt-1">
          Browse official MoTA scholarship and fellowship schemes. Only schemes configured in the system are shown.
        </p>
      </div>

      {/* Source note */}
      {sourceNote && (
        <Alert className="border-blue-200 bg-blue-50">
          <Info className="w-4 h-4 text-blue-600" />
          <AlertDescription className="text-blue-700 text-xs">{sourceNote}</AlertDescription>
        </Alert>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search schemes by name or code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
        />
      </div>

      {/* Schemes */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="border-slate-200 animate-pulse">
              <CardContent className="p-6 space-y-3">
                <div className="h-4 bg-slate-200 rounded w-3/4" />
                <div className="h-3 bg-slate-100 rounded w-full" />
                <div className="h-3 bg-slate-100 rounded w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-bold text-slate-700">
            {search ? "No schemes match your search" : "No schemes available"}
          </h3>
          <p className="text-sm text-slate-500 mt-2">
            {search ? "Try a different search term." : "Schemes will appear here once configured by the administrator."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((scheme) => (
            <Link key={scheme.id} href={`/schemes/${scheme.code}`}>
              <Card className="border-slate-200 hover:border-blue-300 hover:shadow-lg transition-all cursor-pointer group h-full">
                <CardContent className="p-5 flex flex-col h-full">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="w-10 h-10 bg-blue-900 rounded-xl flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-5 h-5 text-amber-300" />
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${TYPE_COLORS[scheme.scheme_type] || "bg-slate-100 text-slate-700"}`}>
                        {TYPE_LABELS[scheme.scheme_type] || scheme.scheme_type}
                      </span>
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="text-[11px] font-mono text-slate-400 mb-1">{scheme.code}</div>
                    <h3 className="font-bold text-slate-900 text-sm leading-tight group-hover:text-blue-800 transition-colors">
                      {scheme.name}
                    </h3>
                    {scheme.description && (
                      <p className="text-xs text-slate-500 mt-2 line-clamp-3">{scheme.description}</p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {scheme.official_url && (
                        <a
                          href={scheme.official_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-[11px] text-blue-600 hover:underline flex items-center gap-1"
                        >
                          <ExternalLink className="w-3 h-3" /> Official Source
                        </a>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-blue-700 font-semibold group-hover:gap-2 transition-all">
                      View Details <ChevronRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="text-center text-xs text-slate-400">
          Showing {filtered.length} of {schemes.length} scheme{schemes.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
