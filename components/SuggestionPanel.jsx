"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X, MessageCircle } from "lucide-react";

const CATEGORY_COLORS = {
    Who: { bg: "bg-rose-50", border: "border-rose-200", text: "text-rose-700", dot: "bg-rose-400" },
    What: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", dot: "bg-blue-400" },
    When: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", dot: "bg-amber-400" },
    Where: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", dot: "bg-emerald-400" },
    Why: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700", dot: "bg-purple-400" },
    How: { bg: "bg-indigo-50", border: "border-indigo-200", text: "text-indigo-700", dot: "bg-indigo-400" },
};

export default function SuggestionPanel({ suggestions, onDismiss, onSuggestionClick, activeSuggestionId }) {
    if (suggestions.length === 0) return null;

    return (
        <motion.div
            initial={{ x: 340, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 340, opacity: 0 }}
            transition={{ type: "spring", damping: 22, stiffness: 200 }}
            className="absolute top-20 right-4 bottom-28 w-80 z-40 flex flex-col gap-3 overflow-y-auto pr-1"
            style={{ scrollbarWidth: "none" }}
        >
            {/* Header */}
            <div className="flex items-center gap-2 px-1">
                <div className="flex items-center gap-1.5 bg-yellow-50 border border-yellow-200 rounded-full px-3 py-1 shadow-sm">
                    <Sparkles className="w-3.5 h-3.5 text-yellow-500" />
                    <span className="text-xs font-semibold text-yellow-700">AI Suggestions</span>
                </div>
                <span className="text-xs text-gray-400">{suggestions.length}개</span>
            </div>

            {/* Suggestion cards */}
            <AnimatePresence mode="popLayout">
                {suggestions.map((s) => {
                    const colors = CATEGORY_COLORS[s.category] || CATEGORY_COLORS.What;
                    const isActive = s.id === activeSuggestionId;
                    return (
                        <motion.div
                            key={s.id}
                            layout
                            initial={{ opacity: 0, y: -12, scale: 0.96 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, x: 60, scale: 0.92 }}
                            transition={{ type: "spring", damping: 20, stiffness: 260 }}
                            className={`relative rounded-2xl border ${colors.border} ${colors.bg} 
                                        shadow-lg backdrop-blur-sm overflow-hidden group cursor-pointer
                                        transition-all duration-200 ${isActive ? "ring-2 ring-indigo-400 ring-offset-1" : "hover:shadow-xl"}`}
                            onClick={() => onSuggestionClick(s)}
                        >
                            {/* Dashed AI indicator */}
                            <div className="absolute inset-0 rounded-2xl border-2 border-dashed border-yellow-300 opacity-40 pointer-events-none" />

                            {/* Category header */}
                            <div className={`px-3 py-2 border-b ${colors.border} bg-white/30 
                                           flex items-center justify-between`}>
                                <div className="flex items-center gap-1.5">
                                    <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
                                    <span className={`text-[10px] font-bold uppercase tracking-wider ${colors.text}`}>
                                        {s.category} · {s.phase}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); onDismiss(s.id); }}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity 
                                                   p-0.5 rounded-full hover:bg-black/10"
                                    >
                                        <X className="w-3 h-3 text-gray-500" />
                                    </button>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="p-3">
                                <div className="font-bold text-sm text-gray-800 leading-tight mb-1.5 flex items-start gap-1">
                                    <Sparkles className="w-3 h-3 text-yellow-500 mt-0.5 shrink-0" />
                                    {s.title}
                                </div>
                                <p className="text-xs text-gray-600 leading-relaxed">{s.content}</p>
                            </div>

                            {/* Click hint */}
                            <div className="px-3 pb-2.5 flex items-center gap-1 text-[10px] text-gray-400">
                                <MessageCircle className="w-3 h-3" />
                                <span>클릭해서 AI와 더 얘기하기</span>
                            </div>
                        </motion.div>
                    );
                })}
            </AnimatePresence>
        </motion.div>
    );
}

