'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface WorkQueueItem {
  application_id: string;
  application_number: string;
  scheme_name: string;
  applicant_name: string;
  status: string;
  priority: 'NORMAL' | 'HIGH' | 'URGENT';
  assigned_to?: string;
  assigned_at?: string;
  pending_document_reviews: number;
  open_deficiencies: number;
  last_activity_at: string;
  created_at: string;
}

interface WorkQueueSummary {
  total_in_queue: number;
  high_priority: number;
  urgent_priority: number;
  pending_doc_reviews: number;
  open_deficiencies: number;
}

export default function WorkQueuePage() {
  const [items, setItems] = useState<WorkQueueItem[]>([]);
  const [summary, setSummary] = useState<WorkQueueSummary>({
    total_in_queue: 0,
    high_priority: 0,
    urgent_priority: 0,
    pending_doc_reviews: 0,
    open_deficiencies: 0,
  });
  const [loading, setLoading] = useState(true);
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [assigneeId, setAssigneeId] = useState<string>('');
  const [assignPriority, setAssignPriority] = useState<string>('NORMAL');
  const [assignNotes, setAssignNotes] = useState<string>('');
  const [assigning, setAssigning] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const fetchWorkQueue = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterPriority !== 'ALL') params.append('priority', filterPriority);
      if (filterStatus !== 'ALL') params.append('status', filterStatus);

      const res = await fetch(`/api/v1/admin/work-queue?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
        if (data.summary) {
          setSummary(data.summary);
        }
      }
    } catch (err) {
      console.error('Failed to fetch work queue:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkQueue();
  }, [filterPriority, filterStatus]);

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppId || !assigneeId) return;

    setAssigning(true);
    setActionMessage(null);

    try {
      const res = await fetch(`/api/v1/admin/applications/${selectedAppId}/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          assigned_to: assigneeId,
          priority: assignPriority,
          notes: assignNotes || undefined
        })
      });

      if (res.ok) {
        setActionMessage('Case successfully assigned/reassigned.');
        setSelectedAppId(null);
        setAssigneeId('');
        setAssignNotes('');
        fetchWorkQueue();
      } else {
        const errData = await res.json();
        setActionMessage(`Error: ${errData.detail || 'Assignment failed'}`);
      }
    } catch (err) {
      setActionMessage('Network error occurred during assignment.');
    } finally {
      setAssigning(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return <span className="px-2 py-0.5 text-xs font-bold rounded bg-red-100 text-red-800 border border-red-300 badge-urgent">URGENT</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-100 text-amber-800 border border-amber-300">HIGH</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium rounded bg-slate-100 text-slate-700 border border-slate-200">NORMAL</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 anim-fade-in">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Officer Work Queue</h1>
          <p className="text-sm text-slate-500 mt-1">
            Ministry of Tribal Affairs Scholarship Case Management & Scrutiny Queue
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => fetchWorkQueue()}
            className="px-3 py-1.5 text-sm bg-white border border-slate-300 text-slate-700 rounded shadow-sm hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Refresh Queue
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs card-interactive transition-all">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total in Queue</span>
          <p className="text-2xl font-bold text-slate-800 mt-1">{summary.total_in_queue}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-amber-200 bg-amber-50/30 shadow-xs card-interactive transition-all">
          <span className="text-xs font-medium text-amber-700 uppercase tracking-wider">High Priority</span>
          <p className="text-2xl font-bold text-amber-900 mt-1">{summary.high_priority}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-red-200 bg-red-50/30 shadow-xs card-interactive transition-all">
          <span className="text-xs font-medium text-red-700 uppercase tracking-wider">Urgent Priority</span>
          <p className="text-2xl font-bold text-red-900 mt-1">{summary.urgent_priority}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-blue-200 bg-blue-50/30 shadow-xs card-interactive transition-all">
          <span className="text-xs font-medium text-blue-700 uppercase tracking-wider">Pending Doc Reviews</span>
          <p className="text-2xl font-bold text-blue-900 mt-1">{summary.pending_doc_reviews}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-purple-200 bg-purple-50/30 shadow-xs card-interactive transition-all">
          <span className="text-xs font-medium text-purple-700 uppercase tracking-wider">Open Deficiencies</span>
          <p className="text-2xl font-bold text-purple-900 mt-1">{summary.open_deficiencies}</p>
        </div>
      </div>

      {actionMessage && (
        <div className={`p-4 rounded-md text-sm ${actionMessage.startsWith('Error') ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}`}>
          {actionMessage}
        </div>
      )}

      {/* Filters and Controls */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Filter Priority</label>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="text-sm border border-slate-300 rounded px-2.5 py-1.5 focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="ALL">All Priorities</option>
              <option value="NORMAL">Normal</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Filter Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="text-sm border border-slate-300 rounded px-2.5 py-1.5 focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="ALL">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="DEFICIENCY_RAISED">Deficiency Raised</option>
              <option value="RESUBMITTED">Resubmitted</option>
            </select>
          </div>
        </div>
        <div className="text-xs text-slate-500">
          Operational Case Queue &bull; Actual Records Only &bull; Zero Fabricated Workload
        </div>
      </div>

      {/* Queue Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Loading operational work queue...</div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-slate-600 font-medium">No cases currently assigned.</p>
            <p className="text-xs text-slate-400 mt-1">When applications are submitted or assigned, they will appear here truthfully.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs font-semibold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">App Number / Scheme</th>
                  <th className="px-4 py-3">Applicant</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-center">Pending Docs</th>
                  <th className="px-4 py-3 text-center">Deficiencies</th>
                  <th className="px-4 py-3">Last Activity</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.application_id} className="hover:bg-slate-50/75 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-900">{item.application_number}</div>
                      <div className="text-xs text-slate-500 truncate max-w-xs">{item.scheme_name}</div>
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {item.applicant_name}
                    </td>
                    <td className="px-4 py-3">
                      {getPriorityBadge(item.priority)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-700">
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {item.pending_document_reviews > 0 ? (
                        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-50 text-amber-700 border border-amber-200">
                          {item.pending_document_reviews} pending
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {item.open_deficiencies > 0 ? (
                        <span className="px-2 py-0.5 text-xs font-semibold rounded bg-purple-50 text-purple-700 border border-purple-200">
                          {item.open_deficiencies} open
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(item.last_activity_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <Link
                        href={`/admin/applications/${item.application_id}/review`}
                        className="inline-block px-2.5 py-1 text-xs font-medium rounded bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200"
                      >
                        Scrutiny
                      </Link>
                      <button
                        onClick={() => setSelectedAppId(item.application_id)}
                        className="px-2.5 py-1 text-xs font-medium rounded bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-300"
                      >
                        Assign
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Assignment Modal */}
      {selectedAppId && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-3">Assign Case to Scrutiny Officer</h3>
            <form onSubmit={handleAssign} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assignee Officer User ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. officer-uuid"
                  value={assigneeId}
                  onChange={(e) => setAssigneeId(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Operational Priority</label>
                <select
                  value={assignPriority}
                  onChange={(e) => setAssignPriority(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="NORMAL">NORMAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="URGENT">URGENT</option>
                </select>
                <p className="text-xs text-slate-400 mt-1">
                  Note: Priority does NOT alter legal eligibility or create automatic preference.
                </p>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Assignment Note (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Instructions for scrutiny officer..."
                  value={assignNotes}
                  onChange={(e) => setAssignNotes(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedAppId(null)}
                  className="px-3 py-1.5 text-sm rounded border border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={assigning}
                  className="px-4 py-1.5 text-sm rounded bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {assigning ? 'Assigning...' : 'Confirm Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
