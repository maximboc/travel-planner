import { Plane, Hotel, Compass, Sun } from 'lucide-react'
import React, { useState, useRef, useEffect } from "react";

export const QuickActions = ({ setInput, showDetails }) => {
  const quickActions = [
    { icon: Plane, text: "Find Flights", color: "from-blue-500 to-cyan-500" },
    { icon: Hotel, text: "Book Hotels", color: "from-purple-500 to-pink-500" },
    { icon: Compass, text: "Activities", color: "from-orange-500 to-red-500" },
    { icon: Sun, text: "Weather", color: "from-yellow-500 to-orange-500" },
  ];

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Quick Actions
      </h2>
      <div
        className={`grid gap-4 ${
          showDetails ? "grid-cols-2" : "grid-cols-2 md:grid-cols-4"
        }`}
      >
        {quickActions.map((action, idx) => (
          <button
            key={idx}
            onClick={() => setInput(`Help me ${action.text.toLowerCase()}`)}
            className="group relative overflow-hidden bg-white p-6 rounded-2xl border border-gray-200 hover:border-transparent hover:shadow-xl transition-all duration-300 text-left"
          >
            <div
              className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-0 group-hover:opacity-10 transition-opacity`}
            />
            <div
              className={`bg-gradient-to-br ${action.color} w-12 h-12 rounded-xl flex items-center justify-center mb-3`}
            >
              <action.icon className="w-6 h-6 text-white" />
            </div>
            <p className="font-semibold text-gray-800 text-sm">
              {action.text}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};

