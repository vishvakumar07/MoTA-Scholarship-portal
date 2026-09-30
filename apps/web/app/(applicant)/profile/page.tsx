"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { formatIndianLakhsCrores, sanitizeInput } from "@/lib/utils";
import { CheckCircle2, AlertCircle, User, GraduationCap, Home, Plus, Trash2, Save, ShieldCheck } from "lucide-react";

const GENDER_OPTIONS = ["male", "female", "transgender", "prefer_not_to_say"];
const EDUCATION_LEVELS = [
  "pre_matric", "matric", "post_matric", "graduate", "post_graduate", "m_phil", "phd", "other"
];
const INDIAN_STATES = [
  "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana",
  "Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur",
  "Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
  "Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Andaman and Nicobar Islands","Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu","Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"
];

function SectionTitle({ icon: Icon, title, subtitle }: { icon: React.ElementType; title: string; subtitle?: string }) {
  return (
    <div className="flex items-start gap-3 pb-4 border-b border-slate-100 mb-4">
      <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
        <Icon className="w-4 h-4 text-blue-700" />
      </div>
      <div>
        <h2 className="font-bold text-slate-900">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [form, setForm] = useState<any>({});
  const [educations, setEducations] = useState<any[]>([]);

  useEffect(() => {
    fetchApi("/api/v1/applicant/profile").then((res) => {
      if (res.data) {
        setProfile(res.data);
        setForm(res.data);
        setEducations(res.data.education_records || []);
      }
      setLoading(false);
    });
  }, []);

  const updateField = (key: string, value: any) => {
    setForm((prev: any) => ({ ...prev, [key]: value }));
    if (fieldErrors[key]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const addEducation = () => {
    setEducations((prev) => [...prev, {
      education_level: "graduate",
      institution_name: "", course_name: "", year_of_passing: "",
      percentage_or_cgpa: "", board_or_university: "", is_current: false,
    }]);
  };

  const removeEducation = (idx: number) => {
    setEducations((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateEducation = (idx: number, key: string, value: any) => {
    setEducations((prev) => prev.map((e, i) => i === idx ? { ...e, [key]: value } : e));
  };

  const validateForm = (): boolean => {
    const errs: Record<string, string> = {};

    if (form.pincode && !/^[1-9][0-9]{5}$/.test(String(form.pincode).trim())) {
      errs.pincode = "Please enter a valid 6-digit Indian PIN code.";
    }

    if (form.annual_family_income !== undefined && form.annual_family_income !== null && form.annual_family_income < 0) {
      errs.annual_family_income = "Annual family income cannot be negative.";
    }

    if (form.date_of_birth) {
      const dob = new Date(form.date_of_birth);
      const today = new Date();
      if (dob > today) {
        errs.date_of_birth = "Date of birth cannot be in the future.";
      }
    }

    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSave = async () => {
    if (saving) return; // Prevent double submission

    setError(null);
    setSuccess(false);

    if (!validateForm()) {
      setError("Please correct the highlighted form errors before saving.");
      return;
    }

    setSaving(true);

    const payload = {
      ...form,
      father_name: sanitizeInput(form.father_name || ""),
      mother_name: sanitizeInput(form.mother_name || ""),
      tribe_name: sanitizeInput(form.tribe_name || ""),
      address_line1: sanitizeInput(form.address_line1 || ""),
      address_line2: sanitizeInput(form.address_line2 || ""),
      district: sanitizeInput(form.district || ""),
      city: sanitizeInput(form.city || ""),
      pincode: sanitizeInput(form.pincode || ""),
      education_records: educations.map((e) => ({
        ...e,
        institution_name: sanitizeInput(e.institution_name || ""),
        course_name: sanitizeInput(e.course_name || ""),
        year_of_passing: e.year_of_passing ? parseInt(e.year_of_passing) : null,
      })),
    };

    const res = await fetchApi("/api/v1/applicant/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });

    setSaving(false);

    if (res.error) {
      setError(res.error);
      if (res.validationErrors) {
        setFieldErrors(res.validationErrors);
      }
    } else {
      setProfile(res.data);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-900 border-t-transparent rounded-full animate-spin" />
          <div className="text-sm text-slate-500">Loading verified profile...</div>
        </div>
      </div>
    );
  }

  const todayStr = new Date().toISOString().split("T")[0];

  return (
    <div className="max-w-3xl space-y-6 anim-fade-in break-anywhere">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Applicant Profile</h1>
        <p className="text-sm text-slate-500 mt-1">
          Profile data is securely synchronized and utilized for scheme eligibility verification and pre-fill.
        </p>
      </div>

      {/* Status Badge */}
      <Alert className={profile?.is_profile_complete ? "border-emerald-200 bg-emerald-50/80" : "border-amber-200 bg-amber-50/80"}>
        {profile?.is_profile_complete
          ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          : <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />}
        <AlertTitle className={`text-sm font-bold ${profile?.is_profile_complete ? "text-emerald-800" : "text-amber-800"}`}>
          Profile Status: {profile?.is_profile_complete ? "Verified & Complete" : "Action Required - Profile Incomplete"}
        </AlertTitle>
        <AlertDescription className={`text-xs ${profile?.is_profile_complete ? "text-emerald-700" : "text-amber-700"} mt-1`}>
          {profile?.is_profile_complete
            ? "Your applicant profile is complete and verified. You are eligible to apply for applicable MoTA schemes."
            : "Please fill all mandatory fields (Date of Birth, Gender, Caste/Tribe, Domicile, Income, and Address) to activate scheme applications."}
        </AlertDescription>
      </Alert>

      {success && (
        <Alert className="border-emerald-300 bg-emerald-50 text-emerald-900 anim-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <AlertTitle className="text-emerald-800 text-sm font-bold">Profile Changes Saved</AlertTitle>
          <AlertDescription className="text-emerald-700 text-xs">
            Your profile details have been securely recorded in the MoTA scholarship database.
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive" className="anim-fade-in">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <AlertTitle className="text-sm font-bold">Save Failed</AlertTitle>
          <AlertDescription className="text-xs">{error}</AlertDescription>
        </Alert>
      )}

      {/* Personal Details */}
      <Card className="border-slate-200 shadow-xs">
        <CardContent className="pt-6">
          <SectionTitle icon={User} title="Personal & Community Details" subtitle="Basic personal and tribal identity information" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="dob" className="text-xs font-semibold">Date of Birth *</Label>
              <Input
                id="dob"
                type="date"
                max={todayStr}
                min="1940-01-01"
                value={form.date_of_birth || ""}
                onChange={(e) => updateField("date_of_birth", e.target.value)}
                error={fieldErrors.date_of_birth}
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="gender" className="text-xs font-semibold">Gender *</Label>
              <select
                id="gender"
                className="w-full min-h-[40px] text-sm border border-slate-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-800"
                value={form.gender || ""}
                onChange={(e) => updateField("gender", e.target.value)}
              >
                <option value="">Select gender</option>
                {GENDER_OPTIONS.map((g) => (
                  <option key={g} value={g}>
                    {g.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="father_name" className="text-xs font-semibold">Father's Name</Label>
              <Input
                id="father_name"
                maxLength={100}
                value={form.father_name || ""}
                onChange={(e) => updateField("father_name", e.target.value)}
                placeholder="Father's full name"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="mother_name" className="text-xs font-semibold">Mother's Name</Label>
              <Input
                id="mother_name"
                maxLength={100}
                value={form.mother_name || ""}
                onChange={(e) => updateField("mother_name", e.target.value)}
                placeholder="Mother's full name"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="caste" className="text-xs font-semibold">Caste Category *</Label>
              <Input
                id="caste"
                maxLength={80}
                value={form.caste || ""}
                onChange={(e) => updateField("caste", e.target.value)}
                placeholder="e.g., Scheduled Tribe (ST)"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tribe_name" className="text-xs font-semibold">Tribe Name / Community</Label>
              <Input
                id="tribe_name"
                maxLength={80}
                value={form.tribe_name || ""}
                onChange={(e) => updateField("tribe_name", e.target.value)}
                placeholder="e.g., Gond, Bhil, Santhal, Bodo, Mizo, etc."
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="state_of_domicile" className="text-xs font-semibold">State of Domicile *</Label>
              <select
                id="state_of_domicile"
                className="w-full min-h-[40px] text-sm border border-slate-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-800"
                value={form.state_of_domicile || ""}
                onChange={(e) => updateField("state_of_domicile", e.target.value)}
              >
                <option value="">Select state of domicile</option>
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="income" className="text-xs font-semibold">Annual Family Income (₹) *</Label>
              <Input
                id="income"
                type="number"
                min={0}
                max={100000000}
                value={form.annual_family_income ?? ""}
                onChange={(e) => updateField("annual_family_income", e.target.value ? parseInt(e.target.value) : null)}
                placeholder="e.g. 250000"
                error={fieldErrors.annual_family_income}
                helperText={form.annual_family_income ? `Formatted: ${formatIndianLakhsCrores(form.annual_family_income)}` : "Income as declared on revenue certificate"}
                className="text-sm"
              />
            </div>
            <div className="flex flex-wrap items-center gap-6 col-span-full pt-2">
              <label className="flex items-center gap-2.5 text-sm cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={form.is_pvtg || false}
                  onChange={(e) => updateField("is_pvtg", e.target.checked)}
                  className="rounded text-blue-900 w-4 h-4 border-slate-300 focus:ring-blue-800"
                />
                <span className="text-slate-800 font-medium">Particularly Vulnerable Tribal Group (PVTG)</span>
              </label>
              <label className="flex items-center gap-2.5 text-sm cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={form.is_divyangjan || false}
                  onChange={(e) => updateField("is_divyangjan", e.target.checked)}
                  className="rounded text-blue-900 w-4 h-4 border-slate-300 focus:ring-blue-800"
                />
                <span className="text-slate-800 font-medium">Divyangjan (Person with Disability)</span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Address */}
      <Card className="border-slate-200 shadow-xs">
        <CardContent className="pt-6">
          <SectionTitle icon={Home} title="Residential Address" subtitle="Official permanent & communication address" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="addr1" className="text-xs font-semibold">Address Line 1 *</Label>
              <Input
                id="addr1"
                maxLength={150}
                value={form.address_line1 || ""}
                onChange={(e) => updateField("address_line1", e.target.value)}
                placeholder="House / Flat No., Street, Landmark"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="addr2" className="text-xs font-semibold">Address Line 2</Label>
              <Input
                id="addr2"
                maxLength={150}
                value={form.address_line2 || ""}
                onChange={(e) => updateField("address_line2", e.target.value)}
                placeholder="Village / Area / Gram Panchayat / Post Office"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="district" className="text-xs font-semibold">District</Label>
              <Input
                id="district"
                maxLength={80}
                value={form.district || ""}
                onChange={(e) => updateField("district", e.target.value)}
                placeholder="District name"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="city" className="text-xs font-semibold">City / Town</Label>
              <Input
                id="city"
                maxLength={80}
                value={form.city || ""}
                onChange={(e) => updateField("city", e.target.value)}
                placeholder="City or Town"
                className="text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="addr_state" className="text-xs font-semibold">State *</Label>
              <select
                id="addr_state"
                className="w-full min-h-[40px] text-sm border border-slate-300 rounded-md px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-800"
                value={form.state || ""}
                onChange={(e) => updateField("state", e.target.value)}
              >
                <option value="">Select state</option>
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="pincode" className="text-xs font-semibold">PIN Code *</Label>
              <Input
                id="pincode"
                value={form.pincode || ""}
                onChange={(e) => updateField("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="6-digit PIN code"
                maxLength={6}
                error={fieldErrors.pincode}
                className="text-sm font-mono"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Education */}
      <Card className="border-slate-200 shadow-xs">
        <CardContent className="pt-6">
          <SectionTitle icon={GraduationCap} title="Academic Qualifications" subtitle="Educational credentials (chronological order)" />
          <div className="space-y-4">
            {educations.map((edu, idx) => (
              <div key={idx} className="p-4 bg-slate-50/80 rounded-xl border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700">Record #{idx + 1}</span>
                  <button
                    onClick={() => removeEducation(idx)}
                    className="text-red-500 hover:text-red-700 text-xs font-semibold flex items-center gap-1 p-1"
                    title="Remove qualification record"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Remove
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs font-semibold">Level *</Label>
                    <select
                      className="w-full min-h-[38px] text-xs border border-slate-300 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-800"
                      value={edu.education_level}
                      onChange={(e) => updateEducation(idx, "education_level", e.target.value)}
                    >
                      {EDUCATION_LEVELS.map((l) => (
                        <option key={l} value={l}>{l.replace(/_/g, " ").toUpperCase()}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-semibold">Institution Name</Label>
                    <Input
                      maxLength={150}
                      value={edu.institution_name || ""}
                      onChange={(e) => updateEducation(idx, "institution_name", e.target.value)}
                      placeholder="School / College / University"
                      className="text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-semibold">Course / Degree</Label>
                    <Input
                      maxLength={100}
                      value={edu.course_name || ""}
                      onChange={(e) => updateEducation(idx, "course_name", e.target.value)}
                      placeholder="e.g. B.Tech Computer Science, BA, Class XII"
                      className="text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-semibold">Year of Passing</Label>
                    <Input
                      type="number"
                      min={1950}
                      max={new Date().getFullYear() + 5}
                      value={edu.year_of_passing || ""}
                      onChange={(e) => updateEducation(idx, "year_of_passing", e.target.value)}
                      placeholder="e.g. 2024"
                      className="text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs font-semibold">Percentage / CGPA</Label>
                    <Input
                      maxLength={20}
                      value={edu.percentage_or_cgpa || ""}
                      onChange={(e) => updateEducation(idx, "percentage_or_cgpa", e.target.value)}
                      placeholder="e.g. 78.5% or 8.2 CGPA"
                      className="text-xs"
                    />
                  </div>
                  <div className="flex items-center gap-2 self-end pb-2">
                    <label className="flex items-center gap-2 text-xs text-slate-700 font-medium cursor-pointer">
                      <input
                        type="checkbox"
                        checked={edu.is_current || false}
                        onChange={(e) => updateEducation(idx, "is_current", e.target.checked)}
                        className="rounded text-blue-900 w-3.5 h-3.5"
                      />
                      <span>Currently enrolled in this course</span>
                    </label>
                  </div>
                </div>
              </div>
            ))}
            <button
              onClick={addEducation}
              className="w-full py-3 border-2 border-dashed border-slate-300 rounded-xl text-xs font-semibold text-slate-600 hover:border-blue-500 hover:text-blue-900 hover:bg-blue-50/20 transition-all flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" /> Add Academic Qualification
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Save Button with Double-Submission Protection */}
      <div className="flex justify-end gap-3 pt-2">
        <Button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-900 hover:bg-blue-800 text-white font-semibold px-8 flex items-center gap-2 shadow-sm min-h-[42px]"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Saving Profile Data...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save & Update Profile</span>
            </>
          )}
        </Button>
      </div>

      {/* Security Note */}
      <div className="text-[11px] text-slate-500 border-t border-slate-200/80 pt-4 flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
        <span>Bank account and Aadhaar credentials are protected with salted SHA-256 and AES-256-GCM encryption under Government of India data privacy guidelines.</span>
      </div>
    </div>
  );
}
