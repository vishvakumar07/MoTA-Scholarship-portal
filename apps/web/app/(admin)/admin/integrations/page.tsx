"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  ShieldAlert,
  ShieldOff,
  RefreshCw,
  Info,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Building2,
} from "lucide-react";

interface IntegrationConfig {
  integration: string;
  display_name: string;
  enabled: boolean;
  configured: boolean;
  mode: string;
  status: string;
  description: string;
  requires: string[];
}

interface IntegrationsResponse {
  integrations: IntegrationConfig[];
  notice: string;
  adapter_framework_version: string;
  data_source: string;
}

function StatusBadge({ status, mode }: { status: string; mode: string }) {
  if (mode === "live" && status === "LIVE_CONFIGURED") {
    return (
      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-xs font-medium">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        Live (Configured)
      </Badge>
    );
  }
  if (status === "REQUIRES_AUTHORIZED_ACCESS") {
    return (
      <Badge className="bg-amber-100 text-amber-800 border-amber-200 text-xs font-medium">
        <ShieldAlert className="w-3 h-3 mr-1" />
        Requires Authorized Access
      </Badge>
    );
  }
  if (status === "NOT_CONFIGURED") {
    return (
      <Badge className="bg-slate-100 text-slate-700 border-slate-200 text-xs font-medium">
        <ShieldOff className="w-3 h-3 mr-1" />
        Not Configured
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-xs">
      {status}
    </Badge>
  );
}

function IntegrationCard({
  config,
  onHealthCheck,
  healthLoading,
  healthResult,
}: {
  config: IntegrationConfig;
  onHealthCheck: (name: string) => void;
  healthLoading: string | null;
  healthResult: Record<string, string>;
}) {
  const isLoading = healthLoading === config.integration;
  const hcResult = healthResult[config.integration];

  return (
    <Card className="border border-slate-200 bg-white shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
              <Building2 className="w-4 h-4 text-indigo-600" />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold text-slate-800">
                {config.display_name}
              </CardTitle>
              <span className="text-xs text-slate-400 font-mono">{config.integration}</span>
            </div>
          </div>
          <StatusBadge status={config.status} mode={config.mode} />
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <p className="text-xs text-slate-600">{config.description}</p>

        {/* Status row */}
        <div className="rounded-md bg-slate-50 border border-slate-100 p-2.5 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">Mode</span>
            <span className={`font-mono font-semibold ${config.mode === "live" ? "text-emerald-600" : "text-slate-500"}`}>
              {config.mode.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">Enabled</span>
            <span className={config.enabled ? "text-emerald-600 font-semibold" : "text-slate-400"}>
              {config.enabled ? "Yes" : "No"}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">Credentials</span>
            <span className={config.configured ? "text-emerald-600 font-semibold" : "text-amber-600"}>
              {config.configured ? "Configured" : "Not configured"}
            </span>
          </div>
        </div>

        {/* Required env vars */}
        <div>
          <p className="text-[10px] text-slate-400 font-medium mb-1 uppercase tracking-wide">Required credentials</p>
          <div className="flex flex-wrap gap-1">
            {config.requires.map((req) => (
              <span key={req} className="text-[10px] font-mono bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                {req}
              </span>
            ))}
          </div>
        </div>

        {/* Health check result */}
        {hcResult && (
          <div className={`rounded-md px-2.5 py-2 text-xs flex items-center gap-1.5 ${
            hcResult === "SUCCESS"
              ? "bg-emerald-50 text-emerald-700"
              : hcResult === "DISABLED"
              ? "bg-slate-50 text-slate-500"
              : "bg-amber-50 text-amber-700"
          }`}>
            {hcResult === "SUCCESS" ? (
              <CheckCircle2 className="w-3 h-3 shrink-0" />
            ) : hcResult === "DISABLED" ? (
              <ShieldOff className="w-3 h-3 shrink-0" />
            ) : (
              <AlertTriangle className="w-3 h-3 shrink-0" />
            )}
            <span>Health check: <strong>{hcResult}</strong></span>
          </div>
        )}

        {/* Health check button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => onHealthCheck(config.integration)}
          disabled={isLoading}
          className="w-full text-xs h-7"
        >
          {isLoading ? (
            <>
              <RefreshCw className="w-3 h-3 mr-1.5 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <RefreshCw className="w-3 h-3 mr-1.5" />
              Run Health Check
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

export default function GovernmentIntegrationsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<IntegrationsResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<string | null>(null);
  const [healthResults, setHealthResults] = useState<Record<string, string>>({});

  const loadIntegrations = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await fetchApi<IntegrationsResponse>("/api/v1/admin/integrations");
    if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setData(res.data);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadIntegrations();
  }, [loadIntegrations]);

  const handleHealthCheck = async (integrationName: string) => {
    setHealthLoading(integrationName);
    const res = await fetchApi<{ status: string }>(
      `/api/v1/admin/integrations/${integrationName}/health-check`,
      { method: "POST" }
    );
    setHealthLoading(null);
    if (res.data?.status) {
      setHealthResults((prev) => ({ ...prev, [integrationName]: res.data!.status }));
    } else {
      setHealthResults((prev) => ({ ...prev, [integrationName]: "ERROR" }));
    }
  };

  const allNotConfigured =
    data?.integrations.every((i) => !i.enabled) ?? false;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <ShieldAlert className="w-5 h-5 text-indigo-600" />
                <h1 className="text-lg font-bold text-slate-800">
                  Government Integration Framework
                </h1>
              </div>
              <p className="text-sm text-slate-500">
                Ministry of Tribal Affairs — Integration Adapter Status
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadIntegrations}
              disabled={loading}
              className="text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6 space-y-5">

        {/* Governance Notice */}
        <Alert className="border-indigo-200 bg-indigo-50">
          <Info className="h-4 w-4 text-indigo-600" />
          <AlertTitle className="text-indigo-800 text-sm font-semibold">
            Integration-Ready Adapters — Not Live Government APIs
          </AlertTitle>
          <AlertDescription className="text-indigo-700 text-xs mt-1 leading-relaxed">
            Government integrations shown here are <strong>integration-ready adapter stubs</strong>.
            Actual verification requires <strong>authorized government credentials</strong>,
            API specifications, and access approval from the respective authority
            (UIDAI, DigiLocker, NSP, DBT Mission, MoTA IT Division).
            No real government API is connected at this time.
          </AlertDescription>
        </Alert>

        {/* All not configured banner */}
        {allNotConfigured && !loading && (
          <Alert className="border-amber-200 bg-amber-50">
            <ShieldOff className="h-4 w-4 text-amber-600" />
            <AlertTitle className="text-amber-800 text-sm font-semibold">
              No Integrations Currently Configured
            </AlertTitle>
            <AlertDescription className="text-amber-700 text-xs mt-1">
              All government integrations are in stub mode. Applications continue to be processed
              by human authorized officers without government API connectivity.
            </AlertDescription>
          </Alert>
        )}

        {/* Error state */}
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertTitle className="text-red-800 text-sm">Failed to load integrations</AlertTitle>
            <AlertDescription className="text-red-700 text-xs">{error}</AlertDescription>
          </Alert>
        )}

        {/* Integration grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Card key={i} className="border border-slate-200 animate-pulse">
                <CardContent className="p-4">
                  <div className="h-4 bg-slate-200 rounded w-1/2 mb-2" />
                  <div className="h-3 bg-slate-100 rounded w-3/4 mb-4" />
                  <div className="h-16 bg-slate-100 rounded" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : data ? (
          <>
            {/* Summary table */}
            <Card className="border border-slate-200 bg-white shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-slate-800">
                  Integration Configuration Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="text-left py-2 px-3 text-slate-500 font-medium">Integration</th>
                        <th className="text-center py-2 px-3 text-slate-500 font-medium">Enabled</th>
                        <th className="text-center py-2 px-3 text-slate-500 font-medium">Configured</th>
                        <th className="text-left py-2 px-3 text-slate-500 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.integrations.map((integ) => (
                        <tr key={integ.integration} className="border-b border-slate-50 hover:bg-slate-50">
                          <td className="py-2 px-3 font-medium text-slate-700">{integ.display_name}</td>
                          <td className="py-2 px-3 text-center">
                            {integ.enabled ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mx-auto" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-slate-300 mx-auto" />
                            )}
                          </td>
                          <td className="py-2 px-3 text-center">
                            {integ.configured ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mx-auto" />
                            ) : (
                              <XCircle className="w-3.5 h-3.5 text-slate-300 mx-auto" />
                            )}
                          </td>
                          <td className="py-2 px-3">
                            <StatusBadge status={integ.status} mode={integ.mode} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-[10px] text-slate-400 mt-3 italic">
                  Data source: {data.data_source} · Framework: v{data.adapter_framework_version}
                </p>
              </CardContent>
            </Card>

            {/* Integration cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.integrations.map((config) => (
                <IntegrationCard
                  key={config.integration}
                  config={config}
                  onHealthCheck={handleHealthCheck}
                  healthLoading={healthLoading}
                  healthResult={healthResults}
                />
              ))}
            </div>

            {/* Governance notice */}
            <Card className="border border-slate-200 bg-slate-50">
              <CardContent className="p-4">
                <div className="flex gap-2">
                  <Clock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-semibold text-slate-700 mb-1">
                      Requirements for Live Integration
                    </p>
                    <ul className="text-xs text-slate-500 space-y-1 list-disc list-inside">
                      <li>Authorized API credentials from the respective government authority</li>
                      <li>Official API specification and sandbox access</li>
                      <li>Data Processing Agreement (DPA) with the authority</li>
                      <li>Security review and penetration testing clearance</li>
                      <li>MoTA IT Division approval and infrastructure provisioning</li>
                    </ul>
                    <p className="text-[10px] text-slate-400 mt-2">
                      {data.notice}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </div>
  );
}
