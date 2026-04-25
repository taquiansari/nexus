"use client";

import React from "react";
import { useExecutionState } from "@/hooks/useExecutionState";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";

interface HitlModalProps {
  onResponse: (option: string) => void;
}

export default function HitlModal({ onResponse }: HitlModalProps) {
  const { hitlRequest } = useExecutionState();

  if (!hitlRequest) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="hitl-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="hitl-modal"
          initial={{ y: 60, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 60, opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
        >
          <div className="hitl-modal-header">
            <AlertTriangle size={20} className="warning-icon" />
            <h3>Human Decision Required</h3>
          </div>

          <div className="hitl-modal-body">
            <p className="hitl-question">{hitlRequest.question}</p>

            {hitlRequest.context && (
              <div className="hitl-context">{hitlRequest.context}</div>
            )}

            {hitlRequest.step_output && (
              <div className="hitl-context" style={{ marginBottom: "16px" }}>
                <div style={{ color: "var(--accent-secondary)", marginBottom: "4px", fontSize: "10px", textTransform: "uppercase", letterSpacing: "1px" }}>
                  Step Output Preview
                </div>
                {hitlRequest.step_output}
              </div>
            )}

            <div className="hitl-options">
              {hitlRequest.options.map((option, index) => (
                <button
                  key={index}
                  className={`hitl-option-btn ${
                    option.toLowerCase().includes("abort") ? "danger" : ""
                  }`}
                  onClick={() => onResponse(option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
