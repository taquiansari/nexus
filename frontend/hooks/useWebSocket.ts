"use client";

import { useRef, useCallback } from "react";
import { useExecutionState } from "./useExecutionState";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const {
    setConnected,
    setRunning,
    addLogEntry,
    setPlan,
    updateDagState,
    setHitlRequest,
    addArtifacts,
    setStatus,
    setCurrentStep,
  } = useExecutionState();

  const connect = useCallback(
    (executionId: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }

      const url = `${WS_BASE_URL}/ws/${executionId}`;
      console.log(`[WS] Connecting to ${url}`);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WS] Connected");
        setConnected(true);
        setRunning(true);
        setStatus("running");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleEvent(data);
        } catch (err) {
          console.error("[WS] Parse error:", err);
        }
      };

      ws.onclose = () => {
        console.log("[WS] Disconnected");
        setConnected(false);
        setRunning(false);
      };

      ws.onerror = () => {
        console.warn("[WS] Connection error (server may have closed)");
        setConnected(false);
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const handleEvent = useCallback(
    (event: any) => {
      const logEntry = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        event_type: event.event_type || "log",
        timestamp: event.timestamp || new Date().toISOString(),
        agent: event.agent || "",
        step_id: event.step_id ?? null,
        message: event.message || "",
        data: event.data,
        dag_state: event.dag_state,
      };

      // Add to log
      addLogEntry(logEntry);

      // Update DAG state
      if (event.dag_state) {
        updateDagState(event.dag_state);
      }

      // Handle specific event types
      switch (event.event_type) {
        case "plan_created":
          setPlan(event.data);
          break;

        case "step_start":
          if (event.step_id != null) {
            setCurrentStep(event.step_id);
          }
          setStatus("executing");
          break;

        case "step_complete":
        case "recovery_complete":
          if (event.data?.artifacts?.length) {
            addArtifacts(event.data.artifacts);
          }
          break;

        case "hitl_request":
          setStatus("hitl_paused");
          if (event.data) {
            setHitlRequest({
              question: event.data.question || event.message || "",
              options: event.data.options || [],
              context: event.data.context || "",
              step_output: event.data.step_output || "",
            });
          }
          break;

        case "hitl_response":
          setHitlRequest(null);
          setStatus("executing");
          break;

        case "execution_complete":
          setStatus("completed");
          setRunning(false);
          if (event.data?.artifacts?.length) {
            addArtifacts(event.data.artifacts);
          }
          break;

        case "execution_aborted":
          setStatus("aborted");
          setRunning(false);
          break;

        case "error":
          setStatus("error");
          setRunning(false);
          break;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const sendHitlResponse = useCallback((selectedOption: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "hitl_response",
          selected_option: selectedOption,
        })
      );
      setHitlRequest(null);
      setStatus("executing");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { connect, disconnect, sendHitlResponse };
}
