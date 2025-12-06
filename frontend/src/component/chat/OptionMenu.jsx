import React, { useState, useRef, useEffect } from "react";
import { Trash2, RotateCcw } from "lucide-react";

export const OptionsMenu = ({
  show,
  withReasoning,
  toolsEnabled,
  plannerMode,
  onReasoningToggle,
  onToolsToggle,
  onPlannerToggle,
  onReset,
  onClear,
}) => {
  if (!show) return null;

  return (
    <div className="absolute bottom-full left-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 p-3 min-w-[180px] z-10">
      <div className="space-y-2">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Reasoning
          </label>
          <div className="flex gap-1 bg-gray-100 p-0.5 rounded">
            <button
              onClick={() => onReasoningToggle(true)}
              className={`flex-1 text-xs px-2 py-1 rounded transition-all ${
                withReasoning
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              On
            </button>
            <button
              onClick={() => onReasoningToggle(false)}
              className={`flex-1 text-xs px-2 py-1 rounded transition-all ${
                !withReasoning
                  ? "bg-red-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              Off
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Tools
          </label>
          <div className="flex gap-1 bg-gray-100 p-0.5 rounded">
            <button
              onClick={() => onToolsToggle(true)}
              className={`flex-1 text-xs px-2 py-1 rounded transition-all ${
                toolsEnabled
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              On
            </button>
            <button
              onClick={() => onToolsToggle(false)}
              className={`flex-1 text-xs px-2 py-1 rounded transition-all ${
                !toolsEnabled
                  ? "bg-red-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              Off
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Planner
          </label>
          <div className="flex gap-1 bg-gray-100 p-0.5 rounded">
            <button
              onClick={() => onPlannerToggle(true)}
              className={`flex-1 text-xs px-2 py-1 rounded transition-all ${
                plannerMode
                  ? "bg-green-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              On
            </button>
            <button
              onClick={() => onPlannerToggle(false)}
              className={`flex-1 text-xs px-2 py-1 rounded transition-all ${
                !plannerMode
                  ? "bg-red-600 text-white shadow-sm"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              Off
            </button>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-2 space-y-1">
          <button
            onClick={onReset}
            className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors text-xs font-medium"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
          <button
            onClick={onClear}
            className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors text-xs font-medium"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        </div>
      </div>
    </div>
  );
};
