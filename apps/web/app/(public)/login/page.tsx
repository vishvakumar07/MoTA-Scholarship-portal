"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ShieldCheck, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetchApi("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (res.error) {
        setError(res.error);
      } else if (res.data) {
        saveAuth(res.data.access_token, res.data.user);
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto px-4 sm:px-0">
      <Card className="shadow-lg border-slate-200">
        <CardHeader className="space-y-2 text-center pb-6 border-b border-slate-100">
          <div className="w-12 h-12 bg-blue-900 rounded-full mx-auto flex items-center justify-center text-white shadow">
            <ShieldCheck className="w-6 h-6 text-amber-400" />
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900">
            Sign In to Portal
          </CardTitle>
          <CardDescription className="text-xs">
            Ministry of Tribal Affairs Scholarship & Fellowship System
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4 pt-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="w-4 h-4" />
                <AlertTitle>Authentication Failed</AlertTitle>
                <AlertDescription className="text-xs">{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email">Registered Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="applicant@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <Label htmlFor="password">Password</Label>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded border">
              Security notice: Your account will be temporarily locked for 15 minutes after 5 consecutive failed login attempts.
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-3 pt-2">
            <Button
              type="submit"
              variant="motaPrimary"
              className="w-full font-semibold"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>

            <div className="text-center text-xs text-slate-600">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="text-blue-700 font-semibold hover:underline">
                Register as Applicant
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

