import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Search, Loader2, ChevronDown, ChevronUp, Database, FileText, Activity, TrendingUp, BarChart3, Sparkles } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [response, setResponse] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const [expandedSections, setExpandedSections] = useState({
    findings: true,
    visualization: true,
    sources: false,
    queries: false,
    data: false,
    logs: false
  });

  useEffect(() => {
    fetchMetadata();
    fetchSampleQuestions();
  }, []);

  const fetchMetadata = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/metadata`);
      const data = await res.json();
      setMetadata(data);
    } catch (error) {
      console.error('Failed to fetch metadata:', error);
    }
  };

  const fetchSampleQuestions = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/sample-questions`);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      console.log('Sample questions fetched:', data);
      setSampleQuestions(data.questions || []);
    } catch (error) {
      console.error('Failed to fetch sample questions:', error);
      // Fallback to hardcoded questions if API fails
      setSampleQuestions([
        { label: "Compare States", question: "Compare rice production in Assam and Odisha over last 5 years" },
        { label: "Find Maximum", question: "Which state had highest wheat production in 2014?" },
        { label: "Trend Analysis", question: "Analyze wheat production trend in Assam for last 10 years" },
        { label: "Correlation", question: "How does annual rainfall correlate with rice production in Odisha?" },
        { label: "Policy Insight", question: "Which crops have the highest yield in Assam?" }
      ]);
    }
  };

  const generateNewQuestions = async () => {
    setLoadingQuestions(true);
    try {
      const res = await fetch(`${API_BASE_URL}/generate-sample-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      
      const data = await res.json();
      console.log('New questions generated:', data);
      setSampleQuestions(data.questions || []);
    } catch (error) {
      console.error('Failed to generate new questions:', error);
      alert('Failed to generate new questions. Please try again.');
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleQuestionClick = async (questionText) => {
    setQuestion(questionText);
    // Generate new questions after clicking
    await generateNewQuestions();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setResponse(null);

    try {
      const res = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });

      if (!res.ok) throw new Error('Query failed');
      
      const data = await res.json();
      setResponse(data);
      setExpandedSections({
        findings: true,
        visualization: true,
        sources: false,
        queries: false,
        data: false,
        logs: false
      });
    } catch (error) {
      console.error('Query error:', error);
      alert('Failed to process query. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const renderVisualization = () => {
    if (!response?.visualization || !response?.results?.length) return null;

    const viz = response.visualization;
    const resultIdx = viz.result_index || 0;
    const data = response.results[resultIdx]?.data || [];

    if (!data.length) return null;

    const ChartComponent = {
      bar: BarChart,
      line: LineChart,
      scatter: ScatterChart
    }[viz.type];

    const DataComponent = {
      bar: Bar,
      line: Line,
      scatter: Scatter
    }[viz.type];

    if (!ChartComponent || !DataComponent) return null;

    return (
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-800 dark:to-gray-900 p-6 rounded-2xl border border-purple-200 dark:border-gray-700">
        <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-purple-600" />
          {viz.title}
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <ChartComponent data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey={viz.x} stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }} 
            />
            <Legend />
            <DataComponent 
              dataKey={viz.y} 
              fill="#8b5cf6" 
              stroke="#8b5cf6"
              strokeWidth={2}
            />
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-purple-600 to-indigo-600 p-2 rounded-xl">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                  Project Samarth
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Enhanced Agricultural Query System
                </p>
              </div>
            </div>
            {metadata && (
              <div className="hidden md:flex items-center gap-2 bg-green-100 dark:bg-green-900/30 px-4 py-2 rounded-full">
                <Database className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  Database Connected
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6 sticky top-24">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                  Sample Questions
                </h2>
                <button
                  onClick={generateNewQuestions}
                  disabled={loadingQuestions}
                  className="text-xs bg-purple-100 dark:bg-purple-900 hover:bg-purple-200 dark:hover:bg-purple-800 text-purple-700 dark:text-purple-300 px-3 py-1 rounded-full transition-all disabled:opacity-50 flex items-center gap-1"
                  title="Generate new questions"
                >
                  {loadingQuestions ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3 h-3" />
                      Refresh
                    </>
                  )}
                </button>
              </div>
              <div className="space-y-2">
                {sampleQuestions.length > 0 ? (
                  sampleQuestions.map((sq, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleQuestionClick(sq.question)}
                      disabled={loadingQuestions}
                      className="w-full text-left px-4 py-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 hover:from-purple-100 hover:to-indigo-100 dark:hover:from-gray-600 dark:hover:to-gray-500 rounded-xl transition-all text-sm font-medium text-gray-700 dark:text-gray-200 border border-purple-200 dark:border-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="font-semibold text-purple-600 dark:text-purple-400 text-xs mb-1">
                        {sq.label}
                      </div>
                      {sq.question}
                    </button>
                  ))
                ) : (
                  <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                    Loading questions...
                  </div>
                )}
              </div>

              {metadata && (
                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-sm font-bold text-gray-700 dark:text-gray-300 mb-3">
                    System Status
                  </h3>
                  {Object.entries(metadata.tables).map(([name, info]) => (
                    <div key={name} className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg mb-2">
                      <p className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                        {name}
                      </p>
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                        {info.date_range[0]} - {info.date_range[1]}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3">
            {/* Query Input */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
              <form onSubmit={handleSubmit}>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Ask your agricultural data question:
                </label>
                <div className="relative">
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Compare rice production in Assam and Odisha over last 5 years"
                    className="w-full px-4 py-3 pr-12 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none transition-all"
                    rows="3"
                    disabled={loading}
                  />
                  <Search className="absolute right-4 top-3 w-5 h-5 text-gray-400" />
                </div>
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="mt-4 w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      Analyze Query
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Results */}
            {response && (
              <div className="space-y-6">
                {/* Answer */}
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6">
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-4 flex items-center gap-2">
                    <Activity className="w-6 h-6 text-purple-600" />
                    Answer
                  </h2>
                  <div 
                    className="prose dark:prose-invert max-w-none"
                    dangerouslySetInnerHTML={{ 
                      __html: response.answer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
                    }}
                  />
                </div>

                {/* Key Findings */}
                {response.key_findings?.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('findings')}
                      className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-amber-50 to-orange-50 dark:from-gray-700 dark:to-gray-600 hover:from-amber-100 hover:to-orange-100 dark:hover:from-gray-600 dark:hover:to-gray-500 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                        <FileText className="w-5 h-5 text-amber-600" />
                        Key Findings
                      </h3>
                      {expandedSections.findings ? (
                        <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </button>
                    {expandedSections.findings && (
                      <div className="p-6">
                        <ul className="space-y-2">
                          {response.key_findings.map((finding, idx) => (
                            <li key={idx} className="flex items-start gap-3">
                              <span className="flex-shrink-0 w-6 h-6 bg-gradient-to-br from-amber-500 to-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                                {idx + 1}
                              </span>
                              <span className="text-gray-700 dark:text-gray-300">{finding}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Visualization */}
                {response.visualization && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('visualization')}
                      className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-purple-50 to-blue-50 dark:from-gray-700 dark:to-gray-600 hover:from-purple-100 hover:to-blue-100 dark:hover:from-gray-600 dark:hover:to-gray-500 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-purple-600" />
                        Visualization
                      </h3>
                      {expandedSections.visualization ? (
                        <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </button>
                    {expandedSections.visualization && (
                      <div className="p-6">
                        {renderVisualization()}
                      </div>
                    )}
                  </div>
                )}

                {/* Citations & Sources */}
                {response.citations?.sources?.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('sources')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                        <Database className="w-5 h-5 text-blue-600" />
                        Data Sources & Provenance
                      </h3>
                      {expandedSections.sources ? (
                        <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </button>
                    {expandedSections.sources && (
                      <div className="p-6 space-y-4">
                        {response.citations.sources.map((source, idx) => (
                          <div key={idx} className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-200 dark:border-blue-800">
                            <p className="font-semibold text-gray-800 dark:text-white">
                              Table: {source.table}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                              File: {source.file}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Rows Retrieved: {source.rows_retrieved}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* SQL Queries */}
                {response.citations?.queries?.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('queries')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                        SQL Queries Executed
                      </h3>
                      {expandedSections.queries ? (
                        <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </button>
                    {expandedSections.queries && (
                      <div className="p-6 space-y-4">
                        {response.citations.queries.map((query, idx) => (
                          <div key={idx} className="bg-gray-50 dark:bg-gray-900 p-4 rounded-xl">
                            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              Query {query.query_id}
                            </p>
                            <pre className="bg-gray-800 text-green-400 p-3 rounded-lg overflow-x-auto text-xs">
                              {query.sql}
                            </pre>
                            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                              <p>Parameters: {JSON.stringify(query.parameters)}</p>
                              <p>Execution Time: {query.execution_time}</p>
                              <p>Rows Returned: {query.rows_returned}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Raw Data */}
                {response.results?.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('data')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                        Retrieved Data
                      </h3>
                      {expandedSections.data ? (
                        <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </button>
                    {expandedSections.data && (
                      <div className="p-6 space-y-4">
                        {response.results.map((result, idx) => (
                          <div key={idx}>
                            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              Result {idx + 1}: {result.source_metadata.table}
                            </h4>
                            <div className="overflow-x-auto">
                              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                <thead className="bg-gray-50 dark:bg-gray-900">
                                  <tr>
                                    {result.data[0] && Object.keys(result.data[0]).map(key => (
                                      <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                  {result.data.slice(0, 10).map((row, rowIdx) => (
                                    <tr key={rowIdx}>
                                      {Object.values(row).map((val, valIdx) => (
                                        <td key={valIdx} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                                          {val}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* System Logs */}
                {response.logs?.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('logs')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                        System Logs
                      </h3>
                      {expandedSections.logs ? (
                        <ChevronUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </button>
                    {expandedSections.logs && (
                      <div className="p-6">
                        <pre className="bg-gray-900 text-green-400 p-4 rounded-xl overflow-x-auto text-xs">
                          {response.logs.join('\n')}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;