import { useState } from 'react';

type Endpoint = {
  label: string;
  method: string;
  path: string;
  body?: any;
  headers?: Record<string, string>;
};

const TITLE = "B2B Customer Segmentation & Churn Predictor";
const TAGLINE = "300 synthetic cloud-services accounts (Large/Medium/Small companies) segmented with KMeans and churn-scored by an interpretable logistic-regression model.";

const ENDPOINTS: Endpoint[] = [
  {
    "label": "Health check",
    "method": "GET",
    "path": "/health"
  },
  {
    "label": "Segment summary",
    "method": "GET",
    "path": "/api/segments"
  },
  {
    "label": "At-Risk accounts",
    "method": "GET",
    "path": "/api/accounts?segment=At-Risk&page=1&page_size=10"
  },
  {
    "label": "Critical-risk small accounts",
    "method": "GET",
    "path": "/api/accounts?risk_band=Critical&size_tier=Small&page=1&page_size=10"
  },
  {
    "label": "One account with churn drivers",
    "method": "GET",
    "path": "/api/accounts/acct-0001"
  },
  {
    "label": "Churn risk summary",
    "method": "GET",
    "path": "/api/churn/summary"
  },
  {
    "label": "Model metrics & coefficients",
    "method": "GET",
    "path": "/api/churn/model"
  },
  {
    "label": "Recompute segments + churn scores",
    "method": "POST",
    "path": "/api/refresh"
  }
];

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-emerald-900 text-emerald-300',
  POST: 'bg-indigo-900 text-indigo-300',
  PATCH: 'bg-amber-900 text-amber-300',
  DELETE: 'bg-red-900 text-red-300',
};

export default function Home() {
  const [output, setOutput] = useState('Click an endpoint on the left to call the live API.');
  const [active, setActive] = useState(-1);
  const [loading, setLoading] = useState(false);

  const run = async (i: number) => {
    const ep = ENDPOINTS[i];
    setActive(i);
    setLoading(true);
    try {
      const res = await fetch(ep.path, {
        method: ep.method,
        headers: {
          ...(ep.body ? { 'Content-Type': 'application/json' } : {}),
          ...(ep.headers || {}),
        },
        body: ep.body ? JSON.stringify(ep.body) : undefined,
      });
      const text = await res.text();
      let pretty = text;
      try { pretty = JSON.stringify(JSON.parse(text), null, 2); } catch {}
      setOutput(`${ep.method} ${ep.path}\nHTTP ${res.status}\n\n${pretty}`);
    } catch (e) {
      setOutput(String(e));
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">{TITLE}</h1>
        <p className="text-gray-400 mb-6">{TAGLINE}</p>
        <div className="grid md:grid-cols-5 gap-6">
          <div className="md:col-span-2 space-y-2">
            {ENDPOINTS.map((ep, i) => (
              <button
                key={i}
                onClick={() => run(i)}
                className={`w-full text-left bg-gray-900 border rounded-xl px-4 py-3 transition-colors ${
                  active === i ? 'border-indigo-500' : 'border-gray-800 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-mono px-2 py-0.5 rounded ${METHOD_COLORS[ep.method] || 'bg-gray-800'}`}>
                    {ep.method}
                  </span>
                  <span className="text-xs text-gray-500 font-mono truncate">{ep.path}</span>
                </div>
                <div className="text-sm font-medium">{ep.label}</div>
              </button>
            ))}
          </div>
          <div className="md:col-span-3">
            <pre className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm text-gray-300 overflow-auto whitespace-pre-wrap min-h-[24rem] max-h-[36rem]">
              {loading ? 'Loading...' : output}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
