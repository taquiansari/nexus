"use client";

import React, { useState, useRef } from "react";
import { Upload, Play, Loader2, FileText } from "lucide-react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface TaskInputProps {
  onExecutionStart: (executionId: string) => void;
  isRunning: boolean;
}

export default function TaskInput({
  onExecutionStart,
  isRunning,
}: TaskInputProps) {
  const [task, setTask] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!task.trim() || isSubmitting || isRunning) return;

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("task", task);
      if (file) {
        formData.append("file", file);
      }

      const response = await fetch(`${API_BASE_URL}/api/execute`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      onExecutionStart(data.execution_id);
    } catch (error) {
      console.error("Failed to start execution:", error);
      alert("Failed to connect to the backend. Make sure the server is running.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) setFile(selectedFile);
  };

  return (
    <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <textarea
        id="task-input"
        className="task-textarea"
        placeholder={`Describe your task in detail...\n\nExample: "I have a CSV file of raw sales transactions for 2025. The data is messy — there are missing values, inconsistent date formats, and duplicate entries. Clean the data, calculate monthly revenue trends, identify the best product category, generate a bar chart, and create a PDF report."`}
        value={task}
        onChange={(e) => setTask(e.target.value)}
        disabled={isRunning}
      />

      <div
        className={`file-upload-zone ${file ? "has-file" : ""}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json,.txt,.xlsx"
          onChange={handleFileSelect}
          style={{ display: "none" }}
          id="file-upload"
        />
        {file ? (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", justifyContent: "center" }}>
            <FileText size={18} />
            <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
          </div>
        ) : (
          <>
            <div className="upload-icon">
              <Upload size={24} />
            </div>
            <div>Drop a file here or click to upload</div>
            <div style={{ fontSize: "11px", marginTop: "4px", opacity: 0.6 }}>
              CSV, JSON, TXT supported
            </div>
          </>
        )}
      </div>

      <button
        id="execute-btn"
        className={`btn-execute ${isRunning ? "running" : ""}`}
        onClick={handleSubmit}
        disabled={!task.trim() || isSubmitting || isRunning}
      >
        {isSubmitting ? (
          <>
            <Loader2 size={18} className="loading-spinner" />
            Starting...
          </>
        ) : isRunning ? (
          <>
            <div className="loading-spinner" />
            Executing...
          </>
        ) : (
          <>
            <Play size={18} />
            Execute Task
          </>
        )}
      </button>

      {file && !isRunning && (
        <button
          onClick={() => setFile(null)}
          style={{
            background: "none",
            border: "none",
            color: "var(--text-muted)",
            fontSize: "12px",
            cursor: "pointer",
            textAlign: "center",
          }}
        >
          Remove file
        </button>
      )}
    </div>
  );
}
