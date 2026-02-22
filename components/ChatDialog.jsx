"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, Send, Loader2, GitBranch } from "lucide-react";
import axios from "axios";

const CATEGORY_COLORS = {
    Who: { border: "border-rose-200", bg: "bg-rose-50", header: "bg-rose-100/60", text: "text-rose-700", dot: "bg-rose-400", accent: "#fb7185" },
    What: { border: "border-blue-200", bg: "bg-blue-50", header: "bg-blue-100/60", text: "text-blue-700", dot: "bg-blue-400", accent: "#60a5fa" },
    When: { border: "border-amber-200", bg: "bg-amber-50", header: "bg-amber-100/60", text: "text-amber-700", dot: "bg-amber-400", accent: "#fbbf24" },
    Where: { border: "border-emerald-200", bg: "bg-emerald-50", header: "bg-emerald-100/60", text: "text-emerald-700", dot: "bg-emerald-400", accent: "#34d399" },
    Why: { border: "border-purple-200", bg: "bg-purple-50", header: "bg-purple-100/60", text: "text-purple-700", dot: "bg-purple-400", accent: "#a78bfa" },
    How: { border: "border-indigo-200", bg: "bg-indigo-50", header: "bg-indigo-100/60", text: "text-indigo-700", dot: "bg-indigo-400", accent: "#818cf8" },
};

export default function ChatDialog({ suggestion, onClose, onAddNodes, existingNodes }) {
    const [messages, setMessages] = useState([]);      // { role, content }
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isConverting, setIsConverting] = useState(false);
    const bottomRef = useRef(null);
    const inputRef = useRef(null);

    const colors = CATEGORY_COLORS[suggestion?.category] || CATEGORY_COLORS.What;

    // 다이얼로그가 열리면 AI가 먼저 제안을 설명하는 첫 메시지 시작
    useEffect(() => {
        if (!suggestion) return;
        setMessages([]);
        setInput("");
        sendMessage("이 제안에 대해 먼저 설명해줘.", true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [suggestion?.id]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async (text, isInitial = false) => {
        const userMsg = isInitial ? null : { role: "user", content: text };
        const historyForApi = isInitial ? [] : messages;

        if (!isInitial) {
            setMessages((prev) => [...prev, { role: "user", content: text }]);
        }
        setInput("");
        setIsLoading(true);

        try {
            const payload = {
                suggestion_title: suggestion.title,
                suggestion_content: suggestion.content,
                suggestion_category: suggestion.category,
                suggestion_phase: suggestion.phase,
                messages: historyForApi,
                user_message: text,
            };
            const res = await axios.post("http://localhost:8000/chat", payload);
            setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "죄송합니다, 오류가 발생했습니다. 다시 시도해주세요." },
            ]);
        } finally {
            setIsLoading(false);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;
        sendMessage(input.trim());
    };

    const handleConvertToNodes = async () => {
        if (messages.length === 0 || isConverting) return;
        setIsConverting(true);
        try {
            const payload = {
                suggestion_title: suggestion.title,
                suggestion_content: suggestion.content,
                suggestion_category: suggestion.category,
                suggestion_phase: suggestion.phase,
                messages,
                existing_nodes: existingNodes.map((n) => ({
                    id: n.id,
                    data: {
                        title: n.data.title,
                        category: n.data.category,
                        phase: n.data.phase,
                    },
                    position: n.position,
                })),
            };
            const res = await axios.post("http://localhost:8000/chat-to-nodes", payload);
            onAddNodes(res.data);
            onClose();
        } catch (err) {
            alert("노드 변환에 실패했습니다. 백엔드 상태를 확인해주세요.");
        } finally {
            setIsConverting(false);
        }
    };

    if (!suggestion) return null;

    return (
        <AnimatePresence>
            <motion.div
                key="chat-dialog"
                initial={{ opacity: 0, y: 30, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 30, scale: 0.96 }}
                transition={{ type: "spring", damping: 24, stiffness: 260 }}
                className={`absolute bottom-28 right-4 w-80 z-50 rounded-2xl border ${colors.border} shadow-2xl flex flex-col overflow-hidden`}
                style={{
                    maxHeight: "420px",
                    background: "rgba(255,255,255,0.97)",
                    backdropFilter: "blur(12px)",
                }}
            >
                {/* Header */}
                <div className={`flex items-center justify-between px-3 py-2.5 ${colors.header} border-b ${colors.border}`}>
                    <div className="flex items-center gap-2 min-w-0">
                        <Sparkles className="w-3.5 h-3.5 text-yellow-500 shrink-0" />
                        <div className="min-w-0">
                            <div className={`text-[10px] font-bold uppercase tracking-wider ${colors.text}`}>
                                {suggestion.category} · {suggestion.phase}
                            </div>
                            <div className="text-xs font-semibold text-gray-800 truncate max-w-[190px]">
                                {suggestion.title}
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-full hover:bg-black/10 transition-colors shrink-0"
                    >
                        <X className="w-3.5 h-3.5 text-gray-500" />
                    </button>
                </div>

                {/* Messages */}
                <div
                    className="flex-1 overflow-y-auto px-3 py-3 flex flex-col gap-2.5"
                    style={{ scrollbarWidth: "none", minHeight: 0 }}
                >
                    {messages.length === 0 && !isLoading && (
                        <div className="text-xs text-gray-400 text-center mt-4">AI가 이 제안을 설명하는 중...</div>
                    )}
                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            {msg.role === "assistant" && (
                                <span className="w-5 h-5 rounded-full bg-yellow-100 border border-yellow-200 flex items-center justify-center mr-1.5 mt-0.5 shrink-0">
                                    <Sparkles className="w-2.5 h-2.5 text-yellow-500" />
                                </span>
                            )}
                            <div
                                className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${msg.role === "user"
                                        ? "bg-indigo-500 text-white rounded-br-sm"
                                        : `${colors.bg} border ${colors.border} text-gray-700 rounded-bl-sm`
                                    }`}
                            >
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start">
                            <span className="w-5 h-5 rounded-full bg-yellow-100 border border-yellow-200 flex items-center justify-center mr-1.5 shrink-0">
                                <Sparkles className="w-2.5 h-2.5 text-yellow-500" />
                            </span>
                            <div className={`${colors.bg} border ${colors.border} rounded-xl rounded-bl-sm px-3 py-2`}>
                                <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-400" />
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* Input */}
                <div className={`border-t ${colors.border} px-2 py-2 flex flex-col gap-1.5`}>
                    <form onSubmit={handleSubmit} className="flex gap-1.5">
                        <input
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="아이디어를 이어서 얘기해보세요..."
                            disabled={isLoading}
                            className="flex-1 text-xs px-3 py-2 rounded-xl border border-gray-200 bg-gray-50 outline-none focus:border-indigo-300 focus:bg-white transition-colors placeholder-gray-400 disabled:opacity-50"
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="p-2 rounded-xl bg-indigo-500 hover:bg-indigo-600 disabled:opacity-40 transition-colors"
                        >
                            <Send className="w-3.5 h-3.5 text-white" />
                        </button>
                    </form>

                    {/* Convert to nodes button */}
                    {messages.length >= 2 && (
                        <button
                            onClick={handleConvertToNodes}
                            disabled={isConverting}
                            className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl 
                                       bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600
                                       text-white text-xs font-semibold transition-all disabled:opacity-50 shadow-sm"
                        >
                            {isConverting ? (
                                <>
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    노드 생성 중...
                                </>
                            ) : (
                                <>
                                    <GitBranch className="w-3 h-3" />
                                    대화를 노드로 만들기
                                </>
                            )}
                        </button>
                    )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
