"use client";
import { useEffect, useState } from 'react';

export default function WalletPage() {
  const [balance, setBalance] = useState("Loading...");
  const [amount, setAmount] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem('token') || '');
  }, []);

  const fetchWallet = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/wallet`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setBalance(data.balance);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchWallet();
  }, [token]);

  const addFunds = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/wallet/fund`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ amount: amount })
      });
      if (res.ok) {
        setAmount("");
        fetchWallet();
      } else {
        alert("Failed to add funds");
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Wallet</h1>
      <div className="bg-white shadow p-6 rounded-lg max-w-md">
        <h2 className="text-gray-500 mb-2">Current Balance</h2>
        <p className="text-4xl font-bold text-green-600">${balance}</p>
        <div className="mt-4 flex gap-2">
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="border p-2 rounded w-full text-black"
            placeholder="Amount"
          />
          <button onClick={addFunds} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 whitespace-nowrap">
            Add Funds
          </button>
        </div>
      </div>
    </div>
  );
}
