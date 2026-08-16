import { useState } from "react";
import "./App.css";

const stages = [
  {
    id: "analyzing",
    label: "Analyzing your question",
    icon: "🔍",
  },
  {
    id: "schema",
    label: "Inspecting database schema",
    icon: "🗄️",
  },
  {
    id: "generating",
    label: "Generating SQL",
    icon: "✨",
  },
  {
    id: "guardrails",
    label: "Checking SQL safety",
    icon: "🛡️",
  },
  {
    id: "executing",
    label: "Executing query",
    icon: "⚡",
  },
  {
    id: "explanation",
    label: "Preparing explanation",
    icon: "📝",
  },
];

function App() {
  const [question, setQuestion] = useState(
    "Who scored the most runs in 2024?"
  );

  const [status, setStatus] = useState("idle");
  const [currentStage, setCurrentStage] = useState(-1);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");

  const runQuery = async () => {
    if (!question.trim() || status === "processing") {
      return;
    }

    setStatus("processing");
    setResponse(null);
    setError("");

    // Visual pipeline progression.
    setCurrentStage(0);

    const stageTimers = [
      setTimeout(() => setCurrentStage(1), 250),
      setTimeout(() => setCurrentStage(2), 500),
      setTimeout(() => setCurrentStage(3), 900),
      setTimeout(() => setCurrentStage(4), 1200),
      setTimeout(() => setCurrentStage(5), 1500),
    ];

    try {
      const res = await fetch(
        "http://127.0.0.1:8000/v1/query",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: question.trim(),
          }),
        }
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data.detail || "Request failed"
        );
      }

      setCurrentStage(5);
      setResponse(data);
      setStatus(
        data.verification?.status === "PASS"
          ? "completed"
          : "error"
      );
    } catch (err) {
      setError(err.message);
      setStatus("error");
    } finally {
      stageTimers.forEach(clearTimeout);
    }
  };

  const resetQuery = () => {
    setQuestion("");
    setStatus("idle");
    setCurrentStage(-1);
    setResponse(null);
    setError("");
  };

  const getStageClass = (index) => {
    if (status === "completed" && index <= 5) {
      return "stage completed";
    }

    if (status === "processing") {
      if (index < currentStage) {
        return "stage completed";
      }

      if (index === currentStage) {
        return "stage active";
      }
    }

    return "stage";
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AI Data Analyst</h1>
          <p>
            Ask questions about your IPL database using
            natural language.
          </p>
        </div>

        <div className="status-badge">
          <span className="status-dot"></span>
          AI Analyst
        </div>
      </header>

      <main className="container">

        {/* Question */}
        <section className="card question-card">
          <h2>Ask a question</h2>

          <textarea
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            placeholder="e.g. Who scored the most runs in 2024?"
            disabled={status === "processing"}
          />

          <div className="actions">
            <button
              className="run-button"
              onClick={runQuery}
              disabled={
                status === "processing" ||
                !question.trim()
              }
            >
              {status === "processing"
                ? "Analyzing..."
                : "Run Query"}
            </button>

            <button
              className="clear-button"
              onClick={resetQuery}
              disabled={status === "processing"}
            >
              Clear
            </button>
          </div>

          <div className="examples">
            <span>Try:</span>

            <button
              onClick={() =>
                setQuestion(
                  "Who scored the most runs in 2024?"
                )
              }
            >
              Top scorer in 2024
            </button>

            <button
              onClick={() =>
                setQuestion(
                  "Which team won the most matches in 2023?"
                )
              }
            >
              Most wins in 2023
            </button>
          </div>
        </section>

        {/* Processing */}
        {(status === "processing" ||
          status === "completed" ||
          status === "error") && (
          <section className="card">
            <div className="section-title">
              <h2>AI Processing</h2>

              {status === "processing" && (
                <span className="processing-label">
                  Processing...
                </span>
              )}

              {status === "completed" && (
                <span className="success-label">
                  ✓ Query completed
                </span>
              )}

              {status === "error" && (
                <span className="error-label">
                  Processing failed
                </span>
              )}
            </div>

            <div className="pipeline">
              {stages.map((stage, index) => (
                <div
                  key={stage.id}
                  className={getStageClass(index)}
                >
                  <div className="stage-icon">
                    {status === "processing" &&
                    index === currentStage ? (
                      <span className="spinner"></span>
                    ) : status === "completed" ||
                      index < currentStage ? (
                      "✓"
                    ) : (
                      stage.icon
                    )}
                  </div>

                  <span>{stage.label}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Error */}
        {error && (
          <section className="card error-card">
            <h2>Something went wrong</h2>
            <p>{error}</p>
          </section>
        )}

        {/* Verification */}
        {response && (
          <section className="card">
            <div className="section-title">
              <h2>Verification</h2>

              <span
                className={
                  response.verification.status === "PASS"
                    ? "pass-badge"
                    : "fail-badge"
                }
              >
                {response.verification.status}
              </span>
            </div>

            <div className="checks">
              {response.verification.checks.map(
                (check) => (
                  <div className="check" key={check}>
                    <span>✓</span>
                    {check.replaceAll("_", " ")}
                  </div>
                )
              )}
            </div>
          </section>
        )}

        {/* SQL */}
        {response?.sql && (
          <section className="card">
            <div className="section-title">
              <h2>Generated SQL</h2>

              <button
                className="copy-button"
                onClick={() =>
                  navigator.clipboard.writeText(
                    response.sql
                  )
                }
              >
                Copy
              </button>
            </div>

            <pre className="sql">
              <code>{response.sql}</code>
            </pre>
          </section>
        )}

        {/* Results */}
        {response?.result && (
          <section className="card">
            <h2>Results</h2>

            {response.result.length === 0 ? (
              <p className="empty">
                No matching records found.
              </p>
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      {Object.keys(
                        response.result[0]
                      ).map((column) => (
                        <th key={column}>
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {response.result.map(
                      (row, index) => (
                        <tr key={index}>
                          {Object.values(row).map(
                            (value, columnIndex) => (
                              <td key={columnIndex}>
                                {String(value)}
                              </td>
                            )
                          )}
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* Explanation */}
        {response?.explanation && (
          <section className="card explanation-card">
            <h2>Explanation</h2>

            <p>{response.explanation}</p>

            <div className="latency">
              Response time:{" "}
              <strong>
                {(response.latency_ms / 1000).toFixed(2)}s
              </strong>
            </div>
          </section>
        )}
      </main>

      <footer>
        AI Data Analyst · Safe Text-to-SQL · IPL Dataset
      </footer>
    </div>
  );
}

export default App;