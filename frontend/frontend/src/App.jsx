"use client"

import { useState, useEffect } from "react"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import {
  Search,
  Loader2,
  Database,
  FileText,
  Activity,
  BarChart3,
  Sparkles,
  Menu,
  X,
  Leaf,
  Code2,
  Table2,
  Terminal,
} from "lucide-react"
import ReactMarkdown from "react-markdown"

const API_BASE_URL = "http://localhost:8000"

function App() {
  const [question, setQuestion] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingQuestions, setLoadingQuestions] = useState(false)
  const [response, setResponse] = useState(null)
  const [metadata, setMetadata] = useState(null)
  const [sampleQuestions, setSampleQuestions] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState("sources")

  useEffect(() => {
    fetchMetadata()
    fetchSampleQuestions()
  }, [])

  const fetchMetadata = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/metadata`)
      const data = await res.json()
      setMetadata(data)
    } catch (error) {
      console.error("Failed to fetch metadata:", error)
    }
  }

  const fetchSampleQuestions = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/sample-questions`)
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      const data = await res.json()
      setSampleQuestions(data.questions || [])
    } catch (error) {
      console.error("Failed to fetch sample questions:", error)
      setSampleQuestions([
        { label: "Compare States", question: "Compare rice production in Assam and Odisha over last 5 years" },
        { label: "Find Maximum", question: "Which state had highest wheat production in 2014?" },
        { label: "Trend Analysis", question: "Analyze wheat production trend in Assam for last 10 years" },
        { label: "Correlation", question: "How does annual rainfall correlate with rice production in Odisha?" },
        { label: "Policy Insight", question: "Which crops have the highest yield in Assam?" },
      ])
    }
  }

  const generateNewQuestions = async () => {
    setLoadingQuestions(true)
    try {
      const res = await fetch(`${API_BASE_URL}/generate-sample-questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
      const data = await res.json()
      setSampleQuestions(data.questions || [])
    } catch (error) {
      console.error("Failed to generate new questions:", error)
      alert("Failed to generate new questions. Please try again.")
    } finally {
      setLoadingQuestions(false)
    }
  }

  const handleQuestionClick = async (questionText) => {
    setQuestion(questionText)
    await generateNewQuestions()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setResponse(null)

    try {
      const res = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      })

      if (!res.ok) throw new Error("Query failed")
      const data = await res.json()
      setResponse(data)
      setActiveTab("sources")
    } catch (error) {
      console.error("Query error:", error)
      alert("Failed to process query. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const renderVisualization = () => {
    if (!response?.visualization || !response?.results?.length) return null

    const viz = response.visualization
    const resultIdx = viz.result_index || 0
    const data = response.results[resultIdx]?.data || []

    if (!data.length) return null

    const ChartComponent = {
      bar: BarChart,
      line: LineChart,
      scatter: ScatterChart,
    }[viz.type]

    const DataComponent = {
      bar: Bar,
      line: Line,
      scatter: Scatter,
    }[viz.type]

    if (!ChartComponent || !DataComponent) return null

    return (
      <div className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-slate-800 dark:to-slate-900 p-6 rounded-2xl border border-emerald-200 dark:border-slate-700">
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          {viz.title}
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <ChartComponent data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey={viz.x} stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(255, 255, 255, 0.95)",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
              }}
            />
            <Legend />
            <DataComponent dataKey={viz.y} fill="#10b981" stroke="#10b981" strokeWidth={2} />
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    )
  }

  const MarkdownContent = ({ content }) => {
    return (
      <div className="prose dark:prose-invert max-w-none">
        <ReactMarkdown
          components={{
            h1: ({ node, ...props }) => (
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white mt-6 mb-4" {...props} />
            ),
            h2: ({ node, ...props }) => (
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-5 mb-3" {...props} />
            ),
            h3: ({ node, ...props }) => (
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-4 mb-2" {...props} />
            ),
            p: ({ node, ...props }) => (
              <p className="text-slate-700 dark:text-slate-300 mb-3 leading-relaxed" {...props} />
            ),
            strong: ({ node, ...props }) => (
              <strong className="font-bold text-emerald-600 dark:text-emerald-400" {...props} />
            ),
            em: ({ node, ...props }) => <em className="italic text-slate-600 dark:text-slate-400" {...props} />,
            ul: ({ node, ...props }) => (
              <ul className="list-disc list-inside space-y-2 mb-3 text-slate-700 dark:text-slate-300" {...props} />
            ),
            ol: ({ node, ...props }) => (
              <ol className="list-decimal list-inside space-y-2 mb-3 text-slate-700 dark:text-slate-300" {...props} />
            ),
            li: ({ node, ...props }) => <li className="ml-2" {...props} />,
            code: ({ node, inline, ...props }) =>
              inline ? (
                <code
                  className="bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-emerald-600 dark:text-emerald-400 font-mono text-sm"
                  {...props}
                />
              ) : (
                <code
                  className="bg-slate-900 text-emerald-400 p-3 rounded-lg block overflow-x-auto font-mono text-sm mb-3"
                  {...props}
                />
              ),
            blockquote: ({ node, ...props }) => (
              <blockquote
                className="border-l-4 border-emerald-500 pl-4 italic text-slate-600 dark:text-slate-400 my-3"
                {...props}
              />
            ),
            table: ({ node, ...props }) => (
              <div className="overflow-x-auto mb-3">
                <table
                  className="min-w-full border-collapse border border-slate-300 dark:border-slate-700"
                  {...props}
                />
              </div>
            ),
            th: ({ node, ...props }) => (
              <th
                className="border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 px-3 py-2 text-left font-semibold"
                {...props}
              />
            ),
            td: ({ node, ...props }) => (
              <td className="border border-slate-300 dark:border-slate-700 px-3 py-2" {...props} />
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    )
  }

  const tabs = [
    { id: "sources", label: "Data Sources", icon: Database },
    { id: "queries", label: "SQL Queries", icon: Code2 },
    { id: "data", label: "Retrieved Data", icon: Table2 },
    { id: "logs", label: "System Logs", icon: Terminal },
  ]

  return (
    <div className="w-screen min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* Enhanced Header */}
      <header className="sticky top-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Logo Section */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-br from-emerald-600 to-teal-600 p-2.5 rounded-xl shadow-lg">
                  <Leaf className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                    Samarth
                  </h1>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Agricultural Intelligence</p>
                </div>
              </div>
            </div>

            {/* Status Badge */}
            {metadata && (
              <div className="hidden md:flex items-center gap-2 bg-emerald-50 dark:bg-emerald-900/20 px-4 py-2 rounded-full border border-emerald-200 dark:border-emerald-800">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">System Active</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Enhanced Sidebar - Made sidebar fixed with independent scrolling */}
        <aside
          className={`${
            sidebarOpen ? "w-80" : "w-0"
          } lg:w-80 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 fixed lg:relative h-[calc(100vh-73px)] overflow-y-auto transition-all duration-300 flex-shrink-0 z-40`}
        >
          <div className="p-6 space-y-6">
            {/* Sample Questions Header */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  Explore
                </h2>
                <button
                  onClick={generateNewQuestions}
                  disabled={loadingQuestions}
                  className="text-xs bg-emerald-100 dark:bg-emerald-900/30 hover:bg-emerald-200 dark:hover:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 px-3 py-1.5 rounded-full transition-all disabled:opacity-50 flex items-center gap-1 font-medium"
                  title="Generate new questions"
                >
                  {loadingQuestions ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span className="hidden sm:inline">Generating</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3 h-3" />
                      <span className="hidden sm:inline">Refresh</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
                Click any question to explore agricultural insights
              </p>
            </div>

            {/* Sample Questions */}
            <div className="space-y-2">
              {sampleQuestions.length > 0 ? (
                sampleQuestions.map((sq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuestionClick(sq.question)}
                    disabled={loadingQuestions}
                    className="w-full text-left px-4 py-3 bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-700 hover:from-emerald-50 hover:to-teal-50 dark:hover:from-emerald-900/20 dark:hover:to-teal-900/20 rounded-xl transition-all text-sm font-medium text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 hover:border-emerald-300 dark:hover:border-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    <div className="font-semibold text-emerald-600 dark:text-emerald-400 text-xs mb-1 group-hover:text-emerald-700 dark:group-hover:text-emerald-300">
                      {sq.label}
                    </div>
                    <div className="text-slate-600 dark:text-slate-300 line-clamp-2">{sq.question}</div>
                  </button>
                ))
              ) : (
                <div className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">
                  <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                  Loading questions...
                </div>
              )}
            </div>

            {/* System Status */}
            {metadata && (
              <div className="pt-6 border-t border-slate-200 dark:border-slate-800">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
                  <Database className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  Data Sources
                </h3>
                <div className="space-y-2">
                  {Object.entries(metadata.tables).map(([name, info]) => (
                    <div
                      key={name}
                      className="bg-emerald-50 dark:bg-emerald-900/20 p-3 rounded-lg border border-emerald-200 dark:border-emerald-800"
                    >
                      <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300 uppercase tracking-wide">
                        {name}
                      </p>
                      <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1">
                        {info.date_range[0]} → {info.date_range[1]}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Main Content - Added margin to account for fixed sidebar on desktop */}
        <main className="flex-1 overflow-y-auto lg:ml-0 w-full">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Query Input Section */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 mb-8">
              <form onSubmit={handleSubmit}>
                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-3">
                  Ask your agricultural question
                </label>
                <div className="relative mb-4">
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Compare rice production in Assam and Odisha over last 5 years"
                    className="w-full px-4 py-3 pr-12 border-2 border-slate-300 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent dark:bg-slate-800 dark:text-white resize-none transition-all placeholder:text-slate-400 dark:placeholder:text-slate-500"
                    rows="3"
                    disabled={loading}
                  />
                  <Search className="absolute right-4 top-3 w-5 h-5 text-slate-400 pointer-events-none" />
                </div>
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center justify-center gap-2"
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

            {/* Results Section with Tabs */}
            {response && (
              <div className="space-y-6">
                {/* Answer */}
                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <Activity className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                    Answer
                  </h2>
                  <MarkdownContent content={response.answer} />
                </div>

                {/* Key Findings */}
                {response.key_findings?.length > 0 && (
                  <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                      <FileText className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                      Key Findings
                    </h3>
                    <ul className="space-y-3">
                      {response.key_findings.map((finding, idx) => (
                        <li key={idx} className="flex items-start gap-3">
                          <span className="shrink-0 w-6 h-6 bg-gradient-to-br from-amber-500 to-orange-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                            {idx + 1}
                          </span>
                          <span className="text-slate-700 dark:text-slate-300">{finding}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Visualization */}
                {response.visualization && (
                  <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                      <BarChart3 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                      Visualization
                    </h3>
                    {renderVisualization()}
                  </div>
                )}

                {(response.citations?.sources?.length > 0 ||
                  response.citations?.queries?.length > 0 ||
                  response.results?.length > 0 ||
                  response.logs?.length > 0) && (
                  <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    {/* Tab Navigation - Improved spacing and styling */}
                    <div className="flex overflow-x-auto border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                      {tabs.map((tab) => {
                        const TabIcon = tab.icon
                        const isActive = activeTab === tab.id
                        const hasContent =
                          (tab.id === "sources" && response.citations?.sources?.length > 0) ||
                          (tab.id === "queries" && response.citations?.queries?.length > 0) ||
                          (tab.id === "data" && response.results?.length > 0) ||
                          (tab.id === "logs" && response.logs?.length > 0)

                        if (!hasContent) return null

                        return (
                          // <div className="items-center" key={tab.id}>
                          <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center mx-3 gap-2 px-5 py-3 font-medium text-sm whitespace-nowrap transition-all border-b-2 my-2 ${
                              isActive
                                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400 bg-white dark:bg-slate-900"
                                : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/50"
                            }`}
                          >
                            <TabIcon className="w-4 h-4 flex-shrink-0" />
                            <span>{tab.label}</span>
                          </button>
                          // </div>
                        )
                      })}
                    </div>

                    {/* Tab Content */}
                    <div className="p-6">
                      {/* Data Sources Tab */}
                      {activeTab === "sources" && response.citations?.sources?.length > 0 && (
                        <div className="space-y-3 mx-2">
                          {response.citations.sources.map((source, idx) => (
                            <div
                              key={idx}
                              className="bg-teal-50 dark:bg-teal-900/20 p-4 rounded-lg border border-teal-200 dark:border-teal-800 hover:border-teal-400 dark:hover:border-teal-600 hover:shadow-md transition-all "
                            >
                              <p className="font-semibold text-slate-900 dark:text-white">{source.table}</p>
                              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{source.file}</p>
                              <p className="text-sm text-slate-600 dark:text-slate-400">{source.rows_retrieved} rows</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* SQL Queries Tab */}
                      {activeTab === "queries" && response.citations?.queries?.length > 0 && (
                        <div className="space-y-4">
                          {response.citations.queries.map((query, idx) => (
                            <div
                              key={idx}
                              className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 hover:shadow-md transition-all"
                            >
                              <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                                Query {query.query_id}
                              </p>
                              <pre className="bg-slate-900 text-emerald-400 p-3 rounded-lg overflow-x-auto text-xs font-mono">
                                {query.sql}
                              </pre>
                              <div className="mt-2 text-xs text-slate-600 dark:text-slate-400 space-y-1">
                                <p>Parameters: {JSON.stringify(query.parameters)}</p>
                                <p>Execution Time: {query.execution_time}</p>
                                <p>Rows Returned: {query.rows_returned}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Retrieved Data Tab */}
                      {activeTab === "data" && response.results?.length > 0 && (
                        <div className="space-y-4">
                          {response.results.map((result, idx) => (
                            <div key={idx}>
                              <h4 className="font-semibold text-slate-900 dark:text-white mb-3">
                                {result.source_metadata.table}
                              </h4>
                              <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                                  <thead className="bg-slate-100 dark:bg-slate-800">
                                    <tr>
                                      {result.data[0] &&
                                        Object.keys(result.data[0]).map((key) => (
                                          <th
                                            key={key}
                                            className="px-4 py-2 text-left text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wide"
                                          >
                                            {key}
                                          </th>
                                        ))}
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-700">
                                    {result.data.slice(0, 10).map((row, rowIdx) => (
                                      <tr
                                        key={rowIdx}
                                        className="hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                      >
                                        {Object.values(row).map((val, valIdx) => (
                                          <td
                                            key={valIdx}
                                            className="px-4 py-2 text-sm text-slate-700 dark:text-slate-300"
                                          >
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

                      {/* System Logs Tab */}
                      {activeTab === "logs" && response.logs?.length > 0 && (
                        <pre className="bg-slate-900 text-emerald-400 p-4 rounded-lg overflow-x-auto text-xs font-mono">
                          {response.logs.join("\n")}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
