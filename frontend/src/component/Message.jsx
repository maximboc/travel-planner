import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CheckCircle2, AlertCircle } from "lucide-react";

export const Message = ({ msg }) => (
  <div
    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
  >
    <div
      className={`max-w-[85%] rounded-2xl px-6 py-4 shadow-sm overflow-hidden ${
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
        <div className="flex items-center gap-2 mb-3 text-green-700 font-bold text-sm border-b border-green-200 pb-2">
          <CheckCircle2 className="w-4 h-4" />
          Final Itinerary
        </div>
      )}
      {msg.needsInput && (
        <div className="flex items-center gap-2 mb-3 text-blue-700 font-bold text-sm border-b border-blue-200 pb-2">
          <AlertCircle className="w-4 h-4 animate-pulse" />
          Awaiting Your Response
        </div>
      )}

      {/* Markdown Renderer */}
      <div className={`text-sm leading-relaxed ${msg.role === "user" ? "text-white" : "text-gray-800"}`}>
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            // Custom styling for Markdown elements
            h1: ({node, ...props}) => <h1 className="text-lg font-bold mt-4 mb-2 border-b pb-1" {...props} />,
            h2: ({node, ...props}) => <h2 className="text-base font-bold mt-3 mb-2 text-purple-700" {...props} />,
            h3: ({node, ...props}) => <h3 className="text-sm font-bold mt-2 mb-1 text-indigo-600" {...props} />,
            ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
            ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
            strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
            p: ({node, ...props}) => <p className="mb-2 last:mb-0 whitespace-pre-wrap" {...props} />,
            a: ({node, ...props}) => <a className="text-blue-600 hover:underline" target="_blank" {...props} />
          }}
        >
          {msg.content}
        </ReactMarkdown>
      </div>
    </div>
  </div>
);
