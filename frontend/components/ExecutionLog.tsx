"use client";

import React, { useEffect, useRef } from "react";
import { useExecutionState, LogEntry } from "@/hooks/useExecutionState";
import { Download, FileText, Image } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function formatTime(timestamp: string): string {
  try {
    const d = new Date(timestamp);
    return d.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "";
  }
}

function ArtifactCard({ artifact }: { artifact: any }) {
  const handleDownload = () => {
    if (artifact.base64) {
      const byteChars = atob(artifact.base64);
      const byteNumbers = new Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) {
        byteNumbers[i] = byteChars.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: artifact.type });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = artifact.name;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const icon = artifact.type?.startsWith("image/") ? (
    <Image size={16} />
  ) : (
    <FileText size={16} />
  );

  return (
    <div className="artifact-card" onClick={handleDownload}>
      <span className="file-icon">{icon}</span>
      <span>📥 {artifact.name}</span>
      <Download size={14} />
    </div>
  );
}

export default function ExecutionLog() {
  const { logs, artifacts } = useExecutionState();
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  // Deduplicate artifacts by name
  const uniqueArtifacts = artifacts.reduce((acc: any[], art: any) => {
    if (!acc.find((a: any) => a.name === art.name)) {
      acc.push(art);
    }
    return acc;
  }, []);

  return (
    <div className="log-container" ref={containerRef}>
      {logs.length === 0 ? (
        <div
          style={{
            color: "var(--text-muted)",
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
          }}
        >
          <div style={{ opacity: 0.5 }}>
            {">"} Waiting for task execution...
          </div>
          <div style={{ opacity: 0.3, marginTop: "4px" }}>
            {">"} Enter a task and click Execute to begin.
          </div>
        </div>
      ) : (
        <>
          {logs.map((entry) => (
            <div
              key={entry.id}
              className={`log-entry type-${entry.event_type}`}
            >
              <span className="log-time">{formatTime(entry.timestamp)}</span>
              <span className="log-message">{entry.message}</span>
            </div>
          ))}

          {/* Artifact download cards */}
          {uniqueArtifacts.length > 0 && (
            <div style={{ marginTop: "12px", display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {uniqueArtifacts.map((artifact: any, i: number) => (
                <ArtifactCard key={`${artifact.name}-${i}`} artifact={artifact} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
