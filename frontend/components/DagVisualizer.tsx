"use client";

import React, { useCallback, useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Position,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useExecutionState } from "@/hooks/useExecutionState";
import { GitBranch } from "lucide-react";

// Custom node component
function NexusNode({ data }: { data: any }) {
  const statusEmoji: Record<string, string> = {
    pending: "⏳",
    running: "⚡",
    passed: "✅",
    failed: "❌",
  };

  return (
    <div className={`nexus-node status-${data.status}`}>
      <Handle type="target" position={Position.Left} id="tgt" style={{ background: 'rgba(99,102,241,0.5)', border: 'none', width: 8, height: 8 }} />
      <div
        style={{
          fontSize: "12px",
          marginBottom: "3px",
        }}
      >
        {statusEmoji[data.status] || "⏳"}
      </div>
      <div className="node-label">{data.label}</div>
      <div className="node-worker">{data.worker}</div>
      <Handle type="source" position={Position.Right} id="src" style={{ background: 'rgba(99,102,241,0.5)', border: 'none', width: 8, height: 8 }} />
    </div>
  );
}

const nodeTypes = { nexusNode: NexusNode };

export default function DagVisualizer() {
  const { dagNodes, dagEdges, plan } = useExecutionState();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Convert dag state to React Flow format
  useEffect(() => {
    const nodeEntries = Object.values(dagNodes);
    if (nodeEntries.length === 0) return;

    // Horizontal flow layout — left to right
    const SPACING_X = 180;
    const CENTER_Y = 60;

    const flowNodes: Node[] = nodeEntries.map((node: any, index: number) => {
      return {
        id: String(node.id),
        type: "nexusNode",
        position: {
          x: 40 + index * SPACING_X,
          y: CENTER_Y,
        },
        data: {
          label: node.label || `Step ${node.id}`,
          worker: node.worker || "",
          status: node.status || "pending",
          instruction: node.instruction || "",
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };
    });

    const flowEdges: Edge[] = dagEdges.map((edge: any) => ({
      id: `e-${edge.source}-${edge.target}`,
      source: String(edge.source),
      target: String(edge.target),
      sourceHandle: "src",
      targetHandle: "tgt",
      type: "smoothstep",
      animated: true,
      style: { stroke: "rgba(99, 102, 241, 0.5)", strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "rgba(99, 102, 241, 0.5)",
      },
    }));

    // Set nodes first, then edges on next frame so handles are registered
    setNodes(flowNodes);
    requestAnimationFrame(() => {
      setEdges(flowEdges);
    });
  }, [dagNodes, dagEdges, setNodes, setEdges]);

  if (!plan) {
    return (
      <div className="dag-empty">
        <div className="empty-icon">
          <GitBranch size={40} />
        </div>
        <span>Execution graph will appear here</span>
        <span style={{ fontSize: "11px", opacity: 0.5 }}>
          Each step lights up as the agent executes
        </span>
      </div>
    );
  }

  return (
    <div className="dag-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={true}
        nodesConnectable={false}
        elementsSelectable={false}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="rgba(99, 102, 241, 0.05)" gap={20} />
        <Controls
          showInteractive={false}
          style={{
            background: "rgba(10, 14, 39, 0.9)",
            borderRadius: "8px",
            border: "1px solid rgba(99, 102, 241, 0.2)",
          }}
        />
      </ReactFlow>
    </div>
  );
}
