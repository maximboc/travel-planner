import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, RotateCcw, Plane, Calendar, DollarSign, MapPin, 
  Hotel, Compass, Sun, Users, CheckCircle2, Loader2, 
  PanelRight, PanelRightClose, AlertCircle, CheckCircle, XCircle, Edit3, Plus
} from 'lucide-react';
export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(`session_${Date.now()}`);
  const [showDetails, setShowDetails] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');
  const [awaitingUserInput, setAwaitingUserInput] = useState(false);
  const [withReasoning, setWithReasoning] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editablePlan, setEditablePlan] = useState(null);
  const [showOptionsMenu, setShowOptionsMenu] = useState(false);
  
  const [agentState, setAgentState] = useState({
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
    current_node: null
  });
  
  const [processingSteps, setProcessingSteps] = useState([]);
  const messagesEndRef = useRef(null);

  const handleReasoningToggle = async (enabled) => {
    setWithReasoning(enabled);
    try {
      await fetch('http://127.0.0.1:8000/chat/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          with_reasoning: enabled,
        }),
      });
    } catch (error) {
      console.error('Failed to configure reasoning:', error);
    }
  };

  const handleEdit = () => {
    setEditablePlan({ ...agentState.plan });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditablePlan(null);
  };

  const handleUpdatePlan = async () => {
    if (!editablePlan) return;

    try {
      const res = await fetch('http://127.0.0.1:8000/chat/update_plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          ...editablePlan,
        }),
      });

      if (!res.ok) throw new Error('Failed to update plan');

      const data = await res.json();
      setAgentState(prev => ({ ...prev, ...data.state }));
      setIsEditing(false);
      setEditablePlan(null);
    } catch (error) {
      console.error('Failed to update plan:', error);
    }
  };

  const resetAll = () => {
    setMessages([]);
    setInput('');
    setProcessingSteps([]);
    setCurrentStreamingMessage('');
    setAwaitingUserInput(false);
    setAgentState({
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
      current_node: null
    });
    const newId = `session_${Date.now()}`;
    setSessionId(newId);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, processingSteps, currentStreamingMessage]);

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setProcessingSteps([]);
    setCurrentStreamingMessage('');
    setAwaitingUserInput(false);

    try {
      const res = await fetch('http://127.0.0.1:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId
        }),
      });

      if (!res.ok) throw new Error('Failed to connect to agent');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              console.log('SSE Data:', data);

              if (data.type === 'node_start') {
                setProcessingSteps(prev => [...prev, {
                  node: data.node,
                  status: 'processing',
                  timestamp: Date.now()
                }]);
                
              } else if (data.type === 'node_end') {
                setProcessingSteps(prev => prev.map(step => 
                  step.node === data.node && step.status === 'processing'
                    ? { ...step, status: 'completed' }
                    : step
                ));
                
              } else if (data.type === 'state_update') {
                setAgentState(prev => ({ ...prev, ...data.state }));
                
              } else if (data.type === 'token') {
                setCurrentStreamingMessage(prev => prev + data.content);
                
              } else if (data.type === 'assistant_message') {
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: data.content,
                  needsInput: data.needsInput || false,
                  isFinal: data.isFinal || false
                }]);
                setCurrentStreamingMessage('');
                
              } else if (data.type === 'needs_input') {
                if (currentStreamingMessage) {
                  setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: currentStreamingMessage,
                    needsInput: true
                  }]);
                  setCurrentStreamingMessage('');
                } else {
                  setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.content || "⚠️ Additional information is required.",
                    needsInput: true
                  }]);
                  setCurrentStreamingMessage('');
                }
                setAwaitingUserInput(true);
                
              } else if (data.type === 'final_itinerary') {
                if (currentStreamingMessage) {
                  setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: currentStreamingMessage,
                    isFinal: true
                  }]);
                  setCurrentStreamingMessage('');
                }
                setAwaitingUserInput(false);
                
              } else if (data.type === 'complete') {
                if (currentStreamingMessage) {
                  setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: currentStreamingMessage
                  }]);
                  setCurrentStreamingMessage('');
                }
                setAwaitingUserInput(false);
                
              } else if (data.type === 'error') {
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: data.content,
                  isError: true
                }]);
                setCurrentStreamingMessage('');
                setAwaitingUserInput(false);
              }
            } catch (err) {
              console.error('Error parsing SSE:', err);
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, {
        role: 'assistant', 
        content: "⚠️ I'm having trouble connecting to the server. Is the Python backend running?",
        isError: true
      }]);
    } finally {
      setIsLoading(false);
      setProcessingSteps([]);
      setCurrentStreamingMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const nodeDisplayNames = {
    planner: 'Planning Trip',
    city_resolver: 'Resolving Cities',
    passenger_agent: 'Processing Passengers',
    flight_agent: 'Searching Flights',
    hotel_agent: 'Finding Hotels',
    activity_agent: 'Discovering Activities',
    compiler: 'Compiling Itinerary',
    reviewer: 'Reviewing Plan'
  };

  const quickActions = [
    { icon: Plane, text: 'Find Flights', color: 'from-blue-500 to-cyan-500' },
    { icon: Hotel, text: 'Book Hotels', color: 'from-purple-500 to-pink-500' },
    { icon: Compass, text: 'Activities', color: 'from-orange-500 to-red-500' },
    { icon: Sun, text: 'Weather', color: 'from-yellow-500 to-orange-500' },
  ];

  const plan = agentState.plan;
  const hasState = plan || agentState.adults || agentState.flight_data;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <header className="bg-white/80 backdrop-blur-md border-b border-purple-100 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-2 rounded-xl">
                <Plane className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Travel Planner AI
                </h1>
                <p className="text-sm text-gray-600">Your intelligent travel companion</p>
              </div>
            </div>
            
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
              
              <button 
                onClick={() => setShowDetails(!showDetails)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${showDetails ? 'bg-purple-100 text-purple-700 border border-purple-200' : 'bg-white text-gray-600 border border-gray-200 hover:border-purple-300'}`}
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
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className={`grid grid-cols-1 ${showDetails ? 'lg:grid-cols-3' : ''} gap-6`}>
          
          <div className={showDetails ? 'lg:col-span-2' : 'w-full'}>
            {messages.length === 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h2>
                <div className={`grid gap-4 ${showDetails ? 'grid-cols-2' : 'grid-cols-2 md:grid-cols-4'}`}>
                  {quickActions.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInput(`Help me ${action.text.toLowerCase()}`)}
                      className="group relative overflow-hidden bg-white p-6 rounded-2xl border border-gray-200 hover:border-transparent hover:shadow-xl transition-all duration-300 text-left"
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-0 group-hover:opacity-10 transition-opacity`} />
                      <div className={`bg-gradient-to-br ${action.color} w-12 h-12 rounded-xl flex items-center justify-center mb-3`}>
                        <action.icon className="w-6 h-6 text-white" />
                      </div>
                      <p className="font-semibold text-gray-800 text-sm">{action.text}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl shadow-lg border border-purple-100 overflow-hidden flex flex-col h-[600px]">
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 && !currentStreamingMessage ? (
                  <div className="h-full flex flex-col items-center justify-center text-center">
                    <div className="bg-gradient-to-br from-purple-100 to-pink-100 p-8 rounded-3xl mb-4">
                      <Plane className="w-16 h-16 text-purple-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-800 mb-2">Start Planning Your Adventure</h3>
                    <p className="text-gray-600 max-w-md">
                      Tell me where you want to go, when you'd like to travel, and what you're interested in.
                    </p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-6 py-4 shadow-sm ${msg.role === 'user' ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-tr-none' : msg.isFinal ? 'bg-gradient-to-r from-green-50 to-emerald-50 text-gray-800 border-2 border-green-200 rounded-tl-none' : msg.isError ? 'bg-red-50 text-red-800 border border-red-200 rounded-tl-none' : msg.needsInput ? 'bg-blue-50 text-gray-800 border-2 border-blue-300 rounded-tl-none' : 'bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none'}`}
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
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    ))}

                    {currentStreamingMessage && (
                      <div className="flex justify-start">
                        <div className="max-w-[85%] rounded-2xl px-6 py-4 shadow-sm bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none">
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{currentStreamingMessage}</p>
                          <span className="inline-block w-2 h-4 bg-purple-600 animate-pulse ml-1"></span>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {processingSteps.length > 0 && (
                  <div className="flex justify-start">
                    <div className="bg-blue-50 border border-blue-200 rounded-2xl px-6 py-4 max-w-[85%]">
                      <div className="flex items-center gap-2 mb-3">
                        <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                        <span className="text-sm font-semibold text-blue-900">Processing...</span>
                      </div>
                      <div className="space-y-2">
                        {processingSteps.map((step, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm">
                            {step.status === 'completed' ? (
                              <CheckCircle2 className="w-4 h-4 text-green-500" />
                            ) : (
                              <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                            )}
                            <span className={step.status === 'completed' ? 'text-gray-600' : 'text-blue-900 font-medium'}>
                              {nodeDisplayNames[step.node] || step.node}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="border-t border-purple-100 p-4 bg-gray-50/50 relative">
                
                {showOptionsMenu && (
                  <div className="absolute bottom-full left-0 right-0 p-4 bg-white border-t border-x border-purple-100 rounded-t-xl shadow-2xl animate-in slide-in-from-bottom-5 duration-300">
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-semibold text-gray-700 mb-2 block">Agent Reasoning</label>
                        <div className="flex rounded-lg border border-gray-200 p-1">
                          <button
                            onClick={() => handleReasoningToggle(true)}
                            className={`flex-1 flex items-center justify-center gap-2 text-sm px-3 py-1.5 rounded-md transition-all ${
                              withReasoning ? 'bg-purple-600 text-white shadow' : 'bg-transparent text-gray-600 hover:bg-gray-100'
                            }`}
                          >
                            <CheckCircle className="w-4 h-4" />
                            Enabled
                          </button>
                          <button
                            onClick={() => handleReasoningToggle(false)}
                            className={`flex-1 flex items-center justify-center gap-2 text-sm px-3 py-1.5 rounded-md transition-all ${
                              !withReasoning ? 'bg-red-600 text-white shadow' : 'bg-transparent text-gray-600 hover:bg-gray-100'
                            }`}
                          >
                            <XCircle className="w-4 h-4" />
                            Disabled
                          </button>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-semibold text-gray-700 mb-2 block">Session</label>
                        <button
                          onClick={resetAll}
                          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm bg-red-500 hover:bg-red-600 text-white rounded-lg"
                          title="Reset conversation"
                        >
                          <RotateCcw className="w-4 h-4" />
                          Reset Conversation
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowOptionsMenu(!showOptionsMenu)}
                    className={`p-4 border rounded-xl transition-all ${showOptionsMenu ? 'bg-purple-100 border-purple-300 text-purple-600' : 'bg-white border-purple-200 text-gray-500 hover:border-purple-400'}`}
                    title="Options"
                  >
                    <Plus className={`w-5 h-5 transition-transform ${showOptionsMenu ? 'rotate-45' : ''}`} />
                  </button>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={awaitingUserInput ? "Please provide the requested information..." : "Ex: I want to go to Tokyo next week for $3000..."}
                    className="flex-1 px-6 py-4 rounded-xl border border-purple-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 focus:outline-none bg-white shadow-sm transition-all placeholder:text-gray-400"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={isLoading || !input.trim()}
                    className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-400 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Send className="w-5 h-5" />
                    <span className="hidden sm:inline">Send</span>
                  </button>
                </div>
                <p className="text-xs text-center text-gray-400 mt-2">
                  Session: <span className="font-mono">{sessionId.slice(-6)}</span> • Powered by Amadeus & LangGraph
                </p>
              </div>
            </div>
          </div>

          {showDetails && (
            <div className="lg:col-span-1">
              <div className="bg-white rounded-2xl shadow-lg border border-purple-100 p-6 sticky top-24 animate-in slide-in-from-right-10 duration-300">
                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                                      <MapPin className="w-5 h-5 text-purple-600" />
                                      Trip Details
                                    </h2>
                                                      {plan && !isEditing && (
                                                        <button onClick={handleEdit} className="text-purple-600 hover:text-purple-800">
                                                          <Edit3 className="w-4 h-4" />
                                                        </button>
                                                      )}
                                                    </div>
                                    
                                                    {!hasState ? (                                    <p className="text-sm text-gray-500 italic">Details will appear as you chat...</p>
                                  ) : (
                                    <div className="space-y-4">
                                      {isEditing ? (
                                        <div className="space-y-4">
                                          <div>
                                            <label className="text-xs font-semibold text-gray-600">Destination</label>
                                            <input
                                              type="text"
                                              value={editablePlan.destination || ''}
                                              onChange={(e) => setEditablePlan({...editablePlan, destination: e.target.value})}
                                              className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                                            />
                                          </div>
                                          <div>
                                            <label className="text-xs font-semibold text-gray-600">Departure Date</label>
                                            <input
                                              type="text"
                                              value={editablePlan.departure_date || ''}
                                              onChange={(e) => setEditablePlan({...editablePlan, departure_date: e.target.value})}
                                              className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                                            />
                                          </div>
                                          <div>
                                            <label className="text-xs font-semibold text-gray-600">Arrival Date</label>
                                            <input
                                              type="text"
                                              value={editablePlan.arrival_date || ''}
                                              onChange={(e) => setEditablePlan({...editablePlan, arrival_date: e.target.value})}
                                              className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                                            />
                                          </div>
                                          <div>
                                            <label className="text-xs font-semibold text-gray-600">Budget</label>
                                            <input
                                              type="number"
                                              value={editablePlan.budget || ''}
                                              onChange={(e) => setEditablePlan({...editablePlan, budget: parseFloat(e.target.value)})}
                                              className="w-full mt-1 p-2 border border-gray-300 rounded-lg"
                                            />
                                          </div>
                                          <div className="flex gap-2">
                                            <button onClick={handleUpdatePlan} className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg">Save</button>
                                            <button onClick={handleCancelEdit} className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg">Cancel</button>
                                          </div>
                                        </div>
                                      ) : (
                                        <>
                                          {plan && (
                                            <>
                                              <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                                                <div className="flex items-center gap-2 mb-2">
                                                  <MapPin className="w-5 h-5 text-blue-600" />
                                                  <span className="text-xs font-semibold text-blue-900 uppercase">Destination</span>
                                                </div>
                                                <p className="font-bold text-gray-800">{plan.destination || '---'}</p>
                                                {agentState.city_code && (
                                                  <p className="text-xs text-gray-600 mt-1">Code: {agentState.city_code}</p>
                                                )}
                                              </div>
                  
                                              <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                                                <div className="flex items-center gap-2 mb-2">
                                                  <Calendar className="w-5 h-5 text-purple-600" />
                                                  <span className="text-xs font-semibold text-purple-900 uppercase">Dates</span>
                                                </div>
                                                <p className="text-sm font-medium text-gray-800">
                                                  {plan.departure_date ? `${plan.departure_date}` : '---'}
                                                </p>
                                                {plan.arrival_date && (
                                                  <p className="text-sm font-medium text-gray-800 mt-1">to {plan.arrival_date}</p>
                                                )}
                                              </div>
                  
                                              <div className="bg-pink-50 p-4 rounded-xl border border-pink-100">
                                                <div className="flex items-center gap-2 mb-2">
                                                  <DollarSign className="w-5 h-5 text-pink-600" />
                                                  <span className="text-xs font-semibold text-pink-900 uppercase">Budget</span>
                                                </div>
                                                <p className="font-bold text-gray-800">${plan.budget || 0}</p>
                                              </div>
                                            </>
                                          )}
                                        </>
                                      )}
                  
                    {(agentState.adults > 0 || agentState.children > 0 || agentState.infants > 0) && !isEditing && (
                      <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
                        <div className="flex items-center gap-2 mb-2">
                          <Users className="w-5 h-5 text-orange-600" />
                          <span className="text-xs font-semibold text-orange-900 uppercase">Passengers</span>
                        </div>
                        <div className="space-y-1 text-sm text-gray-700">
                          {agentState.adults > 0 && <p>Adults: {agentState.adults}</p>}
                          {agentState.children > 0 && <p>Children: {agentState.children}</p>}
                          {agentState.infants > 0 && <p>Infants: {agentState.infants}</p>}
                          {agentState.travel_class && (
                            <p className="text-xs text-gray-600 mt-2">Class: {agentState.travel_class}</p>
                          )}
                        </div>
                      </div>
                    )}

                    {agentState.flight_data && agentState.flight_data.length > 0 && !isEditing && (
                      <div className="bg-cyan-50 p-4 rounded-xl border border-cyan-100">
                        <div className="flex items-center gap-2 mb-2">
                          <Plane className="w-5 h-5 text-cyan-600" />
                          <span className="text-xs font-semibold text-cyan-900 uppercase">Flights Found</span>
                        </div>
                        <div className="space-y-2">
                          {agentState.flight_data.map((f, i) => (
                            <div key={i} className="text-sm p-2 bg-white/50 rounded-lg">
                              <p className="font-bold">{f.price} {f.currency}</p>
                              <p className="text-xs">Depart: {new Date(f.departure_time).toLocaleString()}</p>
                              <p className="text-xs">Arrive: {new Date(f.arrival_time).toLocaleString()}</p>
                            </div>
                          ))}
                        </div>
                        {agentState.selected_flight_index !== null && (
                          <p className="text-xs text-gray-600 mt-1">Selected: Option {agentState.selected_flight_index + 1}</p>
                        )}
                      </div>
                    )}

                    {agentState.hotel_data && agentState.hotel_data.hotels && agentState.hotel_data.hotels.length > 0 && !isEditing && (
                      <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100">
                        <div className="flex items-center gap-2 mb-2">
                          <Hotel className="w-5 h-5 text-emerald-600" />
                          <span className="text-xs font-semibold text-emerald-900 uppercase">Hotels Found</span>
                        </div>
                        <p className="font-bold text-gray-800">{agentState.hotel_data.hotels.length} options</p>
                        {agentState.selected_hotel_index !== null && (
                          <p className="text-xs text-gray-600 mt-1">Selected: Option {agentState.selected_hotel_index + 1}</p>
                        )}
                      </div>
                    )}

                    {agentState.activity_data && agentState.activity_data.length > 0 && (
                      <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-100">
                        <div className="flex items-center gap-2 mb-2">
                          <Compass className="w-5 h-5 text-yellow-600" />
                          <span className="text-xs font-semibold text-yellow-900 uppercase">Activities</span>
                        </div>
                        <p className="font-bold text-gray-800">{agentState.activity_data.length} found</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}