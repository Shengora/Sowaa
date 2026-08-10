import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from 'next/link';
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Sowaa",
  description: "AI API Proxy and Monetization Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen bg-gray-50 text-black">
          <nav className="w-64 bg-white shadow-md flex flex-col p-4">
            <h1 className="text-xl font-bold mb-8 text-blue-600">Sowaa</h1>
            <div className="flex flex-col gap-2">
              <Link href="/" className="p-2 hover:bg-gray-100 rounded">Home / Auth</Link>
              <Link href="/dashboard/wallet" className="p-2 hover:bg-gray-100 rounded">Wallet</Link>
              <Link href="/dashboard/api-keys" className="p-2 hover:bg-gray-100 rounded">API Keys</Link>
              <Link href="/dashboard/usage" className="p-2 hover:bg-gray-100 rounded">Usage</Link>
              <hr className="my-4" />
              <p className="text-xs text-gray-500 font-bold mb-2 uppercase">Admin</p>
              <Link href="/admin/users" className="p-2 hover:bg-gray-100 rounded">Users</Link>
              <Link href="/admin/pricing" className="p-2 hover:bg-gray-100 rounded">Pricing</Link>
              <Link href="/admin/providers" className="p-2 hover:bg-gray-100 rounded">Providers</Link>
              <Link href="/admin/audit-logs" className="p-2 hover:bg-gray-100 rounded">Audit Logs</Link>
            </div>
          </nav>
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
