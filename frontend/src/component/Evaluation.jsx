import React, { useState, useEffect, useRef } from "react";
import {
  Scale,
  Milestone,
  CheckCircle,
  XCircle,
  Play,
  Loader,
  Terminal,
} from "lucide-react";

// Helper to determine the color for scores
const getScoreColor = (score) => {
  if (score >= 8) return "text-green-700";
  if (score >= 5) return "text-yellow-600";
  return "text-red-600";
};

// A single row in the evaluation table

const EvaluationRow = ({ item, index, prompts }) => {

  const [isExpanded, setIsExpanded] = useState(false);

  const user_prompt = prompts.length > 0 ? prompts[index % prompts.length]?.user_prompt : '';



  return (

    <tbody

      className={`transition-all duration-300 ${

        index % 2 === 0 ? "bg-white" : "bg-gray-50/50"

      }`}

    >

      <tr

        className="cursor-pointer hover:bg-purple-50"

        onClick={() => setIsExpanded(!isExpanded)}

      >

        <td className="p-4 text-xs text-gray-500">{index + 1}</td>

        <td className="p-4 text-sm font-medium text-gray-800 max-w-sm truncate">

          {user_prompt}

        </td>

        <td className="p-4 text-center">

          <span

            className={`font-bold text-lg ${getScoreColor(item.relevance)}`}

          >

            {item.relevance}

          </span>

        </td>

        <td className="p-4 text-center">

          <span

            className={`font-bold text-lg ${getScoreColor(item.helpfulness)}`}

          >

            {item.helpfulness}

          </span>

        </td>

        <td className="p-4 text-center">

          <span className={`font-bold text-lg ${getScoreColor(item.logic)}`}>

            {item.logic}

          </span>

        </td>

        <td className="p-4 text-sm text-gray-600 max-w-lg truncate">

          {item.analysis}

        </td>

      </tr>

      {isExpanded && (

        <tr className="bg-purple-50">

          <td colSpan="6" className="p-6">

            <div className="space-y-4">

              <div>

                <h4 className="font-bold text-gray-700">User Prompt</h4>

                <p className="text-sm text-gray-600 mt-1">

                  {user_prompt}

                </p>

              </div>

              <div>

                <h4 className="font-bold text-gray-700">Agent Response</h4>

                <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">

                  {item.agent_response}

                </p>

              </div>

              <div>

                <h4 className="font-bold text-gray-700">Judge's Analysis</h4>

                <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">

                  {item.analysis}

                </p>

              </div>

              {item.conditions && (

                <div>

                  <h4 className="font-bold text-gray-700">

                    Acceptance Conditions

                  </h4>

                  <p className="text-sm text-gray-600 mt-1">

                    {item.conditions}

                  </p>

                </div>

              )}

            </div>

          </td>

        </tr>

      )}

    </tbody>

  );

};

