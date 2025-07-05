import React, { useState, useEffect } from 'react';

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [question, setQuestion] = useState('');
  const [description, setDescription] = useState('');
  const [attributes, setAttributes] = useState([]);
  const [answer, setAnswer] = useState('');
  const [query, setQuery] = useState('');
  const [queryResponse, setQueryResponse] = useState('');
  const [loading, setLoading] = useState(true);

  // Start a new audit session
  const startAudit = async () => {
    try {
      const res = await fetch('http://localhost:8000/audit/start', { method: 'POST' });
      const data = await res.json();
      setSessionId(data.session_id);
    } catch (err) {
      console.error('Failed to start audit:', err);
    }
  };

  // Fetch the next clause: question, description, attributes
  const fetchNextClause = async (id) => {
    setLoading(true);
    setQueryResponse('');
    try {
      const res = await fetch(`http://localhost:8000/audit/${id}/next`);
      const data = await res.json();
      setQuestion(data.question);
      setDescription(data.description || '');
      setAttributes(data.attributes || []);
    } catch (err) {
      console.error('Failed to fetch clause:', err);
    } finally {
      setLoading(false);
    }
  };


  

  // On mount, initialize session and load first clause
  useEffect(() => {
    startAudit();
  }, []);

  // When sessionId is set, load the first clause
  useEffect(() => {
    if (sessionId) {
      fetchNextClause(sessionId);
    }
  }, [sessionId]);

  // Ask a question about current clause
  const handleQuery = async () => {
    if (!sessionId || !query) return;
    try {
      const res = await fetch(`http://localhost:8000/audit/${sessionId}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setQueryResponse(data.response);
    } catch (err) {
      console.error('Failed to query agent:', err);
    }
  };

  // Submit answer and move to next clause
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!sessionId || !answer) return;
    try {
      await fetch(`http://localhost:8000/audit/${sessionId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer }),
      });
      setAnswer('');
      fetchNextClause(sessionId);
    } catch (err) {
      console.error('Failed to submit answer:', err);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="max-w-lg mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">ISO 27001 Internal Auditor</h1>

      {/* Clause description */}
      {description && (
        <div className="mb-4 p-3 bg-gray-100 rounded">
          <h2 className="font-semibold mb-2">Clause Description</h2>
          <p className="mb-2">{description}</p>
          {attributes.length > 0 && (
            <ul className="list-disc list-inside">
              {attributes.map((attr, idx) => (
                <li key={idx}>{attr}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* AI query section */}
      <div className="mb-4">
        <h2 className="font-semibold mb-2">Ask about this clause</h2>
        <div className="flex space-x-2 mb-2">
          <input
            type="text"
            className="flex-grow p-2 border rounded"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Your question..."
          />
          <button
            onClick={handleQuery}
            className="px-4 py-2 bg-green-600 text-white rounded"
          >
            Ask
          </button>
        </div>
        {queryResponse && (
          <div className="p-3 bg-gray-50 border rounded">
            <p>{queryResponse}</p>
          </div>
        )}
      </div>

      {/* Question and answer section */}
      <div className="mb-4">
        <h2 className="font-semibold mb-2">Audit Question</h2>
        <p className="mb-2">{question}</p>
      </div>

      <form onSubmit={handleSubmit} className="flex space-x-2">
        <input
          type="text"
          className="flex-grow p-2 border rounded"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Type your answer..."
          required
        />
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">
          Submit
        </button>
      </form>
    </div>
  );
}
