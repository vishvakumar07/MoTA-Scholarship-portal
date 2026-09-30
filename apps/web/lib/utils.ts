import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines Tailwind class names cleanly, resolving conflicts safely.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Hardened Currency Formatter
 * - Handles number, string numbers, null, undefined, NaN
 * - Default currency: Indian Rupee (INR) with Indian numbering format (Lakhs/Crores)
 * - Standardizes symbol spacing consistently across all JavaScript/Node/browser environments
 */
export function formatCurrency(
  amount: number | string | null | undefined,
  currency: string = "INR",
  locale: string = "en-IN"
): string {
  if (amount === null || amount === undefined || amount === "") {
    return "₹ 0";
  }

  const num = typeof amount === "number" ? amount : parseFloat(String(amount).replace(/,/g, ""));
  if (isNaN(num) || num === 0) {
    return "₹ 0";
  }

  try {
    const formatted = new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(num);
    return formatted.replace(/^₹\s*/, "₹ ");
  } catch {
    return `₹ ${num.toLocaleString("en-IN")}`;
  }
}

/**
 * Formats large amounts into official Indian Government denomination (Lakh / Crore)
 * e.g., 250000 -> "₹ 2.50 Lakh", 12500000 -> "₹ 1.25 Crore"
 */
export function formatIndianLakhsCrores(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || amount === "") return "₹ 0";
  const num = typeof amount === "number" ? amount : parseFloat(String(amount).replace(/,/g, ""));
  if (isNaN(num) || num === 0) return "₹ 0";

  if (Math.abs(num) >= 10000000) {
    return `₹ ${(num / 10000000).toFixed(2)} Crore`;
  }
  if (Math.abs(num) >= 100000) {
    return `₹ ${(num / 100000).toFixed(2)} Lakh`;
  }
  return formatCurrency(num);
}

/**
 * Hardened Number Formatter
 * - Formats with Indian grouping (1,25,000)
 * - Safe against NaN, null, undefined
 */
export function formatNumber(
  value: number | string | null | undefined,
  locale: string = "en-IN"
): string {
  if (value === null || value === undefined || value === "") return "0";
  const num = typeof value === "number" ? value : parseFloat(String(value).replace(/,/g, ""));
  if (isNaN(num)) return "0";

  try {
    return new Intl.NumberFormat(locale).format(num);
  } catch {
    return String(num);
  }
}

/**
 * Hardened Date Formatter
 * - Never returns "Invalid Date" or crashes UI
 * - Returns clean localized date (e.g. "28 Sep 2026")
 */
export function formatDate(
  dateInput: string | Date | number | null | undefined,
  options: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short", year: "numeric" },
  fallback: string = "--"
): string {
  if (!dateInput) return fallback;

  try {
    const d = typeof dateInput === "object" && dateInput instanceof Date ? dateInput : new Date(dateInput);
    if (isNaN(d.getTime())) return fallback;

    return new Intl.DateTimeFormat("en-IN", options).format(d);
  } catch {
    return fallback;
  }
}

/**
 * Formats date and time cleanly
 * e.g. "28 Sep 2026, 11:30 AM"
 */
export function formatDateTime(
  dateInput: string | Date | number | null | undefined,
  fallback: string = "--"
): string {
  return formatDate(
    dateInput,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    },
    fallback
  );
}

/**
 * Relative time formatter
 * e.g. "Just now", "5 minutes ago", "3 hours ago", "Yesterday"
 */
export function formatRelativeTime(dateInput: string | Date | number | null | undefined): string {
  if (!dateInput) return "--";

  try {
    const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
    if (isNaN(d.getTime())) return "--";

    const now = Date.now();
    const diffSeconds = Math.round((now - d.getTime()) / 1000);

    if (diffSeconds < 60) return "Just now";
    if (diffSeconds < 3600) {
      const mins = Math.floor(diffSeconds / 60);
      return `${mins} ${mins === 1 ? "minute" : "minutes"} ago`;
    }
    if (diffSeconds < 86400) {
      const hours = Math.floor(diffSeconds / 3600);
      return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
    }
    if (diffSeconds < 172800) return "Yesterday";

    const days = Math.floor(diffSeconds / 86400);
    if (days < 30) return `${days} days ago`;

    return formatDate(d);
  } catch {
    return "--";
  }
}

/**
 * Safe String Truncation
 * - Uses Array.from() to protect multibyte unicode characters and emojis from being sliced in half
 */
export function safeTruncate(
  text: string | null | undefined,
  maxLength: number,
  ellipsis: string = "..."
): string {
  if (!text) return "";
  const chars = Array.from(text);
  if (chars.length <= maxLength) return text;
  return chars.slice(0, maxLength).join("") + ellipsis;
}

/**
 * Pluralization helper
 */
export function safePlural(count: number, singular: string, plural: string): string {
  return `${formatNumber(count)} ${count === 1 ? singular : plural}`;
}

/**
 * Sanitize User Input
 * - Trims whitespace
 * - Strips ASCII control characters
 */
export function sanitizeInput(val: string): string {
  if (!val) return "";
  return val.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "").trim();
}
