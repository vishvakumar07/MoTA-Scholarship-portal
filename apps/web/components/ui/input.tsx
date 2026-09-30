import * as React from "react";
import { cn } from "@/lib/utils";
import { AlertCircle } from "lucide-react";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean | string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, helperText, leftIcon, rightIcon, id, ...props }, ref) => {
    const hasError = !!error;
    const errorMessage = typeof error === "string" ? error : undefined;
    const errorId = id ? `${id}-error` : undefined;
    const helperId = id ? `${id}-helper` : undefined;

    return (
      <div className="w-full space-y-1">
        <div className="relative flex items-center w-full">
          {leftIcon && (
            <div className="absolute left-3 flex items-center pointer-events-none text-slate-400">
              {leftIcon}
            </div>
          )}

          <input
            id={id}
            type={type}
            ref={ref}
            aria-invalid={hasError ? "true" : undefined}
            aria-describedby={
              hasError && errorId ? errorId : helperText && helperId ? helperId : undefined
            }
            className={cn(
              "input-enhanced",
              "flex min-h-[40px] w-full rounded-md border bg-white px-3 py-2 text-sm shadow-xs",
              "transition-colors duration-150",
              "placeholder:text-slate-400 text-slate-900",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1",
              "disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500 disabled:opacity-75",
              leftIcon && "pl-9",
              rightIcon && "pr-9",
              hasError
                ? "border-red-500 focus-visible:ring-red-400 text-red-950 bg-red-50/10"
                : "border-slate-300 focus-visible:ring-blue-800",
              className
            )}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 flex items-center pointer-events-none text-slate-400">
              {rightIcon}
            </div>
          )}
        </div>

        {hasError && errorMessage && (
          <p id={errorId} role="alert" className="text-xs text-red-600 font-medium flex items-center gap-1 mt-1">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{errorMessage}</span>
          </p>
        )}

        {!hasError && helperText && (
          <p id={helperId} className="text-[11px] text-slate-500 mt-1">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
