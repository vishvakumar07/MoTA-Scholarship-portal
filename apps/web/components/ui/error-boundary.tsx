"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home, ShieldAlert } from "lucide-react";
import { Button } from "./button";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  resetOnPropChange?: any;
}

interface State {
  hasError: boolean;
  error: Error | null;
  eventId: string;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    eventId: "",
  };

  public static getDerivedStateFromError(error: Error): State {
    const eventId = `ERR-${Date.now().toString(36).toUpperCase()}`;
    return { hasError: true, error, eventId };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (process.env.NODE_ENV !== "production") {
      console.error("ErrorBoundary caught an unhandled error:", error, errorInfo);
    }
  }

  public componentDidUpdate(prevProps: Props) {
    if (
      this.props.resetOnPropChange !== undefined &&
      prevProps.resetOnPropChange !== this.props.resetOnPropChange
    ) {
      this.handleReset();
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, eventId: "" });
  };

  public render() {
    if (this.state.hasError) {
      const {
        fallbackTitle = "Display Anomaly Detected",
        fallbackMessage = "An unexpected error occurred while rendering this scholarship component. Your application data remains securely saved in the MoTA database.",
      } = this.props;

      return (
        <div className="p-6 my-4 bg-white border border-red-200 rounded-xl shadow-xs text-slate-800 anim-fade-in">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center shrink-0 text-red-700">
              <ShieldAlert className="w-5 h-5" />
            </div>

            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-bold text-slate-900 text-base">{fallbackTitle}</h3>
                {this.state.eventId && (
                  <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    Ref: {this.state.eventId}
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                {fallbackMessage}
              </p>

              <div className="flex flex-wrap items-center gap-3 pt-3">
                <Button
                  size="sm"
                  onClick={this.handleReset}
                  className="bg-blue-900 hover:bg-blue-800 text-white text-xs gap-1.5 shadow-xs"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Retry Section
                </Button>
                <Link href="/dashboard">
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-slate-300 text-slate-700 hover:bg-slate-50 text-xs gap-1.5"
                  >
                    <Home className="w-3.5 h-3.5 text-slate-500" />
                    Scholar Dashboard
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
