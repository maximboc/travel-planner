import { ChatInput } from "./component/ChatInput";
import { QuickActions } from './component/QuickActions'
import { TripDetailsSidebar } from './component/TripDetails'
import { Header } from './component/Header'
import { ProcessingSteps } from './component/ProcessingSteps'
import { Message } from './component/Message'
import React, { useState, useRef, useEffect } from "react";
import { Plane } from "lucide-react";

const INITIAL_AGENT_STATE = {
  plan: null,
  adults: null,
  children: null,
  infants: null,
  travel_class: null,
  city_code: null,
  origin_code: null,
  flight_data: null,
  selected_flight_index: null,
  validation_question: null,
  needs_user_input: false,
  hotel_data: null,
  selected_hotel_index: null,
  activity_data: null,
  current_node: null,
};

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(`session_${Date.now()}`);
  const [showDetails, setShowDetails] = useState(false);

  const [currentStreamingMessage, setCurrentStreamingMessage] = useState("");
  const [awaitingUserInput, setAwaitingUserInput] = useState(false);
  const [withReasoning, setWithReasoning] = useState(false);
  const [withTools, setWithTools] = useState(true);
  const [withPlanner, setWithPlanner] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editablePlan, setEditablePlan] = useState(null);
  const [showOptionsMenu, setShowOptionsMenu] = useState(false);

  const [agentState, setAgentState] = useState(INITIAL_AGENT_STATE);

  const [processingSteps, setProcessingSteps] = useState([]);
  const messagesEndRef = useRef(null);

  const handleReasoningToggle = async (enabled) => {
    setWithReasoning(enabled);
    try {
      await fetch("http://127.0.0.1:8000/chat/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          with_reasoning: enabled,
          with_planner: withPlanner,
          with_reasoning: withReasoning
        }),
      });
    } catch (error) {
      console.error("Failed to configure reasoning:", error);
    }
  };

  const handleToolsToggle = async (enabled) => {
    setWithTools(enabled);
    try {
      await fetch("http://127.0.0.1:8000/chat/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          with_tools: enabled,
          with_reasoning: withReasoning,
          with_planner: withPlanner
        }),
      });
    } catch (error) {
      console.error("Failed to configure tools:", error);
    }
  };

  const handlePlannerToggle = async (enabled) => {
    setWithPlanner(enabled);
    try {
      await fetch("http://127.0.0.1:8000/chat/configure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          with_planner: enabled,
          with_reasoning: withReasoning,
          with_tools: withTools
        }),
      });
    } catch (error) {
      console.error("Failed to configure planner:", error);
    }
  };

  const handleEdit = () => {
    if (agentState.plan) {
      setEditablePlan({ ...agentState.plan });
      setIsEditing(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditablePlan(null);
  };

  const handleUpdatePlan = async () => {
    if (!editablePlan) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/chat/update_plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          ...editablePlan,
        }),
      });

      if (!res.ok) throw new Error("Failed to update plan");

      const data = await res.json();
      setAgentState((prev) => ({ ...prev, ...data.state }));
      setIsEditing(false);
      setEditablePlan(null);
    } catch (error) {
      console.error("Failed to update plan:", error);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setInput("");
    setProcessingSteps([]);
    setCurrentStreamingMessage("");
    setAwaitingUserInput(false);
    setAgentState(INITIAL_AGENT_STATE);
    const newId = `session_${Date.now()}`;
    setSessionId(newId);
  };

  const clearConversation = () => {
    setMessages([]);
    setProcessingSteps([]);
    setCurrentStreamingMessage("");
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, processingSteps, currentStreamingMessage]);

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setProcessingSteps([]);
    setCurrentStreamingMessage("");
    setAwaitingUserInput(false);
    setShowOptionsMenu(false);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
        }),
      });

      if (!res.ok) throw new Error("Failed to connect to agent");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "node_start") {
                setProcessingSteps((prev) => [
                  ...prev,
                  {
                    node: data.node,
                    status: "processing",
                    timestamp: Date.now(),
                  },
                ]);
              } else if (data.type === "node_end") {
                setProcessingSteps((prev) =>
                  prev.map((step) =>
                    step.node === data.node && step.status === "processing"
                      ? { ...step, status: "completed" }
                      : step
                  )
                );
              } else if (data.type === "state_update") {
                setAgentState((prev) => ({ ...prev, ...data.state }));
              } else if (data.type === "assistant_message") {
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: data.content,
                    needsInput: data.needsInput || false,
                    isFinal: data.isFinal || false,
                  },
                ]);
                setCurrentStreamingMessage("");
              } else if (data.type === "needs_input") {
                if (currentStreamingMessage) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: currentStreamingMessage,
                      needsInput: true,
                    },
                  ]);
                  setCurrentStreamingMessage("");
                } else {
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content:
                        data.content ||
                        "⚠️ Additional information is required.",
                      needsInput: true,
                    },
                  ]);
                }
                setAwaitingUserInput(true);
              } else if (data.type === "final_itinerary") {
                if (currentStreamingMessage) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: currentStreamingMessage,
                      isFinal: true,
                    },
                  ]);
                  setCurrentStreamingMessage("");
                }
                setAwaitingUserInput(false);
              } else if (data.type === "complete") {
                if (currentStreamingMessage) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: currentStreamingMessage,
                    },
                  ]);
                  setCurrentStreamingMessage("");
                }
                setAwaitingUserInput(false);
              } else if (data.type === "error") {
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: data.content,
                    isError: true,
                  },
                ]);
                setCurrentStreamingMessage("");
                setAwaitingUserInput(false);
              }
            } catch (err) {
              console.error("Error parsing SSE:", err);
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ I'm having trouble connecting to the server.",
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
      setProcessingSteps([]);
      setCurrentStreamingMessage("");
    }
  };

  const hasState = agentState.plan || agentState.adults || agentState.flight_data;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <Header 
        awaitingUserInput={awaitingUserInput}
        showDetails={showDetails}
        setShowDetails={setShowDetails}
      />

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className={`grid grid-cols-1 ${showDetails ? "lg:grid-cols-3" : ""} gap-6`}>
          
          {/* --- Main Chat Column --- */}
          <div className={showDetails ? "lg:col-span-2" : "w-full"}>
            
            {messages.length === 0 && (
              <QuickActions setInput={setInput} showDetails={showDetails} />
            )}

            <div className="bg-white rounded-2xl shadow-lg border border-purple-100 overflow-hidden flex flex-col h-[600px]">
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                
                {messages.length === 0 && !currentStreamingMessage ? (
                  <div className="h-full flex flex-col items-center justify-center text-center">
                    <div className="bg-gradient-to-br from-purple-100 to-pink-100 p-8 rounded-3xl mb-4">
                      <Plane className="w-16 h-16 text-purple-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">
                      Start Planning Your Adventure
                    </h3>
                    <p className="text-gray-600 max-w-md">
                      Tell me where you want to go, when you'd like to travel,
                      and what you're interested in.
                    </p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg, idx) => (
                      <Message key={idx} msg={msg} />
                    ))}

                    {currentStreamingMessage && (
                       <div className="flex justify-start">
                        <div className="max-w-[85%] rounded-2xl px-6 py-4 shadow-sm bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none">
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">
                            {currentStreamingMessage}
                          </p>
                          <span className="inline-block w-2 h-4 bg-purple-600 animate-pulse ml-1"></span>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {processingSteps.length > 0 && (
                  <ProcessingSteps steps={processingSteps} />
                )}
                
                <div ref={messagesEndRef} />
              </div>

              <ChatInput
                input={input}
                setInput={setInput}
                isLoading={isLoading}
                awaitingUserInput={awaitingUserInput}
                sessionId={sessionId}
                showOptionsMenu={showOptionsMenu}
                setShowOptionsMenu={setShowOptionsMenu}
                withReasoning={withReasoning}
                toolsEnabled={withTools}
                plannerMode={withPlanner}
                onSubmit={handleSubmit}
                onReasoningToggle={handleReasoningToggle}
                onToolsToggle={handleToolsToggle}
                onPlannerToggle={handlePlannerToggle}
                onReset={handleReset}
                onClear={clearConversation}
              />
            </div>
          </div>

          {/* --- Details Sidebar Column --- */}
          {showDetails && (
            <div className="lg:col-span-1">
              <TripDetailsSidebar
                agentState={agentState}
                isEditing={isEditing}
                editablePlan={editablePlan || {}}
                setEditablePlan={setEditablePlan}
                onEdit={handleEdit}
                onUpdatePlan={handleUpdatePlan}
                onCancelEdit={handleCancelEdit}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

