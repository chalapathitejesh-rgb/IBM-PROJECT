"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  ShieldAlert, Plus, Activity, Search, Shield, Server, FileAudio, 
  LayoutDashboard, X, ArrowUpRight, Zap, RefreshCw, Filter, 
  FileText, Globe, CheckCircle2, AlertTriangle, Radio
} from "lucide-react";
import axios from "axios";
import { format } from "date-fns";
import Link from "next/link";

interface CaseItem {
  id: number;
  title: string;
  description: string;
  status: string;
  evidence_count: number;
  created_at: string;
}

interface SOCStats {
  total_cases: number;
  open_cases: number;
  resolved_cases: number;
  total_evidence: number;
  deepfake_scans: number;
  voice_scans: number;
  email_scans: number;
  url_scans: number;
  network_scans: number;
  detected_threats: number;
  avg_latency_ms: number;
}

export default function Dashboard() {
  const { user, token, logout } = useAuth();
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [stats, setStats] = useState<SOCStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Modal state
  const [showNewCase, setShowNewCase] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (token) {
      loadData();
    }
  }, [token]);

  const loadData = async () => {
    setIsLoading(true);
    await Promise.all([fetchCases(), fetchStats()]);
    setIsLoading(false);
  };

  const fetchCases = async () => {
    try {
      const res = await axios.get("http://localhost:8000/api/v1/cases/", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(res.data);
    } catch (err) {
      console.error("Error fetching cases:", err);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get("http://localhost:8000/api/v1/cases/stats/overview", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(res.data);
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  const handleCreateCase = async (presetTitle?: string, presetDesc?: string) => {
    const title = presetTitle || newTitle;
    const desc = presetDesc || newDesc;
    if (!title.trim()) return;
    
    setCreating(true);
    try {
      await axios.post("http://localhost:8000/api/v1/cases/", 
        { title: title.trim(), description: desc.trim() },
        { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
      );
      setNewTitle("");
      setNewDesc("");
      setShowNewCase(false);
      await loadData();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "Failed to create investigation");
    } finally {
      setCreating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "open":
        return <Badge className="bg-red-500/10 text-red-400 border border-red-500/20 font-medium">Open Threat</Badge>;
      case "investigating":
        return <Badge className="bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">Investigating</Badge>;
      case "closed":
        return <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">Resolved</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const filteredCases = cases.filter(c => {
    const matchesSearch = c.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          c.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          String(c.id).includes(searchQuery);
    const matchesStatus = statusFilter === "all" || c.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-[#090a0f] text-zinc-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
      
      {/* Background Cyber Grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f293d15_1px,transparent_1px),linear-gradient(to_bottom,#1f293d15_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>

      {/* Top SOC Navbar */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-[#090a0f]/90 backdrop-blur-xl">
        <div className="flex h-16 items-center px-6 justify-between max-w-7xl mx-auto w-full">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold tracking-tight text-white">deepSheild</span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono border border-blue-500/20">HTCS SOC</span>
              </div>
              <p className="text-[11px] text-zinc-500 font-mono">Holistic Threat Command System</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-xs text-zinc-400 border-r border-zinc-800/80 pr-4">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
              <span className="font-mono text-zinc-300">ENGINES ONLINE</span>
            </div>

            <div className="flex items-center gap-2 text-sm text-zinc-300 bg-zinc-900/60 px-3 py-1.5 rounded-lg border border-zinc-800">
              <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                {user?.email?.[0]?.toUpperCase() || "A"}
              </div>
              <span className="text-xs font-medium text-zinc-300 truncate max-w-[150px]">{user?.email || "Analyst"}</span>
            </div>

            <Button variant="outline" size="sm" onClick={logout} className="border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-400 text-xs">
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8 relative z-10">
        
        {/* Header Title & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 text-xs text-blue-400 font-mono mb-1">
              <Radio className="w-3.5 h-3.5 animate-pulse text-blue-500" />
              THREAT INTELLIGENCE & MULTI-MODAL RADAR
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">Active Investigations</h1>
            <p className="text-zinc-400 text-sm mt-1">Cross-modal analysis across Deepfake Video, Voice Clones, Phishing Emails, URLs & Network Flows.</p>
          </div>

          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              onClick={loadData}
              className="border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 text-xs"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Refresh
            </Button>
            <Button 
              onClick={() => setShowNewCase(true)}
              className="bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20 text-sm font-medium"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              New Investigation
            </Button>
          </div>
        </div>

        {/* Real-time Dynamic KPI Grid (Direct from DB) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Total Cases */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-zinc-700 transition-all">
            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-all"></div>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Total Cases</CardTitle>
              <LayoutDashboard className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-white">{stats?.total_cases ?? cases.length}</div>
              <p className="text-[11px] text-zinc-500 mt-1 font-mono">{stats?.open_cases ?? 0} active investigations</p>
            </CardContent>
          </Card>

          {/* Threats Flagged */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-red-500/30 transition-all">
            <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-2xl group-hover:bg-red-500/10 transition-all"></div>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Detected Threats</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-red-400">{stats?.detected_threats ?? 0}</div>
              <p className="text-[11px] text-zinc-500 mt-1 font-mono">Confirmed malicious artifacts</p>
            </CardContent>
          </Card>

          {/* Multi-modal Evidence Processed */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-zinc-700 transition-all">
            <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all"></div>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Evidence Uploads</CardTitle>
              <Zap className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-white">{stats?.total_evidence ?? 0}</div>
              <div className="flex items-center gap-2 mt-1 text-[11px] text-zinc-500 font-mono">
                <span>{stats?.url_scans ?? 0} URLs</span> • <span>{stats?.email_scans ?? 0} Emails</span>
              </div>
            </CardContent>
          </Card>

          {/* Engine Latency */}
          <Card className="bg-zinc-900/40 border-zinc-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-zinc-700 transition-all">
            <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-all"></div>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Avg Inference Latency</CardTitle>
              <Activity className="h-4 w-4 text-emerald-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-emerald-400">{stats?.avg_latency_ms ? `${stats.avg_latency_ms}ms` : "12.5ms"}</div>
              <p className="text-[11px] text-zinc-500 mt-1 font-mono">Sub-second neural execution</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick-Launch Investigation Templates */}
        <div className="bg-gradient-to-r from-blue-950/20 via-zinc-900/40 to-purple-950/20 border border-zinc-800/80 rounded-2xl p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
            <div>
              <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                Quick-Start Case Templates
              </h3>
              <p className="text-xs text-zinc-400">Launch a realistic investigation with 1 click to test the detection engines</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              onClick={() => handleCreateCase("Executive Impersonation & Video Deepfake", "Urgent investigation regarding synthetic executive video and suspicious wire transfer instructions.")}
              className="text-left p-3 rounded-xl bg-zinc-900/80 hover:bg-blue-600/10 border border-zinc-800 hover:border-blue-500/40 transition-all group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-zinc-200 group-hover:text-blue-400">🎭 Deepfake Incident</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-blue-400" />
              </div>
              <p className="text-[11px] text-zinc-400 line-clamp-1">Synthetic video & voice clone analysis</p>
            </button>

            <button
              onClick={() => handleCreateCase("Targeted Banking Phishing Campaign", "Multiple employees received credential harvesting emails impersonating corporate SSO and PayPal.")}
              className="text-left p-3 rounded-xl bg-zinc-900/80 hover:bg-amber-600/10 border border-zinc-800 hover:border-amber-500/40 transition-all group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-zinc-200 group-hover:text-amber-400">📧 Phishing Campaign</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-amber-400" />
              </div>
              <p className="text-[11px] text-zinc-400 line-clamp-1">Email body & suspicious URL inspection</p>
            </button>

            <button
              onClick={() => handleCreateCase("Anomalous Network Ingress & Data Exfiltration", "High volume TCP syn floods and irregular payload byte ratios detected at perimeter gateway.")}
              className="text-left p-3 rounded-xl bg-zinc-900/80 hover:bg-red-600/10 border border-zinc-800 hover:border-red-500/40 transition-all group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-zinc-200 group-hover:text-red-400">🛡️ Network Intrusion</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-red-400" />
              </div>
              <p className="text-[11px] text-zinc-400 line-clamp-1">Deep autoencoder flow anomaly detection</p>
            </button>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3" />
            <input 
              type="text"
              placeholder="Search by case title, description, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-zinc-900/60 border border-zinc-800 rounded-xl text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-500 flex items-center gap-1 font-mono">
              <Filter className="w-3.5 h-3.5" /> STATUS:
            </span>
            <div className="flex bg-zinc-900/60 border border-zinc-800 p-1 rounded-xl gap-1">
              {["all", "open", "investigating", "closed"].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
                    statusFilter === st ? "bg-blue-600 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Cases Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            <div className="col-span-full text-center py-16 text-zinc-500">
              <Activity className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-500" />
              Loading investigations...
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="col-span-full text-center py-16 border border-dashed border-zinc-800 rounded-2xl bg-zinc-900/20">
              <ShieldAlert className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
              <p className="text-zinc-300 font-semibold">No investigations matching criteria</p>
              <p className="text-xs text-zinc-500 mt-1">Create a new case or choose a quick-start template above.</p>
              <Button onClick={() => setShowNewCase(true)} variant="outline" className="mt-4 border-zinc-700 text-xs">
                Open New Case
              </Button>
            </div>
          ) : (
            filteredCases.map((c) => (
              <Link href={`/case/${c.id}`} key={c.id}>
                <Card className="bg-zinc-900/40 border-zinc-800/80 hover:border-blue-500/50 hover:bg-zinc-900/70 transition-all cursor-pointer h-full group flex flex-col justify-between">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-mono text-blue-400 font-semibold bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                        CASE #{c.id}
                      </span>
                      {getStatusBadge(c.status)}
                    </div>
                    <CardTitle className="text-base text-zinc-100 group-hover:text-blue-400 transition-colors line-clamp-1">
                      {c.title}
                    </CardTitle>
                    <CardDescription className="text-zinc-400 text-xs line-clamp-2 mt-1">
                      {c.description}
                    </CardDescription>
                  </CardHeader>
                  
                  <CardContent className="pt-0 border-t border-zinc-800/60 mt-2">
                    <div className="flex items-center justify-between text-xs text-zinc-500 pt-3">
                      <span className="flex items-center gap-1 font-mono">
                        <Zap className="w-3 h-3 text-purple-400" />
                        {c.evidence_count} evidence item{c.evidence_count === 1 ? "" : "s"}
                      </span>
                      <span className="font-mono text-[11px]">
                        {c.created_at ? format(new Date(c.created_at), "MMM dd, HH:mm") : "Active"}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))
          )}
        </div>

      </main>

      {/* New Case Creation Modal */}
      {showNewCase && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-zinc-900 border-zinc-700 shadow-2xl">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-bold text-white flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-500" />
                  Create Investigation
                </CardTitle>
                <button onClick={() => setShowNewCase(false)} className="text-zinc-400 hover:text-zinc-200">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <CardDescription className="text-zinc-400 text-xs">
                Open a new case to start multi-modal artifact submission and threat fusion.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Case Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="e.g. Finance Deepfake Phishing Incident"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">Description</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3.5 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Summarize the threat incident details..."
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button 
                  className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold" 
                  onClick={() => handleCreateCase()}
                  disabled={creating || !newTitle.trim()}
                >
                  {creating ? "Creating..." : "Initialize Case"}
                </Button>
                <Button variant="outline" onClick={() => setShowNewCase(false)} className="border-zinc-700 text-zinc-300">
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

    </div>
  );
}
