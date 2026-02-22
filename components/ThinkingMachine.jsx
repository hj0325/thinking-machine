"use client";

import { useState, useCallback } from "react";
import {
    useNodesState,
    useEdgesState,
    addEdge,
} from "reactflow";
import axios from "axios";
import { Loader2 } from "lucide-react";
import NodeMap from "./NodeMap";
import InputPanel from "./InputPanel";

const INITIAL_NODES = [];
const INITIAL_EDGES = [];

export default function ThinkingMachine() {
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const onConnect = useCallback(
        (params) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    const handleInputSubmit = async (text) => {
        setIsAnalyzing(true);

        try {
            // Prepare the payload 
            // We pass existing nodes as history if needed.
            const payload = {
                text,
                history: nodes.map(n => ({
                    id: n.id,
                    data: {
                        title: n.data.title,
                        category: n.data.category,
                        phase: n.data.phase,
                    },
                    position: n.position
                }))
            };

            // Call Backend
            const response = await axios.post("http://localhost:8000/analyze", payload);
            const data = response.data; // AnalysisResponse: { nodes: Node[], edges: Edge[] }

            // Process new nodes
            const newReactFlowNodes = data.nodes.map((n) => ({
                id: n.id,
                type: n.type || 'default',
                position: n.position,
                data: {
                    title: n.data.label,      // Map backend 'label' (title) to frontend 'title'
                    label: n.data.content,    // Map backend 'content' (detail) to frontend 'label' (body)
                    phase: n.data.phase,
                    category: n.data.category,
                    is_ai_suggestion: n.data.is_ai_generated // Map to frontend prop
                },
                style: {
                    background: n.data.is_ai_generated
                        ? 'rgba(254, 252, 232, 0.9)'
                        : (n.data.phase === 'Problem' ? 'rgba(255, 241, 242, 0.9)' : 'rgba(240, 249, 255, 0.9)'),
                    border: n.data.is_ai_generated
                        ? '2px dashed #eab308'
                        : (n.data.phase === 'Problem' ? '1px solid #fda4af' : '1px solid #bae6fd'),
                    borderRadius: '12px',
                    padding: '0',
                    width: 200,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    backdropFilter: 'blur(8px)'
                }
            }));

            // JSX rendering in nodes
            const enrichedNodes = newReactFlowNodes.map((n) => ({
                ...n,
                data: {
                    ...n.data,
                    label: (
                        <div className="flex flex-col h-full text-left">
                            <div className="px-3 py-2 border-b border-black/5 bg-black/5 text-[10px] font-bold uppercase tracking-wider opacity-70 flex justify-between items-center">
                                <span>{n.data.category}</span>
                                <span className={`w-2 h-2 rounded-full ${n.data.phase === 'Problem' ? 'bg-red-400' : 'bg-blue-400'}`}></span>
                            </div>
                            <div className="p-3">
                                <div className="font-bold text-sm mb-1 text-gray-800 leading-tight">{n.data.title}</div>
                                <div className="text-xs text-gray-600 leading-relaxed line-clamp-4">{n.data.label}</div>
                            </div>
                        </div>
                    )
                }
            }));

            const newReactFlowEdges = data.edges.map((e) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                label: e.label,
                type: 'smoothstep',
                animated: true,
                style: { stroke: '#94a3b8' } // Default style
            }));

            // Adjust edge style based on type
            newReactFlowEdges.forEach((e) => {
                if (e.id.startsWith('e-cross-')) {
                    // 기존 노드와의 cross-connection: 보라색 굵은 실선
                    e.style = { stroke: '#8b5cf6', strokeWidth: 2.5 };
                    e.animated = false;
                } else if (e.label === 'suggestion' || e.label === 'expansion') {
                    // 내부 AI 제안 연결: 노란 점선
                    e.style = { stroke: '#eab308', strokeDasharray: 5 };
                }
            });

            setNodes((nds) => [...nds, ...enrichedNodes]);
            setEdges((eds) => [...eds, ...newReactFlowEdges]);

        } catch (error) {
            console.error("Failed to analyze input:", error);
            alert("Failed to connect to AI Agent. Check if backend is running and OpenAI Key is set.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <div className="w-full h-screen relative flex flex-col overflow-hidden bg-slate-50">
            <header className="absolute top-0 left-0 right-0 z-50 p-6 flex justify-between items-center bg-transparent pointer-events-none">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 pointer-events-auto">
                    Visual Thinking Machine
                </h1>
                <div className="flex gap-2 pointer-events-auto">
                    <div className="px-3 py-1 rounded-full bg-white/50 border border-indigo-100 text-xs text-indigo-800 backdrop-blur-sm shadow-sm flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
                        Autonomous Agent Active
                    </div>
                </div>
            </header>

            <main className="flex-1 w-full h-full relative">
                <NodeMap
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                />
                <InputPanel onSubmit={handleInputSubmit} isAnalyzing={isAnalyzing} />
            </main>
        </div>
    );
}
