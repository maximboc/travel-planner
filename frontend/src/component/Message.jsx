import React, { useState, useRef, useEffect } from "react";
import { CheckCircle2, AlertCircle, } from "lucide-react";

export const Message = ({ msg }) => (
  <div
    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
  >
    <div
      className={`max-w-[85%] rounded-2xl px-6 py-4 shadow-sm ${
        msg.role === "user"
          ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-tr-none"
          : msg.isFinal
          ? "bg-gradient-to-r from-green-50 to-emerald-50 text-gray-800 border-2 border-green-200 rounded-tl-none"
          : msg.isError
          ? "bg-red-50 text-red-800 border border-red-200 rounded-tl-none"
          : msg.needsInput
          ? "bg-blue-50 text-gray-800 border-2 border-blue-300 rounded-tl-none"
          : "bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none"
      }`}
    >
      {msg.isFinal && (
        <div className="flex items-center gap-2 mb-2 text-green-600 font-semibold text-sm">
          <CheckCircle2 className="w-4 h-4" />
          Final Itinerary
        </div>
      )}
      {msg.needsInput && (
        <div className="flex items-center gap-2 mb-2 text-blue-600 font-semibold text-sm">
          <AlertCircle className="w-4 h-4 animate-pulse" />
          Awaiting Your Response
        </div>
      )}

      <p className="text-sm leading-relaxed whitespace-pre-wrap">
        {msg.content}
      </p>
    </div>
  </div>
);