// The main component for the evaluation page
export const Evaluation = () => {
  const [results, setResults] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [usePlanner, setUsePlanner] = useState(true);
  const [useTools, setUseTools] = useState(true);
  const [useReasoning, setUseReasoning] = useState(true);
  const logContainerRef = useRef(null);

  const fetchPrompts = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/get_prompts");
      if (!res.ok) {
        throw new Error(`Failed to fetch prompts: ${res.statusText}`);
      }
      const data = await res.json();
      setPrompts(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchEvaluationResults = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:8000/get_evaluation_results");
      if (!res.ok) {
        if (res.status === 404) {
          setResults([]);
          setError(null);
        } else {
          throw new Error(`Failed to fetch: ${res.statusText}`);
        }
      }
      else {
        const data = await res.json();
        setResults(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluationResults();
    fetchPrompts();
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const handleRunEvaluation = () => {
    setIsRunning(true);
    setLogs([]);
    setError(null);

    const params = new URLSearchParams({
      use_planner: usePlanner,
      use_tools: useTools,
      use_reasoning: useReasoning,
    });

    const eventSource = new EventSource(
      `http://127.0.0.1:8000/run_evaluation_stream?${params.toString()}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'start' || data.type === 'end' || data.type === 'error') {
        setLogs((prev) => [...prev, { type: data.type, text: data.message }]);
      } else if (data.type === 'stdout' || data.type === 'stderr') {
        setLogs((prev) => [...prev, { type: data.type, text: data.line }]);
      }

      if (data.type === "end" || data.type === "error") {
        eventSource.close();
        setIsRunning(false);
        if (data.type === "end") {
          fetchEvaluationResults();
        }
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setLogs((prev) => [...prev, { type: 'error', text: "Connection to server failed." }]);
      setError("Failed to connect to the evaluation service.");
      setIsRunning(false);
      eventSource.close();
    };
  };

  return (
    <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
      <div className="p-6 border-b border-purple-100 flex justify-between items-center bg-gray-50">
        <div className="flex items-center gap-3">
          <Scale className="w-8 h-8 text-purple-600" />
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              Judge Evaluation
            </h2>
            <p className="text-sm text-gray-600">
              Run and review agent performance.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center">
                      <input type="checkbox" id="usePlanner" checked={usePlanner} onChange={() => setUsePlanner(!usePlanner)} className="h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mr-2" />
                      <label htmlFor="usePlanner" className="ml-2 block text-sm text-gray-900 cursor-pointer">Planner</label>
                    </div>
                    <div className="flex items-center">
                      <input type="checkbox" id="useTools" checked={useTools} onChange={() => setUseTools(!useTools)} className="h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mr-2" />
                      <label htmlFor="useTools" className="ml-2 block text-sm text-gray-900 cursor-pointer">Tools</label>
                    </div>
                    <div className="flex items-center">
                      <input type="checkbox" id="useReasoning" checked={useReasoning} onChange={() => setUseReasoning(!useReasoning)} className="h-4 w-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mr-2" />
                      <label htmlFor="useReasoning" className="ml-2 block text-sm text-gray-900 cursor-pointer">Reasoning</label>
                    </div>
          <button
            onClick={handleRunEvaluation}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 disabled:bg-gray-400 transition-all"
          >
            {isRunning ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Evaluation
              </>
            )}
          </button>
        </div>
      </div>

      {isRunning || logs.length > 0 ? (
        <div
          ref={logContainerRef}
          className="h-64 bg-gray-900 text-white font-mono text-xs p-4 overflow-y-auto rounded-lg"
        >
          {logs.map((log, i) => (
            <p key={i} className={log.type === 'stderr' || log.type === 'error' ? 'text-red-300' : 'text-gray-200'}>
              {`> ${log.text}`}
            </p>
          ))}
        </div>
      ) : null}

      {loading && (
        <div className="flex justify-center items-center h-64">
          <Milestone className="w-12 h-12 text-purple-500 animate-spin" />
        </div>
      )}

      {error && !isRunning && (
        <div className="text-center p-8 bg-red-50 text-red-700 rounded-lg m-4">
          <XCircle className="w-12 h-12 mx-auto mb-4" />
          <h3 className="text-xl font-bold">Error</h3>
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && results.length === 0 && !isRunning && (
        <div className="text-center p-8 bg-yellow-50 text-yellow-800 rounded-lg m-4">
          <CheckCircle className="w-12 h-12 mx-auto mb-4" />
          <h3 className="text-xl font-bold">No Results</h3>
          <p>
            Click "Run" to generate the results.
          </p>
        </div>
      )}
      
      {!loading && results.length > 0 && (
        <div className="overflow-x-auto rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-purple-100">
                          <tr>
                            <th className="p-4 text-left text-xs font-semibold text-purple-800 uppercase tracking-wider w-12">#</th>
                            <th className="p-4 text-left text-xs font-semibold text-purple-800 uppercase tracking-wider">User Prompt</th>
                            <th className="p-4 text-xs font-semibold text-purple-800 uppercase tracking-wider">Relevance</th>
                            <th className="p-4 text-xs font-semibold text-purple-800 uppercase tracking-wider">Helpfulness</th>
                            <th className="p-4 text-xs font-semibold text-purple-800 uppercase tracking-wider">Logic</th>
                            <th className="p-4 text-left text-xs font-semibold text-purple-800 uppercase tracking-wider">Analysis</th>
                          </tr>
                        </thead>
            {results.map((item, index) => (
              <EvaluationRow key={item.id || index} item={item} index={index} prompts={prompts} />
            ))}
          </table>
        </div>
      )}
    </div>
  );
};
