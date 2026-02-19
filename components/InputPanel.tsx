"use client";

import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

interface InputPanelProps {
    onSubmit: (text: string) => void;
    isAnalyzing: boolean;
}

export default function InputPanel({ onSubmit, isAnalyzing }: InputPanelProps) {
    const [text, setText] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (text.trim() && !isAnalyzing) {
            onSubmit(text);
            setText("");
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-2xl z-50 px-4"
        >
            <form onSubmit={handleSubmit} className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-100 to-purple-100 rounded-2xl blur-xl opacity-20 group-hover:opacity-30 transition-opacity" />

                <div className="relative bg-white/80 backdrop-blur-xl border border-white/50 shadow-2xl rounded-2xl p-2 flex items-end gap-2">
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                        placeholder="What are you thinking? describe your idea..."
                        className="w-full bg-transparent border-none outline-none resize-none p-3 text-gray-700 placeholder-gray-400 min-h-[60px] max-h-[200px]"
                        disabled={isAnalyzing}
                    />

                    <button
                        type="submit"
                        disabled={!text.trim() || isAnalyzing}
                        className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl text-white shadow-lg hover:shadow-indigo-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
                    >
                        {isAnalyzing ? (
                            <Sparkles className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </form>
        </motion.div>
    );
}
