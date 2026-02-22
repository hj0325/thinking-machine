"use client";

import { useMemo } from "react";
import ReactFlow, {
    Background,
    Controls,
    ConnectionMode,
    MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

export default function NodeMap({ nodes, edges, onNodesChange, onEdgesChange }) {

    const defaultEdgeOptions = useMemo(() => ({
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#b1b1b7', strokeWidth: 2 },
        markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#b1b1b7',
        },
    }), []);

    return (
        <div className="w-full h-full bg-slate-50">
            {/* Background Visuals for Double Diamond */}
            <div className="absolute inset-0 pointer-events-none z-0 flex">
                <div className="w-1/2 h-full bg-gradient-to-br from-blue-50/50 to-indigo-50/50 border-r border-indigo-100/50 p-8">
                    <h2 className="text-4xl font-bold text-indigo-900/10 tracking-widest uppercase">Problem</h2>
                    <p className="text-indigo-900/10">Research Focus</p>
                </div>
                <div className="w-1/2 h-full bg-gradient-to-bl from-purple-50/50 to-pink-50/50 p-8 text-right">
                    <h2 className="text-4xl font-bold text-purple-900/10 tracking-widest uppercase">Solution</h2>
                    <p className="text-purple-900/10">Design Focus</p>
                </div>
            </div>

            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                defaultEdgeOptions={defaultEdgeOptions}
                connectionMode={ConnectionMode.Loose}
                fitView
                className="z-10"
                minZoom={0.2}
            >
                <Background gap={20} color="#f1f5f9" />
                <Controls className="bg-white/80 backdrop-blur-sm border-white/50 shadow-xl" />
            </ReactFlow>
        </div>
    );
}
