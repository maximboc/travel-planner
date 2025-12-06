import React, { useState, useRef, useEffect } from "react";
import { Wrench, Brain, Sparkles } from "lucide-react";

export const ModeIndicators = ({
  withReasoning,
  toolsEnabled,
  plannerMode,
}) => {
  const activeModes = [];

  if (withReasoning) {
    activeModes.push({ icon: Brain, label: "Reasoning", color: "purple" });
  }
  if (toolsEnabled) {
    activeModes.push({ icon: Wrench, label: "Tools", color: "blue" });
  }
  if (plannerMode) {
    activeModes.push({ icon: Sparkles, label: "Planner", color: "green" });
  }

  if (activeModes.length === 0) return null;

  return (
    <div className="flex gap-2 mb-2 flex-wrap justify-end">
      {activeModes.map((mode, idx) => (
        <div
          key={idx}
          className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-medium bg-${mode.color}-50 text-${mode.color}-700 border border-${mode.color}-200`}
        >
          <mode.icon className="w-3 h-3" />
          {mode.label}
        </div>
      ))}
    </div>
  );
};
