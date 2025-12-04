import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Plane,
  Calendar,
  DollarSign,
  MapPin,
  Hotel,
  Compass,
  PanelRight,
  PanelRightClose,
  AlertCircle,
  Trash2,
  Edit3,
  Plus,
  RotateCcw,
  Brain,
  Wrench,
  Sparkles,
} from "lucide-react";

import { OptionsMenu } from './OptionMenu'
import { ModeIndicators } from './ModeIndicators'

export const ChatInput = ({
  input,
  setInput,
  isLoading,
  awaitingUserInput,
  sessionId,
  showOptionsMenu,
  setShowOptionsMenu,
  withReasoning,
  toolsEnabled,
  plannerMode,
  onSubmit,
  onReasoningToggle,
  onToolsToggle,
  onPlannerToggle,
  onReset,
  onClear,
}) => {
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="border-t border-purple-100 p-4 bg-gray-50/50">
      <ModeIndicators
        withReasoning={withReasoning}
        toolsEnabled={toolsEnabled}
        plannerMode={plannerMode}
      />
      <div className="flex gap-3 relative">
        <div className="relative">
          <button
            onClick={() => setShowOptionsMenu(!showOptionsMenu)}
            className={`p-4 border rounded-xl transition-all ${
              showOptionsMenu
                ? "bg-purple-100 border-purple-300 text-purple-600"
                : "bg-white border-purple-200 text-gray-500 hover:border-purple-400"
            }`}
            title="Options"
          >
            <Plus
              className={`w-5 h-5 transition-transform ${
                showOptionsMenu ? "rotate-45" : ""
              }`}
            />
          </button>
          <OptionsMenu
            show={showOptionsMenu}
            withReasoning={withReasoning}
            toolsEnabled={toolsEnabled}
            plannerMode={plannerMode}
            onReasoningToggle={onReasoningToggle}
            onToolsToggle={onToolsToggle}
            onPlannerToggle={onPlannerToggle}
            onReset={onReset}
            onClear={onClear}
          />
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            awaitingUserInput
              ? "Please provide the requested information..."
              : "Ex: I want to go to Tokyo next week for $3000..."
          }
          className="flex-1 px-6 py-4 rounded-xl border border-purple-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 focus:outline-none bg-white shadow-sm transition-all placeholder:text-gray-400"
          disabled={isLoading}
        />
        <button
          onClick={onSubmit}
          disabled={isLoading || !input.trim()}
          className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-400 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Send className="w-5 h-5" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </div>
      <p className="text-xs text-center text-gray-400 mt-2">
        Session: <span className="font-mono">{sessionId.slice(-6)}</span> •
        Powered by Amadeus & LangGraph
      </p>
    </div>
  );
};

