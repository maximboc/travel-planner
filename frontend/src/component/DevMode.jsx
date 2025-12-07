import React, { useState, useRef } from 'react';
import { 
  Upload, 
  Download, 
  History, 
  Play, 
  FileJson, 
  Trash2, 
  Clock,
  CheckCircle,
  AlertCircle,
  X,
  RefreshCw
} from 'lucide-react';

export function DevMode({ sessionId, onStateRestored, onClose }) {
  const [activeTab, setActiveTab] = useState('upload');
  const [checkpointHistory, setCheckpointHistory] = useState([]);
  const [savedCheckpoints, setSavedCheckpoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    loadCheckpointHistory();
    loadSavedCheckpoints();
  }, [sessionId]);

  const loadCheckpointHistory = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/checkpoint/history/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setCheckpointHistory(data.history || []);
      }
    } catch (error) {
      console.error('Failed to load checkpoint history:', error);
    }
  };

  const loadSavedCheckpoints = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/checkpoint/list');
      if (res.ok) {
        const data = await res.json();
        setSavedCheckpoints(data.checkpoints || []);
      }
    } catch (error) {
      console.error('Failed to load saved checkpoints:', error);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionId);
      formData.append('create_new_thread', 'false');

      const res = await fetch('http://127.0.0.1:8000/checkpoint/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Upload failed');

      const data = await res.json();
      setMessage({ type: 'success', text: 'Checkpoint uploaded successfully!' });
      
      if (data.state) {
        onStateRestored?.(data.state);
      }

      // Refresh history
      await loadCheckpointHistory();
    } catch (error) {
      setMessage({ type: 'error', text: `Upload failed: ${error.message}` });
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleExportCurrent = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/checkpoint/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          include_history: false,
        }),
      });

      if (!res.ok) throw new Error('Export failed');

      const data = await res.json();
      
      // Download the file
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `checkpoint_${sessionId}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setMessage({ type: 'success', text: 'Checkpoint exported successfully!' });
      await loadSavedCheckpoints();
    } catch (error) {
      setMessage({ type: 'error', text: `Export failed: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleExportHistory = async () => {
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/checkpoint/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          include_history: true,
        }),
      });

      if (!res.ok) throw new Error('Export failed');

      const data = await res.json();
      
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `history_${sessionId}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setMessage({ type: 'success', text: 'History exported successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: `Export failed: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleReplayCheckpoint = async (checkpointId) => {
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch('http://127.0.0.1:8000/checkpoint/replay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          checkpoint_id: checkpointId,
        }),
      });

      if (!res.ok) throw new Error('Replay failed');

      const data = await res.json();
      setMessage({ type: 'success', text: 'Checkpoint replayed successfully!' });
      
      if (data.state) {
        onStateRestored?.(data.state);
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Replay failed: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSaved = async (filename) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/checkpoint/download/${filename}`);
      if (!res.ok) throw new Error('Download failed');
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setMessage({ type: 'success', text: 'File downloaded!' });
    } catch (error) {
      setMessage({ type: 'error', text: `Download failed: ${error.message}` });
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Unknown';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="bg-purple-100 p-2 rounded-lg">
              <FileJson className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-800">Checkpoint Manager</h2>
              <p className="text-sm text-gray-500">Session: {sessionId.slice(0, 20)}...</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-6">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-3 font-medium transition-colors ${
              activeTab === 'upload'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Upload
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-3 font-medium transition-colors ${
              activeTab === 'history'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <History className="w-4 h-4 inline mr-2" />
            History ({checkpointHistory.length})
          </button>
          <button
            onClick={() => setActiveTab('saved')}
            className={`px-4 py-3 font-medium transition-colors ${
              activeTab === 'saved'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Download className="w-4 h-4 inline mr-2" />
            Saved ({savedCheckpoints.length})
          </button>
        </div>

        {/* Message Banner */}
        {message && (
          <div className={`mx-6 mt-4 p-3 rounded-lg flex items-center gap-2 ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            <span className="text-sm font-medium">{message.text}</span>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'upload' && (
            <div className="space-y-6">
              {/* Upload Section */}
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-purple-400 transition-colors">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center gap-3"
                >
                  <div className="bg-purple-100 p-4 rounded-full">
                    <Upload className="w-8 h-8 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-gray-800">
                      Upload Checkpoint JSON
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      Click to browse or drag and drop
                    </p>
                  </div>
                </label>
              </div>

              {/* Export Buttons */}
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={handleExportCurrent}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                >
                  <Download className="w-5 h-5" />
                  Export Current State
                </button>
                <button
                  onClick={handleExportHistory}
                  disabled={loading}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                >
                  <History className="w-5 h-5" />
                  Export Full History
                </button>
              </div>

              {/* Info Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                <h3 className="font-semibold text-blue-900 mb-2">How it works</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Upload a checkpoint JSON to restore conversation state</li>
                  <li>• Export current state to save progress</li>
                  <li>• Export full history to backup entire conversation</li>
                  <li>• Use saved checkpoints for debugging or sharing</li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-3">
              {checkpointHistory.length === 0 ? (
                <div className="text-center py-12">
                  <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No checkpoint history available</p>
                </div>
              ) : (
                checkpointHistory.map((checkpoint, idx) => (
                  <div
                    key={checkpoint.checkpoint_id || idx}
                    className="border border-gray-200 rounded-xl p-4 hover:border-purple-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            {checkpoint.checkpoint_id?.slice(0, 12)}...
                          </span>
                          {checkpoint.next?.length > 0 && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              Next: {checkpoint.next.join(', ')}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500">
                          {formatDate(checkpoint.created_at)}
                        </p>
                        {checkpoint.metadata?.step !== undefined && (
                          <p className="text-xs text-gray-400 mt-1">
                            Step: {checkpoint.metadata.step}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => handleReplayCheckpoint(checkpoint.checkpoint_id)}
                        disabled={loading}
                        className="flex items-center gap-1 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-200 transition-colors disabled:opacity-50"
                      >
                        <Play className="w-4 h-4" />
                        Replay
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'saved' && (
            <div className="space-y-3">
              <div className="flex justify-end mb-4">
                <button
                  onClick={loadSavedCheckpoints}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
              </div>
              {savedCheckpoints.length === 0 ? (
                <div className="text-center py-12">
                  <FileJson className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No saved checkpoints</p>
                </div>
              ) : (
                savedCheckpoints.map((checkpoint, idx) => (
                  <div
                    key={idx}
                    className="border border-gray-200 rounded-xl p-4 hover:border-purple-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-gray-800">{checkpoint.filename}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Thread: {checkpoint.thread_id}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(checkpoint.exported_at)}
                        </p>
                        {checkpoint.is_history && (
                          <span className="inline-block mt-2 text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                            Full History
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleDownloadSaved(checkpoint.filename)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {loading && (
          <div className="border-t border-gray-200 px-6 py-4">
            <div className="flex items-center justify-center gap-2 text-purple-600">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span className="text-sm font-medium">Processing...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
