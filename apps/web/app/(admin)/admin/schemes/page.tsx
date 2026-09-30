"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface RuleConfig {
  id: string;
  ruleKey: string;
  field: string;
  operator: string;
  expectedValue: string;
  severity: "HARD_STOP" | "WARNING" | "INFO";
  isOfficialSourceConfirmed: boolean;
  sourceUrl?: string;
  explanation?: string;
}

interface FormFieldConfig {
  id: string;
  fieldKey: string;
  label: string;
  type: string;
  required: boolean;
  helpText?: string;
}

export default function AdminSchemesConfigPage() {
  const [schemeCode, setSchemeCode] = useState("POST_MATRIC");
  const [versionNumber, setVersionNumber] = useState("1.0");
  const [versionStatus, setVersionStatus] = useState<"DRAFT" | "PUBLISHED">("PUBLISHED");

  const [rules, setRules] = useState<RuleConfig[]>([
    {
      id: "1",
      ruleKey: "caste_requirement",
      field: "applicant.caste_category",
      operator: "eq",
      expectedValue: "ST",
      severity: "HARD_STOP",
      isOfficialSourceConfirmed: true,
      sourceUrl: "https://tribal.nic.in/ScholarshiP.aspx",
      explanation: "Must belong to ST community with valid certificate.",
    },
    {
      id: "2",
      ruleKey: "income_limit_annual",
      field: "applicant.annual_family_income",
      operator: "lte",
      expectedValue: "250000",
      severity: "HARD_STOP",
      isOfficialSourceConfirmed: true,
      sourceUrl: "https://tribal.nic.in/ScholarshiP.aspx",
      explanation: "Annual family income must be <= Rs. 2,50,000.",
    },
    {
      id: "3",
      ruleKey: "attendance_norm",
      field: "academic.attendance_percentage",
      operator: "gte",
      expectedValue: "75",
      severity: "WARNING",
      isOfficialSourceConfirmed: false,
      explanation: "OFFICIAL SOURCE REQUIRED",
    },
  ]);

  const [formFields, setFormFields] = useState<FormFieldConfig[]>([
    { id: "1", fieldKey: "caste_certificate_no", label: "ST Caste Certificate No.", type: "text", required: true },
    { id: "2", fieldKey: "annual_family_income", label: "Annual Family Income (INR)", type: "number", required: true },
  ]);

  const [newRuleKey, setNewRuleKey] = useState("");
  const [newField, setNewField] = useState("");
  const [newOperator, setNewOperator] = useState("lte");
  const [newExpectedValue, setNewExpectedValue] = useState("");
  const [isOfficialConfirmed, setIsOfficialConfirmed] = useState(false);

  const handleAddRule = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleKey || !newField) return;

    if (versionStatus === "PUBLISHED") {
      alert("Published version rules are immutable! Creating a new DRAFT version 1.1...");
      setVersionNumber("1.1");
      setVersionStatus("DRAFT");
    }

    const newRule: RuleConfig = {
      id: Date.now().toString(),
      ruleKey: newRuleKey,
      field: newField,
      operator: newOperator,
      expectedValue: newExpectedValue,
      severity: "HARD_STOP",
      isOfficialSourceConfirmed: isOfficialConfirmed,
      explanation: isOfficialConfirmed ? "Verified rule." : "OFFICIAL SOURCE REQUIRED",
    };

    setRules([...rules, newRule]);
    setNewRuleKey("");
    setNewField("");
    setNewExpectedValue("");
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scheme Configuration & Rule Engine Manager</h1>
          <p className="text-sm text-gray-600">Ministry of Tribal Affairs — Admin Interface</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium">Version {versionNumber}</span>
          <Badge variant={versionStatus === "PUBLISHED" ? "default" : "secondary"}>
            {versionStatus}
          </Badge>
          {versionStatus === "PUBLISHED" && (
            <Badge variant="outline" className="text-xs text-amber-600 border-amber-400">
              IMMUTABLE
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rules Card */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Versioned Eligibility Rules</h2>
          <div className="space-y-4 mb-6">
            {rules.map((r) => (
              <div key={r.id} className="p-3 border rounded-lg bg-gray-50 flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold">{r.ruleKey}</span>
                    <Badge variant={r.severity === "HARD_STOP" ? "destructive" : "secondary"} className="text-xs">
                      {r.severity}
                    </Badge>
                    {!r.isOfficialSourceConfirmed && (
                      <Badge variant="outline" className="text-xs border-amber-500 text-amber-700 bg-amber-50">
                        OFFICIAL SOURCE REQUIRED
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mt-1">
                    <code className="bg-gray-200 px-1 py-0.5 rounded">{r.field}</code> {r.operator} <strong>{r.expectedValue}</strong>
                  </p>
                  <p className="text-xs italic text-gray-500 mt-1">{r.explanation}</p>
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleAddRule} className="border-t pt-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-800">Add / Edit Rule</h3>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="text-xs">Rule Key</Label>
                <Input value={newRuleKey} onChange={(e) => setNewRuleKey(e.target.value)} placeholder="e.g. age_limit" className="h-8 text-xs" />
              </div>
              <div>
                <Label className="text-xs">Field Path</Label>
                <Input value={newField} onChange={(e) => setNewField(e.target.value)} placeholder="applicant.age" className="h-8 text-xs" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="text-xs">Operator</Label>
                <select value={newOperator} onChange={(e) => setNewOperator(e.target.value)} className="w-full h-8 text-xs border rounded px-2">
                  <option value="lte">lte (&lt;=)</option>
                  <option value="gte">gte (&gt;=)</option>
                  <option value="eq">eq (==)</option>
                  <option value="in">in (list)</option>
                </select>
              </div>
              <div>
                <Label className="text-xs">Expected Value</Label>
                <Input value={newExpectedValue} onChange={(e) => setNewExpectedValue(e.target.value)} placeholder="e.g. 250000" className="h-8 text-xs" />
              </div>
            </div>
            <div className="flex items-center gap-2 pt-1">
              <input type="checkbox" id="official_chk" checked={isOfficialConfirmed} onChange={(e) => setIsOfficialConfirmed(e.target.checked)} />
              <Label htmlFor="official_chk" className="text-xs text-gray-700">Official MoTA Source Confirmed</Label>
            </div>
            <Button type="submit" size="sm" className="w-full">
              {versionStatus === "PUBLISHED" ? "Save (Spawns New Draft)" : "Add Rule to Draft"}
            </Button>
          </form>
        </Card>

        {/* Dynamic Form Schema Card */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Dynamic Schema-Driven Form Fields</h2>
          <div className="space-y-3">
            {formFields.map((f) => (
              <div key={f.id} className="p-3 border rounded-lg bg-gray-50 flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{f.label}</span>
                    <Badge variant="outline" className="text-xs">{f.type}</Badge>
                    {f.required && <Badge className="text-xs bg-red-100 text-red-700 hover:bg-red-100">Required</Badge>}
                  </div>
                  <p className="text-xs font-mono text-gray-500 mt-0.5">key: {f.fieldKey}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
