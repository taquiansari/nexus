"use client";

import React from "react";
import { useExecutionState } from "@/hooks/useExecutionState";

export default function ProgressBar() {
  const { totalSteps, currentStep, status, isRunning } = useExecutionState();

  if (totalSteps === 0 && !isRunning) return null;

  const progress =
    status === "completed"
      ? 100
      : totalSteps > 0
      ? Math.min((currentStep / totalSteps) * 100, 100)
      : 0;

  const statusLabel: Record<string, string> = {
    running: "Executing",
    executing: "Executing",
    planning: "Planning",
    evaluating: "Evaluating",
    recovery: "Recovering",
    hitl_paused: "Waiting for Input",
    completed: "Complete",
    aborted: "Aborted",
    idle: "",
  };

  return (
    <div className="progress-bar-container">
      <div className="progress-bar">
        <div
          className="progress-bar-fill"
          style={{
            width: `${progress}%`,
            background:
              status === "completed"
                ? "linear-gradient(90deg, #10b981, #06b6d4)"
                : status === "aborted"
                ? "linear-gradient(90deg, #ef4444, #f59e0b)"
                : undefined,
          }}
        />
      </div>
      <div className="progress-info">
        <span>
          {status === "completed"
            ? `✅ All ${totalSteps} steps complete`
            : status === "aborted"
            ? "🛑 Execution aborted"
            : currentStep > 0
            ? `Step ${currentStep} / ${totalSteps}`
            : totalSteps > 0
            ? `${totalSteps} steps planned`
            : "Initializing..."}
        </span>
        <span>{statusLabel[status] || status}</span>
      </div>
    </div>
  );
}
