"use client";
import { useEffect, useState } from 'react';

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<any[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [shownKey, setShownKey] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem('token') || '');
  }, []);

  const fetchKeys = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/keys`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setKeys(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, [token]);

  const generateKey = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name: newKeyName || "New Key" })
      });
      if (res.ok) {
        const data = await res.json();
        setShownKey(data.raw_key);
        setNewKeyName("");
        fetchKeys();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const revokeKey = async (id: number) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/keys/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) fetchKeys();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Keys</h1>

      {shownKey && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
          <p className="font-bold">Please copy your API key now. It will not be shown again.</p>
          <p className="mt-2 font-mono bg-yellow-200 p-2 inline-block rounded">{shownKey}</p>
        </div>
      )}

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          className="border p-2 rounded text-black"
          placeholder="Key Name"
        />
        <button onClick={generateKey} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Generate New Key
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Key Prefix</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {keys.map((k) => (
              <tr key={k.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{k.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{k.key_prefix}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button onClick={() => revokeKey(k.id)} className="text-red-600 hover:text-red-900">Revoke</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
