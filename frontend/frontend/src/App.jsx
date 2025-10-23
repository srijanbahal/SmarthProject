import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Search, Loader2, ChevronDown, ChevronUp, Database, FileText, Activity, TrendingUp, BarChart3, Sparkles, RefreshCw } from 'lucide-react';

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
      console.log('Generating new sample questions...');
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
      <div className="bg-white dark:bg-gray-900 p-6 rounded-lg border border-gray-200 dark:border-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          {viz.title}
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <ChartComponent data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-800" />
            <XAxis dataKey={viz.x} stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '6px'
              }}
            />
            <Legend />
            <DataComponent
              dataKey={viz.y}
              fill="#000000"
              stroke="#000000"
              strokeWidth={2}
            />
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-950">
      {/* Fixed Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between max-w-[1600px] mx-auto">
            <div className="flex items-center gap-3">
              <div className="bg-black dark:bg-white p-2 rounded-lg">
                <Sparkles className="w-6 h-6 text-white dark:text-black" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Project Samarth
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Enhanced Agricultural Query System
                </p>
              </div>
            </div>
            {metadata && (
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-900 px-3 py-1.5 rounded-md border border-gray-200 dark:border-gray-800">
                <Database className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  Database Connected
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content with Fixed Sidebar */}
      <div className="flex pt-[73px] h-screen">
        {/* Fixed Sidebar */}
        <aside className="fixed left-0 top-[73px] bottom-0 w-80 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Sample Questions
              </h2>
              <button
                onClick={generateNewQuestions}
                disabled={loadingQuestions}
                className="text-xs bg-gray-100 dark:bg-gray-900 hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-900 dark:text-white px-2 py-1 rounded border border-gray-200 dark:border-gray-800 transition-all disabled:opacity-50 flex items-center gap-1"
                title="Generate new questions"
              >
                {loadingQuestions ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RefreshCw className="w-3 h-3" />
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
                    className="w-full text-left px-3 py-2.5 bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-all text-sm text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <div className="font-semibold text-gray-900 dark:text-white text-xs mb-1">
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
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-800">
                <h3 className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-3">
                  System Status
                </h3>
                {Object.entries(metadata.tables).map(([name, info]) => (
                  <div key={name} className="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg mb-2 border border-gray-200 dark:border-gray-800">
                    <p className="text-xs font-semibold text-gray-900 dark:text-white">
                      {name}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {info.date_range[0]} - {info.date_range[1]}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 ml-80 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-8 py-8">
            {/* Query Input */}
            <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 p-6 mb-6">
              <form onSubmit={handleSubmit}>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  Ask your agricultural data question:
                </label>
                <div className="relative">
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Which crops have the highest yield in Assam?"
                    className="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-800 rounded-lg focus:ring-2 focus:ring-black dark:focus:ring-white focus:border-transparent bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 resize-none transition-all"
                    rows="3"
                    disabled={loading}
                  />
                  <Search className="absolute right-4 top-3 w-5 h-5 text-gray-400" />
                </div>
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="mt-4 w-full bg-black hover:bg-gray-800 disabled:bg-gray-300 dark:bg-white dark:hover:bg-gray-200 dark:disabled:bg-gray-700 text-white dark:text-black font-semibold py-3 px-6 rounded-lg transition-all disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
                <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Answer
                  </h2>
                  <div
                    className="prose dark:prose-invert max-w-none text-gray-700 dark:text-gray-300"
                    dangerouslySetInnerHTML={{
                      __html: response.answer.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>')
                    }}
                  />
                </div>

                {/* Key Findings */}
                {response.key_findings?.length > 0 && (
                  <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <button
                      onClick={() => toggleSection('findings')}
                      className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <FileText className="w-5 h-5" />
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
                              <span className="shrink-0 w-6 h-6 bg-black dark:bg-white text-white dark:text-black rounded-full flex items-center justify-center text-xs font-bold">
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
                  <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <button
                      onClick={() => toggleSection('visualization')}
                      className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <BarChart3 className="w-5 h-5" />
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
                  <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <button
                      onClick={() => toggleSection('sources')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Database className="w-5 h-5" />
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
                          <div key={idx} className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-800">
                            <p className="font-semibold text-gray-900 dark:text-white">
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
                  <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <button
                      onClick={() => toggleSection('queries')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
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
                          <div key={idx} className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                              Query {query.query_id}
                            </p>
                            <pre className="bg-gray-900 dark:bg-black text-green-400 p-3 rounded-lg overflow-x-auto text-xs">
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
                  <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <button
                      onClick={() => toggleSection('data')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
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
                              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
                                <thead className="bg-gray-50 dark:bg-gray-900">
                                  <tr>
                                    {result.data[0] && Object.keys(result.data[0]).map(key => (
                                      <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="bg-white dark:bg-gray-950 divide-y divide-gray-200 dark:divide-gray-800">
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
                  <div className="bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
                    <button
                      onClick={() => toggleSection('logs')}
                      className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
                    >
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
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
                        <pre className="bg-gray-900 dark:bg-black text-green-400 p-4 rounded-lg overflow-x-auto text-xs">
                          {response.logs.join('\n')}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
