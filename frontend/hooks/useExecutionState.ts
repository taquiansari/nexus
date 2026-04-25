"use client";

import { create } from "zustand";

export interface LogEntry {
  id: string;
  event_type: string;
  timestamp: string;
  agent: string;
  step_id: number | null;
  message: string;
  data?: any;
  dag_state?: any;
}

export interface DagNode {
  id: string;
  label: string;
  worker: string;
  status: "pending" | "running" | "passed" | "failed";
  instruction: string;
}

export interface DagEdge {
  source: string;
  target: string;
}

export interface HITLRequest {
  question: string;
  options: string[];
  context: string;
  step_output?: string;
}

interface ExecutionState {
  // Connection
  executionId: string | null;
  isConnected: boolean;
  isRunning: boolean;

  // Plan
  plan: any | null;
  totalSteps: number;
  currentStep: number;

  // Logs
  logs: LogEntry[];

  // DAG
  dagNodes: Record<string, DagNode>;
  dagEdges: DagEdge[];

  // HITL
  hitlRequest: HITLRequest | null;

  // Artifacts
  artifacts: any[];

  // Status
  status: string;

  // Actions
  setExecutionId: (id: string) => void;
  setConnected: (connected: boolean) => void;
  setRunning: (running: boolean) => void;
  addLogEntry: (entry: LogEntry) => void;
  setPlan: (plan: any) => void;
  updateDagState: (dagState: any) => void;
  setHitlRequest: (request: HITLRequest | null) => void;
  addArtifacts: (artifacts: any[]) => void;
  setStatus: (status: string) => void;
  setCurrentStep: (step: number) => void;
  reset: () => void;
}

const initialState = {
  executionId: null,
  isConnected: false,
  isRunning: false,
  plan: null,
  totalSteps: 0,
  currentStep: 0,
  logs: [],
  dagNodes: {},
  dagEdges: [],
  hitlRequest: null,
  artifacts: [],
  status: "idle",
};

export const useExecutionState = create<ExecutionState>((set) => ({
  ...initialState,

  setExecutionId: (id) => set({ executionId: id }),
  setConnected: (connected) => set({ isConnected: connected }),
  setRunning: (running) => set({ isRunning: running }),

  addLogEntry: (entry) =>
    set((state) => ({
      logs: [...state.logs, entry],
    })),

  setPlan: (plan) =>
    set({
      plan,
      totalSteps: plan?.steps?.length || 0,
    }),

  updateDagState: (dagState) => {
    if (!dagState) return;
    set({
      dagNodes: dagState.nodes || {},
      dagEdges: dagState.edges || [],
    });
  },

  setHitlRequest: (request) => set({ hitlRequest: request }),

  addArtifacts: (newArtifacts) =>
    set((state) => ({
      artifacts: [...state.artifacts, ...newArtifacts],
    })),

  setStatus: (status) => set({ status }),

  setCurrentStep: (step) => set({ currentStep: step }),

  reset: () => set(initialState),
}));
