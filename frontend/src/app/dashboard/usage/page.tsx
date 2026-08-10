"use client";
import { useEffect, useState } from 'react';

export default function UsagePage() {
  const [stats, setStats] = useState({ total_requests: 0, total_cost: 0, total_tokens: 0 });
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem('token') || '');
  }, []);

  useEffect(() => {
    const fetchUsage = async () => {
      if (!token) return;
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dashboard/usage`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchUsage();
  }, [token]);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Usage Statistics</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 shadow rounded-lg">
          <h2 className="text-gray-500 mb-2">Total Requests</h2>
          <p className="text-3xl font-bold text-black">{stats.total_requests}</p>
        </div>
        <div className="bg-white p-6 shadow rounded-lg">
          <h2 className="text-gray-500 mb-2">Total Cost</h2>
          <p className="text-3xl font-bold text-red-500">${stats.total_cost}</p>
        </div>
        <div className="bg-white p-6 shadow rounded-lg">
          <h2 className="text-gray-500 mb-2">Tokens Processed</h2>
          <p className="text-3xl font-bold text-black">{stats.total_tokens}</p>
        </div>
      </div>
    </div>
  );
}
