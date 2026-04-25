"use client";

import React, { useCallback } from "react";
import { useExecutionState } from "@/hooks/useExecutionState";
import { useWebSocket } from "@/hooks/useWebSocket";
import TaskInput from "@/components/TaskInput";
import ExecutionLog from "@/components/ExecutionLog";
import DagVisualizer from "@/components/DagVisualizer";
import HitlModal from "@/components/HitlModal";
import ProgressBar from "@/components/ProgressBar";
import {
  Terminal,
  GitBranch,
  Cpu,
  History,
  Zap,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { isRunning, hitlRequest, status, reset } = useExecutionState();
  const { connect, sendHitlResponse, disconnect } = useWebSocket();
  const { setExecutionId } = useExecutionState();

  const handleExecutionStart = useCallback(
    (executionId: string) => {
      reset();
      setExecutionId(executionId);
      connect(executionId);
    },
    [reset, setExecutionId, connect]
  );

  const handleNewTask = useCallback(() => {
    disconnect();
    reset();
  }, [disconnect, reset]);

  return (
    <div className="app-container">
      {/* Header */}
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
          <Link href="/" className="active">
            Dashboard
          </Link>
          <Link href="/history">
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <History size={14} />
              History
            </span>
          </Link>
          {(status === "completed" || status === "aborted") && (
            <button
              onClick={handleNewTask}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                border: "1px solid var(--border-primary)",
                background: "rgba(99, 102, 241, 0.1)",
                color: "var(--text-bright)",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: 500,
                fontFamily: "var(--font-body)",
              }}
            >
              + New Task
            </button>
          )}
        </nav>
      </header>

      {/* Progress Bar */}
      <ProgressBar />

      {/* Main Dashboard Grid */}
      <main className="dashboard">
        {/* Left Panel: Task Input */}
        <div className="panel-input glass-card panel">
          <div className="panel-header">
            <h2>
              <Cpu size={14} className="icon" />
              Task Input
            </h2>
            {isRunning && (
              <span
                style={{
                  fontSize: "10px",
                  color: "var(--accent-success)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <span
                  style={{
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    background: "var(--accent-success)",
                    display: "inline-block",
                    animation: "pulse-node 1.5s ease-in-out infinite",
                  }}
                />
                LIVE
              </span>
            )}
          </div>
          <TaskInput
            onExecutionStart={handleExecutionStart}
            isRunning={isRunning}
          />
        </div>

        {/* Right Top Panel: DAG Visualizer */}
        <div className="panel-dag glass-card panel">
          <div className="panel-header">
            <h2>
              <GitBranch size={14} className="icon" />
              Execution Graph
            </h2>
          </div>
          <DagVisualizer />
        </div>

        {/* Bottom Panel: Execution Log */}
        <div className="panel-log glass-card panel">
          <div className="panel-header">
            <h2>
              <Terminal size={14} className="icon" />
              Execution Log
            </h2>
          </div>
          <ExecutionLog />
        </div>
      </main>

      {/* HITL Modal */}
      {hitlRequest && (
        <HitlModal onResponse={sendHitlResponse} />
      )}
    </div>
  );
}
