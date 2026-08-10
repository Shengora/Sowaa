"use client";
import { useState, useEffect } from 'react';

export default function AdminProvidersPage() {
  const [providerName, setProviderName] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem('token') || '');
  }, []);

  const verifyCompliance = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/providers/${providerName}/compliance`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        alert("Compliance verified!");
        setProviderName("");
      } else {
        alert("Failed to verify compliance");
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Provider Compliance</h1>
      <div className="bg-white shadow rounded-lg p-6 max-w-lg text-black">
        <p className="mb-4 text-sm text-gray-600">Explicitly verify that you have legal permission to use the provider.</p>
        <div className="flex gap-2">
          <input type="text" placeholder="Provider Name (e.g. anthropic)" value={providerName} onChange={e => setProviderName(e.target.value)} className="border p-2 rounded w-full" />
          <button onClick={verifyCompliance} className="bg-green-600 text-white p-2 rounded hover:bg-green-700 whitespace-nowrap">Verify & Enable</button>
        </div>
      </div>
    </div>
  );
}
