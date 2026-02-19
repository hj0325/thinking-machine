"use client";

import { useState, useCallback } from "react";
import {
    useNodesState,
    useEdgesState,
    Node,
    Edge,
    addEdge,
    Connection,
} from "reactflow";
import axios from "axios";
import { Loader2 } from "lucide-react";
import NodeMap from "./NodeMap";
import InputPanel from "./InputPanel";

interface ThinkingMachineProps { }

const INITIAL_NODES: Node[] = [];
const INITIAL_EDGES: Edge[] = [];

export default function ThinkingMachine({ }: ThinkingMachineProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    const handleInputSubmit = async (text: string) => {
        setIsAnalyzing(true);

        try {
            // Prepare the payload with current graph state for context
            const payload = {
                text,
                current_nodes: nodes.map(n => ({
                    id: n.id,
                    type: n.type || "default",
                    content: n.data.label, // ReactFlow stores content in data.label usually, but we need to align with our backend model
                    phase: n.data.phase || "Problem",
                    category: n.data.category || "What",
                    position: n.position,
                    is_ai_suggestion: n.data.is_ai_suggestion || false
                })),
                current_edges: edges.map(e => ({
                    id: e.id,
                    source: e.source,
                    target: e.target,
                    label: e.label as string || undefined
                }))
            };

            // Call Backend
            const response = await axios.post("http://localhost:8000/analyze", payload);
            const data = response.data; // AnalysisResponse

            // Process new nodes
            const newReactFlowNodes = data.new_nodes.map((n: any) => ({
                id: n.id,
                type: n.type,
                position: n.position,
                data: {
                    title: n.title, // New field
                    label: n.content, // Body
                    phase: n.phase,
                    category: n.category,
                    is_ai_suggestion: n.is_ai_suggestion
                },
                style: {
                    background: n.is_ai_suggestion
                        ? 'rgba(254, 252, 232, 0.9)'
                        : (n.phase === 'Problem' ? 'rgba(255, 241, 242, 0.9)' : 'rgba(240, 249, 255, 0.9)'),
                    border: n.is_ai_suggestion
                        ? '2px dashed #eab308'
                        : (n.phase === 'Problem' ? '1px solid #fda4af' : '1px solid #bae6fd'),
                    borderRadius: '12px',
                    padding: '0', // Reset padding to handle internal layout
                    width: 200,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    backdropFilter: 'blur(8px)'
                }
            }));

            // Map to Custom Node Content logic (inline style for now, better to allow customization later)
            // Custom render inside the node using label prop?
            // React Flow default node just renders 'label'.
            // We can pass a JSX element as label!

            const enrichedNodes = newReactFlowNodes.map((n: any) => ({
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

            const newReactFlowEdges = data.new_edges.map((e: any) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                label: e.label,
                type: 'smoothstep',
                animated: true,
                style: e.label === 'suggestion' ? { stroke: '#eab308', strokeDasharray: 5 } : undefined
            }));

            setNodes((nds) => [...nds, ...enrichedNodes]);
            setEdges((eds) => [...eds, ...newReactFlowEdges]);

        } catch (error) {
            console.error("Failed to analyze input:", error);
            alert("Failed to connect to AI Agent. Is the backend running?");
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
