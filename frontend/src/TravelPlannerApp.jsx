import React, { useState } from 'react';
import { Send, Plane, Calendar, DollarSign, MapPin, Hotel, Compass, Sun, TrendingUp, AlertCircle } from 'lucide-react';

export default function TravelPlannerApp() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // Generate a persistent ID for the session
  const [sessionId] = useState(`session_${Date.now()}`); 
  const [tripStats, setTripStats] = useState({ budget: 0, destination: '---', dates: '---' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // --- REAL BACKEND INTEGRATION ---
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId
        }),
      });

      if (!res.ok) throw new Error('Failed to connect to agent');

      const data = await res.json();
      
      const botResponse = {
        role: 'assistant',
        content: data.content
      };

      setMessages(prev => [...prev, botResponse]);
      
      // Update UI stats from backend data
      if (data.stats) {
        setTripStats({
          budget: data.stats.budget || 0,
          destination: data.stats.destination || '---',
          dates: data.stats.dates || '---'
        });
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "⚠️ I'm having trouble connecting to the server. Is the Python backend running?" 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    { icon: Plane, text: 'Find Flights', color: 'from-blue-500 to-cyan-500' },
    { icon: Hotel, text: 'Book Hotels', color: 'from-purple-500 to-pink-500' },
    { icon: Compass, text: 'Activities', color: 'from-orange-500 to-red-500' },
    { icon: Sun, text: 'Weather', color: 'from-yellow-500 to-orange-500' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-purple-100 sticky top-0 z-50 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4">
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
            <div className="flex gap-2">
              <div className="px-4 py-2 rounded-lg bg-white border border-purple-200 text-sm font-medium text-purple-700 flex items-center gap-2">
                 <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                 Online
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        
        {/* Dynamic Stats Bar (Updates from Backend) */}
        {messages.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-white p-4 rounded-xl border border-blue-100 flex items-center gap-3 shadow-sm">
                    <MapPin className="w-8 h-8 text-blue-500 bg-blue-50 p-1.5 rounded-lg"/>
                    <div>
                        <p className="text-xs text-gray-500 uppercase font-semibold">Destination</p>
                        <p className="font-bold text-gray-800 truncate">{tripStats.destination}</p>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-purple-100 flex items-center gap-3 shadow-sm">
                    <Calendar className="w-8 h-8 text-purple-500 bg-purple-50 p-1.5 rounded-lg"/>
                    <div>
                        <p className="text-xs text-gray-500 uppercase font-semibold">Dates</p>
                        <p className="font-bold text-gray-800 truncate">{tripStats.dates}</p>
                    </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-pink-100 flex items-center gap-3 shadow-sm">
                    <DollarSign className="w-8 h-8 text-pink-500 bg-pink-50 p-1.5 rounded-lg"/>
                    <div>
                        <p className="text-xs text-gray-500 uppercase font-semibold">Budget</p>
                        <p className="font-bold text-gray-800">${tripStats.budget}</p>
                    </div>
                </div>
            </div>
        )}

        {/* Quick Actions (Only show when chat is empty) */}
        {messages.length === 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

        {/* Chat Messages */}
        <div className="bg-white rounded-2xl shadow-lg border border-purple-100 overflow-hidden mb-6 flex flex-col h-[550px]">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <div className="bg-gradient-to-br from-purple-100 to-pink-100 p-8 rounded-3xl mb-4 animate-bounce-slow">
                  <Plane className="w-16 h-16 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Start Planning Your Adventure</h3>
                <p className="text-gray-600 max-w-md">
                  Tell me where you want to go, when you'd like to travel, and what you're interested in.
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-6 py-4 shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-tr-none'
                        : 'bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-none'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-50 rounded-2xl px-6 py-4 border border-gray-100 rounded-tl-none">
                  <div className="flex gap-2 items-center">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    <span className="text-xs text-gray-400 ml-2">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-purple-100 p-4 bg-gray-50/50">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ex: I want to go to Tokyo next week for $3000..."
                className="flex-1 px-6 py-4 rounded-xl border border-purple-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-100 focus:outline-none bg-white shadow-sm transition-all placeholder:text-gray-400"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-300 disabled:to-gray-400 text-white rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
                <span className="hidden sm:inline">Send</span>
              </button>
            </form>
            <p className="text-xs text-center text-gray-400 mt-2">
                Session ID: <span className="font-mono">{sessionId.slice(-6)}</span> • Powered by Amadeus & LangGraph
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
