"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { History, Zap, ArrowLeft, RefreshCw } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Execution {
  id: string;
  task: string;
  status: string;
  created_at: string;
  duration_seconds: number | null;
  total_steps: number;
}

export default function HistoryPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExecutions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/executions`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setExecutions(data.executions || []);
    } catch (err: any) {
      setError(err.message || "Failed to load executions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-header-logo">
          <div className="logo-icon">
            <Zap size={18} />
          </div>
          <div>
            <h1>NEXUS</h1>
            <div className="subtitle">AI Task Execution Agent</div>
          </div>
        </div>
        <nav className="header-nav">
          <Link href="/">
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <ArrowLeft size={14} />
              Dashboard
            </span>
          </Link>
          <Link href="/history" className="active">
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <History size={14} />
              History
            </span>
          </Link>
        </nav>
      </header>

      <div className="history-container">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
          <h1 className="history-title" style={{ marginBottom: 0 }}>
            Execution History
          </h1>
          <button
            onClick={fetchExecutions}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 16px",
              background: "rgba(99, 102, 241, 0.1)",
              border: "1px solid var(--border-primary)",
              borderRadius: "8px",
              color: "var(--text-secondary)",
              cursor: "pointer",
              fontSize: "13px",
              fontFamily: "var(--font-body)",
            }}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {loading && (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
            <div className="loading-spinner" style={{ margin: "0 auto 12px" }} />
            Loading executions...
          </div>
        )}

        {error && (
          <div
            style={{
              padding: "20px",
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: "12px",
              color: "var(--accent-danger)",
              textAlign: "center",
              fontSize: "14px",
            }}
          >
            {error}
            <div style={{ marginTop: "8px", fontSize: "12px", color: "var(--text-muted)" }}>
              Make sure the backend is running.
            </div>
          </div>
        )}

        {!loading && !error && executions.length === 0 && (
          <div
            style={{
              textAlign: "center",
              padding: "60px 20px",
              color: "var(--text-muted)",
            }}
          >
            <History size={48} style={{ marginBottom: "16px", opacity: 0.3 }} />
            <div style={{ fontSize: "15px" }}>No executions yet</div>
            <div style={{ fontSize: "12px", marginTop: "8px" }}>
              <Link href="/" style={{ color: "var(--accent-primary)", textDecoration: "none" }}>
                Run your first task →
              </Link>
            </div>
          </div>
        )}

        {!loading && executions.length > 0 && (
          <table className="history-table">
            <thead>
              <tr>
                <th>Task</th>
                <th>Status</th>
                <th>Steps</th>
                <th>Duration</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((exec) => (
                <tr key={exec.id} style={{ cursor: "pointer" }}>
                  <td style={{ maxWidth: "400px" }}>
                    <div style={{ fontWeight: 500 }}>
                      {exec.task.length > 80
                        ? exec.task.slice(0, 80) + "..."
                        : exec.task}
                    </div>
                    <div
                      style={{
                        fontSize: "11px",
                        color: "var(--text-muted)",
                        fontFamily: "var(--font-mono)",
                        marginTop: "4px",
                      }}
                    >
                      {exec.id}
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${exec.status}`}>
                      {exec.status === "completed" && "✅"}
                      {exec.status === "aborted" && "🛑"}
                      {exec.status === "planning" && "🧠"}
                      {exec.status === "executing" && "⚡"}
                      {" "}
                      {exec.status}
                    </span>
                  </td>
                  <td>{exec.total_steps || "—"}</td>
                  <td>
                    {exec.duration_seconds
                      ? `${exec.duration_seconds.toFixed(1)}s`
                      : "—"}
                  </td>
                  <td style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    {formatDate(exec.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
