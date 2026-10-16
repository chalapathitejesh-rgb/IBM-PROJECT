"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShieldAlert, Loader2 } from "lucide-react";
import axios from "axios";

export default function LoginPage() {
  const [email, setEmail] = useState("admin"); // Pre-filled for demo
  const [password, setPassword] = useState("admin123");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      // Backend expects standard OAuth2 PasswordRequestForm which uses URL encoded form data
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await axios.post("http://localhost:8000/api/v1/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      
      const data = response.data;
      
      if (data.access_token) {
        // Fetch user profile
        const userRes = await axios.get("http://localhost:8000/api/v1/auth/me", {
          headers: { Authorization: `Bearer ${data.access_token}` }
        });
        
        login(data.access_token, userRes.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to login. Please check credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
      
      <Card className="z-10 w-full max-w-md bg-zinc-900/80 border-zinc-800 backdrop-blur-xl">
        <CardHeader className="space-y-2 text-center">
          <div className="mx-auto bg-blue-500/10 p-3 rounded-full w-fit mb-2">
            <ShieldAlert className="w-8 h-8 text-blue-500" />
          </div>
          <CardTitle className="text-2xl text-zinc-50">deepSheild SOC</CardTitle>
          <CardDescription className="text-zinc-400">
            Sign in to the HTCS Analysis Command Center
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Username</label>
              <input 
                type="text" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="admin"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-300">Password</label>
              <input 
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="••••••••"
                required
              />
            </div>
            
            {error && (
              <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-sm text-red-400">
                {error}
              </div>
            )}
            
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white" disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {isLoading ? "Authenticating..." : "Access Dashboard"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
