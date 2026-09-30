import React from "react";
import Link from "next/link";
import { LucideIcon, FileText } from "lucide-react";
import { Button } from "./button";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  secondaryActionHref?: string;
  onSecondaryAction?: () => void;
}

export function EmptyState({
  icon: Icon = FileText,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  secondaryActionLabel,
  secondaryActionHref,
  onSecondaryAction,
}: EmptyStateProps) {
  return (
    <div className="text-center py-12 px-4 bg-white border border-slate-200 rounded-xl shadow-xs anim-fade-in max-w-xl mx-auto my-4">
      <div className="w-12 h-12 rounded-2xl bg-blue-50/80 border border-blue-100 flex items-center justify-center mx-auto mb-3.5 text-blue-900 shadow-xs">
        <Icon className="w-6 h-6" />
      </div>

      <h3 className="text-base font-bold text-slate-900 tracking-tight">{title}</h3>
      <p className="text-xs text-slate-500 max-w-md mx-auto mt-1.5 leading-relaxed">
        {description}
      </p>

      {(actionLabel || secondaryActionLabel) && (
        <div className="flex flex-wrap items-center justify-center gap-3 mt-5">
          {actionLabel && (
            actionHref ? (
              <Link href={actionHref}>
                <Button size="sm" className="bg-blue-900 hover:bg-blue-800 text-white text-xs font-semibold shadow-xs">
                  {actionLabel}
                </Button>
              </Link>
            ) : (
              <Button size="sm" onClick={onAction} className="bg-blue-900 hover:bg-blue-800 text-white text-xs font-semibold shadow-xs">
                {actionLabel}
              </Button>
            )
          )}

          {secondaryActionLabel && (
            secondaryActionHref ? (
              <Link href={secondaryActionHref}>
                <Button variant="outline" size="sm" className="border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium">
                  {secondaryActionLabel}
                </Button>
              </Link>
            ) : (
              <Button variant="outline" size="sm" onClick={onSecondaryAction} className="border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-medium">
                {secondaryActionLabel}
              </Button>
            )
          )}
        </div>
      )}
    </div>
  );
}
