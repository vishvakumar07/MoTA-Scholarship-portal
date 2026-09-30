"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { EmptyState } from "@/components/ui/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Bell, CheckCircle2, Clock, AlertTriangle, ShieldCheck,
  Check, ArrowRight, ExternalLink, Filter, Mail
} from "lucide-react";

interface NotificationItem {
  id: string;
  channel: string;
  status: string;
  title: string;
  body: string;
  action_url: string | null;
  related_entity_type: string | null;
  sent_at: string | null;
  read_at: string | null;
  created_at: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [channelStatus, setChannelStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    const [notifRes, statusRes] = await Promise.all([
      fetchApi("/api/v1/notifications"),
      fetchApi("/api/v1/notifications/status"),
    ]);

    if (notifRes.data) {
      setNotifications(notifRes.data.notifications || []);
      setUnreadCount(notifRes.data.unread_count || 0);
    } else {
      setError(notifRes.error || "Failed to load notifications.");
    }

    if (statusRes.data) {
      setChannelStatus(statusRes.data);
    }

    setLoading(false);
  };

  const handleMarkAsRead = async (id: string) => {
    const res = await fetchApi(`/api/v1/notifications/${id}/read`, { method: "POST" });
    if (res.data) {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read_at: new Date().toISOString() } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    }
  };

  const handleMarkAllAsRead = async () => {
    const res = await fetchApi("/api/v1/notifications/read-all", { method: "POST" });
    if (res.data) {
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read_at: n.read_at || new Date().toISOString() }))
      );
      setUnreadCount(0);
    }
  };

  const filtered = notifications.filter((n) => {
    if (filter === "unread") return !n.read_at;
    return true;
  });

  return (
    <div className="space-y-6 break-anywhere">
      {/* Header with animation */}
      <div className="anim-fade-in flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-blue-900 tracking-wider uppercase mb-1">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            Official Applicant Communications
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            Notifications & Alerts
            {unreadCount > 0 && (
              <span className="bg-amber-100 text-amber-900 text-xs px-2.5 py-0.5 rounded-full font-bold border border-amber-200 notif-dot">
                {unreadCount} unread
              </span>
            )}
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Timely scrutiny alerts, deficiency advisories, and status updates regarding your scholarship applications.
          </p>
        </div>

        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkAllAsRead}
            className="text-xs font-semibold border-slate-300 hover:bg-slate-50 text-slate-700 self-start sm:self-auto gap-1.5 shadow-xs"
          >
            <Check className="w-3.5 h-3.5" />
            Mark all as read
          </Button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="anim-fade-in delay-1 flex items-center gap-2 text-xs font-medium border-b border-slate-200 pb-2">
        <button
          onClick={() => setFilter("all")}
          className={`px-3 py-1.5 rounded-md transition-all duration-150 ${
            filter === "all" ? "bg-blue-900 text-white shadow-sm font-semibold" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          All ({notifications.length})
        </button>
        <button
          onClick={() => setFilter("unread")}
          className={`px-3 py-1.5 rounded-md transition-all duration-150 flex items-center gap-1.5 ${
            filter === "unread" ? "bg-blue-900 text-white shadow-sm font-semibold" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          Unread Only
          {unreadCount > 0 && (
            <span className="bg-amber-400 text-amber-950 font-bold rounded-full px-1.5 py-0.2 text-[10px]">
              {unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Notifications List */}
      {loading ? (
        <div className="space-y-3 anim-fade-in">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-5 border border-slate-200 rounded-lg bg-white space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-200 animate-pulse" />
                <div className="h-4 bg-slate-200 rounded w-1/3 animate-pulse" />
              </div>
              <div className="h-3 bg-slate-100 rounded w-2/3 animate-pulse" />
            </div>
          ))}
        </div>
      ) : error ? (
        <Alert className="border-red-200 bg-red-50 text-red-800 anim-fade-in">
          <AlertTriangle className="w-4 h-4 text-red-600" />
          <AlertTitle className="text-xs font-semibold">Error Loading Notifications</AlertTitle>
          <AlertDescription className="text-xs mt-1">{error}</AlertDescription>
        </Alert>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-lg p-6 anim-fade-in">
          <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3 text-slate-400">
            <Bell className="w-6 h-6" />
          </div>
          <h2 className="text-base font-semibold text-slate-800">No notifications</h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            {filter === "unread"
              ? "You have caught up with all official notifications."
              : "You have no notifications in your inbox yet. New messages will appear here when your application status progresses."}
          </p>
        </div>
      ) : (
        <div className="space-y-3 anim-fade-in delay-2">
          {filtered.map((item) => {
            const isUnread = !item.read_at;
            const isDeficiency = item.title.toLowerCase().includes("deficiency") || item.body.toLowerCase().includes("deficiency");

            return (
              <Card
                key={item.id}
                className={`border card-interactive transition-all ${
                  isUnread
                    ? isDeficiency
                      ? "border-red-300 bg-red-50/30 shadow-xs"
                      : "border-blue-200 bg-blue-50/20 shadow-xs"
                    : "border-slate-200 bg-white"
                }`}
              >
                <CardContent className="p-4 sm:p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3.5 min-w-0">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 shadow-xs ${
                          isDeficiency
                            ? "bg-red-100 text-red-700"
                            : isUnread
                            ? "bg-blue-100 text-blue-900"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {isDeficiency ? (
                          <AlertTriangle className="w-4 h-4" />
                        ) : (
                          <Bell className="w-4 h-4" />
                        )}
                      </div>

                      <div className="space-y-1.5 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-sm font-bold text-slate-900 leading-snug">
                            {item.title}
                          </h2>
                          {isUnread && (
                            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
                          )}
                          {isDeficiency && (
                            <Badge variant="urgent" className="text-[10px]">Action Required</Badge>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">{item.body}</p>
                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 font-mono pt-1">
                          <span>
                            {formatDateTime(item.created_at)}
                          </span>
                          <span>&bull;</span>
                          <span className="capitalize">{item.channel} Notification</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
                      {isUnread && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleMarkAsRead(item.id)}
                          className="text-xs text-slate-500 hover:text-blue-900 hover:bg-blue-50"
                        >
                          Mark read
                        </Button>
                      )}
                      {item.action_url && (
                        <Link href={item.action_url}>
                          <Button size="sm" className="bg-blue-900 hover:bg-blue-800 text-white text-xs gap-1 shadow-xs">
                            View <ArrowRight className="w-3 h-3" />
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
