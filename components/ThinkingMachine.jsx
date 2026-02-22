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
import ChatDialog from "./ChatDialog";

const INITIAL_NODES = [];
const INITIAL_EDGES = [];

// 노드 데이터에서 JSX label 빌드 (재사용)
function buildNodeLabel(nodeData) {
    return (
        <div className="flex flex-col h-full text-left">
            <div className="px-3 py-2 border-b border-black/5 bg-black/5 text-[10px] font-bold uppercase tracking-wider opacity-70 flex justify-between items-center">
                <span>{nodeData.category}</span>
                <span className={`w-2 h-2 rounded-full ${nodeData.phase === 'Problem' ? 'bg-red-400' : 'bg-blue-400'}`}></span>
            </div>
            <div className="p-3">
                <div className="font-bold text-sm mb-1 text-gray-800 leading-tight">{nodeData.title}</div>
                <div className="text-xs text-gray-600 leading-relaxed line-clamp-4">{nodeData.label}</div>
            </div>
        </div>
    );
}

function buildNodeStyle(phase) {
    return {
        background: phase === 'Problem' ? 'rgba(255, 241, 242, 0.9)' : 'rgba(240, 249, 255, 0.9)',
        border: phase === 'Problem' ? '1px solid #fda4af' : '1px solid #bae6fd',
        borderRadius: '12px',
        padding: '0',
        width: 200,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        backdropFilter: 'blur(8px)',
    };
}

function buildEdgeStyle(edgeId) {
    if (edgeId.startsWith('e-cross-')) {
        return { style: { stroke: '#8b5cf6', strokeWidth: 2.5 }, animated: false };
    }
    if (edgeId.startsWith('e-input-') || edgeId.startsWith('e-chat-')) {
        return { style: { stroke: '#6366f1', strokeDasharray: '4 3', strokeWidth: 1.5 }, animated: false };
    }
    return { style: { stroke: '#94a3b8' }, animated: true };
}

function toReactFlowNode(n, highlightedId) {
    const nodeData = {
        title: n.data.label,
        label: n.data.content,
        phase: n.data.phase,
        category: n.data.category,
        is_ai_suggestion: false,
    };
    const rfNode = {
        id: n.id,
        type: n.type || 'default',
        position: n.position,
        className: n.id === highlightedId ? 'node-highlighted' : '',
        data: { ...nodeData },
        style: buildNodeStyle(n.data.phase),
    };
    rfNode.data.label = buildNodeLabel(nodeData);
    return rfNode;
}

export default function ThinkingMachine() {
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    // AI 제안 패널
    const [suggestions, setSuggestions] = useState([]);
    const [highlightedNodeIds, setHighlightedNodeIds] = useState(new Set());

    // Chat dialog
    const [activeSuggestion, setActiveSuggestion] = useState(null);

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
                // 열려있는 채팅창이 dismiss된 카드와 같으면 닫기
                if (activeSuggestion?.id === suggestionId) {
                    setActiveSuggestion(null);
                }
            }
            return prev.filter((s) => s.id !== suggestionId);
        });
    };

    const handleSuggestionClick = (suggestion) => {
        // 같은 카드 다시 클릭 시 토글
        if (activeSuggestion?.id === suggestion.id) {
            setActiveSuggestion(null);
        } else {
            setActiveSuggestion(suggestion);
        }
    };

    // 채팅 대화에서 노드+엣지 추가
    const handleAddNodesFromChat = (data) => {
        const newEdges = data.edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            label: e.label,
            type: 'smoothstep',
            ...buildEdgeStyle(e.id),
        }));

        const newNodes = data.nodes.map((n) => toReactFlowNode(n, null));

        setNodes((nds) => [...nds, ...newNodes]);
        setEdges((eds) => [...eds, ...newEdges]);
    };

    const handleInputSubmit = async (text) => {
        setIsAnalyzing(true);

        try {
            const payload = {
                text,
                history: nodes.map((n) => ({
                    id: n.id,
                    data: {
                        title: n.data.title,
                        category: n.data.category,
                        phase: n.data.phase,
                    },
                    position: n.position,
                })),
            };

            const response = await axios.post("http://localhost:8000/analyze", payload);
            const data = response.data;

            // 제안 노드(is_ai_generated=true)와 사용자 노드 분리
            const suggestionNodeData = data.nodes.find((n) => n.data.is_ai_generated);
            const userNodeDatas = data.nodes.filter((n) => !n.data.is_ai_generated);

            // e-suggest- 엣지에서 연결된 사용자 노드 ID 파악
            const suggestEdge = data.edges.find((e) => e.id.startsWith("e-suggest-"));
            const highlightedMainNodeId = suggestEdge ? suggestEdge.source : null;

            // 사용자 노드 → ReactFlow
            const enrichedNodes = userNodeDatas.map((n) => toReactFlowNode(n, highlightedMainNodeId));

            // 제안 노드 → SuggestionPanel
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

            // 엣지 처리 (e-suggest- 제외)
            const newReactFlowEdges = data.edges
                .filter((e) => !e.id.startsWith("e-suggest-"))
                .map((e) => ({
                    id: e.id,
                    source: e.source,
                    target: e.target,
                    label: e.label,
                    type: 'smoothstep',
                    ...buildEdgeStyle(e.id),
                }));

            setNodes((nds) => {
                // 기존 하이라이트된 노드의 className 갱신
                const updated = nds.map((n) => ({
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
                    highlightedNodeIds={highlightedNodeIds}
                />

                {/* AI 제안 우측 패널 */}
                <SuggestionPanel
                    suggestions={suggestions}
                    onDismiss={handleDismissSuggestion}
                    onSuggestionClick={handleSuggestionClick}
                    activeSuggestionId={activeSuggestion?.id}
                />

                {/* AI 채팅 대화창 */}
                {activeSuggestion && (
                    <ChatDialog
                        suggestion={activeSuggestion}
                        onClose={() => setActiveSuggestion(null)}
                        onAddNodes={handleAddNodesFromChat}
                        existingNodes={nodes}
                    />
                )}

                <InputPanel onSubmit={handleInputSubmit} isAnalyzing={isAnalyzing} />
            </main>
        </div>
    );
}
