import React from 'react';
export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">Customer Segmentation CDP</h1>
        <p className="text-gray-400 mb-8">Customer segments, RFM analysis, and cohort tracking</p>
        <div className="bg-gray-900 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">API Endpoints</h2>
          <ul className="space-y-2 text-gray-300"><li>/customers</li>
<li>/customers/{id}</li>
<li>/segments</li>
<li>/segments/{id}/customers</li>
<li>/rfm-analysis</li></ul>
        </div>
      </div>
    </div>
  );
}
