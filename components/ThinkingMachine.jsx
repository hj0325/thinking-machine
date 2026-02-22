"use client";

import { useState, useCallback } from "react";
import {
    useNodesState,
    useEdgesState,
    addEdge,
} from "reactflow";
import axios from "axios";
import NodeMap from "./NodeMap";
import InputPanel from "./InputPanel";
import SuggestionPanel from "./SuggestionPanel";

const INITIAL_NODES = [];
const INITIAL_EDGES = [];

export default function ThinkingMachine() {
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // AI 제안 패널 상태
    const [suggestions, setSuggestions] = useState([]);
    // 제안과 연결된 노드 ID들 (글로우 효과)
    const [highlightedNodeIds, setHighlightedNodeIds] = useState(new Set());

    const onConnect = useCallback(
        (params) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    const handleDismissSuggestion = (suggestionId) => {
        setSuggestions((prev) => {
            const dismissed = prev.find((s) => s.id === suggestionId);
            if (dismissed) {
                setHighlightedNodeIds((ids) => {
                    const next = new Set(ids);
                    next.delete(dismissed.relatedNodeId);
                    return next;
                });
            }
            return prev.filter((s) => s.id !== suggestionId);
        });
    };

    const handleInputSubmit = async (text) => {
        setIsAnalyzing(true);

        try {
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

            const response = await axios.post("http://localhost:8000/analyze", payload);
            const data = response.data;

            // ── 제안 노드(is_ai_generated=true)와 사용자 노드 분리 ──
            const suggestionNodeData = data.nodes.find(n => n.data.is_ai_generated);
            const userNodeDatas = data.nodes.filter(n => !n.data.is_ai_generated);

            // e-suggest- 엣지에서 연결된 사용자 노드 ID 파악
            const suggestEdge = data.edges.find(e => e.id.startsWith("e-suggest-"));
            const highlightedMainNodeId = suggestEdge ? suggestEdge.source : null;

            // ── 사용자 노드 → ReactFlow에 추가 ──
            const newReactFlowNodes = userNodeDatas.map((n) => ({
                id: n.id,
                type: n.type || 'default',
                position: n.position,
                className: n.id === highlightedMainNodeId ? 'node-highlighted' : '',
                data: {
                    title: n.data.label,
                    label: n.data.content,
                    phase: n.data.phase,
                    category: n.data.category,
                    is_ai_suggestion: false,
                },
                style: {
                    background: n.data.phase === 'Problem'
                        ? 'rgba(255, 241, 242, 0.9)'
                        : 'rgba(240, 249, 255, 0.9)',
                    border: n.data.phase === 'Problem'
                        ? '1px solid #fda4af'
                        : '1px solid #bae6fd',
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

            // JSX 렌더링
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

            // ── 제안 노드 → SuggestionPanel 상태로 ──
            if (suggestionNodeData) {
                const newSuggestion = {
                    id: `suggestion-${Date.now()}`,
                    title: suggestionNodeData.data.label,
                    content: suggestionNodeData.data.content,
                    category: suggestionNodeData.data.category,
                    phase: suggestionNodeData.data.phase,
                    relatedNodeId: highlightedMainNodeId,
                };
                setSuggestions((prev) => [newSuggestion, ...prev]);
                if (highlightedMainNodeId) {
                    setHighlightedNodeIds((prev) => new Set([...prev, highlightedMainNodeId]));
                }
            }

            // ── 엣지 처리 (제안 노드 관련 e-suggest- 엣지는 제외) ──
            const newReactFlowEdges = data.edges
                .filter(e => !e.id.startsWith('e-suggest-'))
                .map((e) => ({
                    id: e.id,
                    source: e.source,
                    target: e.target,
                    label: e.label,
                    type: 'smoothstep',
                    animated: true,
                    style: { stroke: '#94a3b8' }
                }));

            newReactFlowEdges.forEach((e) => {
                if (e.id.startsWith('e-cross-')) {
                    e.style = { stroke: '#8b5cf6', strokeWidth: 2.5 };
                    e.animated = false;
                } else if (e.id.startsWith('e-input-')) {
                    e.style = { stroke: '#6366f1', strokeDasharray: '4 3', strokeWidth: 1.5 };
                    e.animated = false;
                }
            });

            setNodes((nds) => {
                // 이미 존재하는 하이라이트 노드에 className 업데이트
                const updated = nds.map(n => ({
                    ...n,
                    className: highlightedNodeIds.has(n.id) ? 'node-highlighted' : (n.className || ''),
                }));
                return [...updated, ...enrichedNodes];
            });
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

                {/* AI 제안 우측 패널 */}
                <SuggestionPanel
                    suggestions={suggestions}
                    onDismiss={handleDismissSuggestion}
                />

                <InputPanel onSubmit={handleInputSubmit} isAnalyzing={isAnalyzing} />
            </main>
        </div>
    );
}
