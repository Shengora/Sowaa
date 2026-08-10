"use client";
import { useState, useEffect } from 'react';

export default function AdminPricingPage() {
  const [model, setModel] = useState("");
  const [provider, setProvider] = useState("");
  const [inputPrice, setInputPrice] = useState("");
  const [outputPrice, setOutputPrice] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem('token') || '');
  }, []);

  const setPricing = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/pricing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          model, provider, input_price: inputPrice, output_price: outputPrice
        })
      });
      if (res.ok) {
        alert("Pricing updated!");
        setModel(""); setProvider(""); setInputPrice(""); setOutputPrice("");
      } else {
        alert("Failed to update pricing");
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Pricing Configuration</h1>
      <div className="bg-white shadow rounded-lg p-6 max-w-lg text-black">
        <div className="flex flex-col gap-4">
          <input type="text" placeholder="Model (e.g. claude-sonnet)" value={model} onChange={e => setModel(e.target.value)} className="border p-2 rounded" />
          <input type="text" placeholder="Provider (e.g. anthropic)" value={provider} onChange={e => setProvider(e.target.value)} className="border p-2 rounded" />
          <input type="number" placeholder="Input Price (per 1M tokens)" value={inputPrice} onChange={e => setInputPrice(e.target.value)} className="border p-2 rounded" />
          <input type="number" placeholder="Output Price (per 1M tokens)" value={outputPrice} onChange={e => setOutputPrice(e.target.value)} className="border p-2 rounded" />
          <button onClick={setPricing} className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700">Set Pricing</button>
        </div>
      </div>
    </div>
  );
}
