import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Plane,
  Calendar,
  DollarSign,
  MapPin,
  Hotel,
  Compass,
  Sun,
  Users,
  CheckCircle2,
  Loader2,
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
  Scale,
} from "lucide-react";

export const Header = ({
  awaitingUserInput,
  showDetails,
  setShowDetails,
  activeTab,
  setActiveTab,
}) => (
  <header className="bg-white/80 backdrop-blur-md border-b border-purple-100 sticky top-0 z-50 shadow-sm">
    <div className="max-w-7xl mx-auto px-6">
      <div className="flex items-center justify-between h-20">
        {/* Left Side: Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-2 rounded-xl">
            <Plane className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Travel Planner AI
            </h1>
            <p className="text-sm text-gray-600">
              Your intelligent travel companion
            </p>
          </div>
        </div>

        {/* Center: Tab Navigation */}
        <div className="flex items-center gap-2 bg-gray-100 p-1.5 rounded-xl">
          <button
            onClick={() => setActiveTab("planner")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "planner"
                ? "bg-white text-purple-700 shadow-md"
                : "text-gray-600 hover:bg-gray-200"
            }`}
          >
            <Plane className="w-4 h-4" />
            Planner
          </button>
          <button
            onClick={() => setActiveTab("evaluation")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "evaluation"
                ? "bg-white text-purple-700 shadow-md"
                : "text-gray-600 hover:bg-gray-200"
            }`}
          >
            <Scale className="w-4 h-4" />
            Evaluation
          </button>
        </div>

        {/* Right Side: Status & Controls */}
        <div className="flex items-center gap-3">
          {awaitingUserInput && (
            <div className="flex px-4 py-2 rounded-lg bg-blue-50 border border-blue-300 text-sm font-medium text-blue-700 items-center gap-2">
              <AlertCircle className="w-4 h-4 animate-pulse" />
              <span className="hidden sm:inline">Awaiting Response</span>
            </div>
          )}

          {!awaitingUserInput && (
            <div className="hidden sm:flex px-4 py-2 rounded-lg bg-white border border-purple-200 text-sm font-medium text-purple-700 items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              Online
            </div>
          )}

          {activeTab === "planner" && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                showDetails
                  ? "bg-purple-100 text-purple-700 border border-purple-200"
                  : "bg-white text-gray-600 border border-gray-200 hover:border-purple-300"
              }`}
            >
              {showDetails ? (
                <>
                  <PanelRightClose className="w-4 h-4" />
                  <span className="hidden sm:inline">Hide Details</span>
                </>
              ) : (
                <>
                  <PanelRight className="w-4 h-4" />
                  <span className="hidden sm:inline">Show Plan Details</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  </header>
);
