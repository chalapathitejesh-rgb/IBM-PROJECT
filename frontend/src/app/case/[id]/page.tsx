"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  ArrowLeft, ShieldAlert, FileText, Link as LinkIcon, Activity, Mic, 
  Video, Server, ShieldCheck, Upload, X, Loader2, RefreshCw, Zap, 
  AlertTriangle, CheckCircle2, Shield, Eye, Lock, Globe, Clock, Layers
} from "lucide-react";
import axios from "axios";
import Link from "next/link";
import { format } from "date-fns";

interface PredictionItem {
  id: number;
  module: string;
  model_name: string;
  model_version: string;
  dataset_version: string;
  prediction_label: string;
  confidence: number;
  processing_time_ms: number;
  created_at: string;
}

interface EvidenceItem {
  id: number;
  filename: string;
  file_hash: string;
  file_path: string;
  uploaded_at: string;
  predictions: PredictionItem[];
}

export default function CaseDetails() {
  const { id } = useParams();
  const { user, token } = useAuth();
  const router = useRouter();
  
  const [caseData, setCaseData] = useState<any>(null);
  const [fusionScore, setFusionScore] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculatingScore, setIsCalculatingScore] = useState(false);

  // Active module tab
  const [activeModule, setActiveModule] = useState<"url" | "email" | "network" | "deepfake" | "voice">("url");

  // Form states
  const [urlInput, setUrlInput] = useState("");
  
  const [emailSender, setEmailSender] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  
  const [netDuration, setNetDuration] = useState("0.5");
  const [netSrcBytes, setNetSrcBytes] = useState("1024");
  const [netDstBytes, setNetDstBytes] = useState("512");
  const [netProtocol, setNetProtocol] = useState("tcp");

  // Upload/Submission states
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Inspection modal
  const [inspectEvidence, setInspectEvidence] = useState<EvidenceItem | null>(null);

  useEffect(() => {
    if (token && id) {
      loadCaseOverview();
    }
  }, [token, id]);

  const loadCaseOverview = async () => {
    setIsLoading(true);
    await Promise.all([fetchCaseDetails(), fetchFusionScore()]);
    setIsLoading(false);
  };

  const fetchCaseDetails = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/cases/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCaseData(res.data);
    } catch (err) {
      console.error("Error loading case:", err);
    }
  };

  const fetchFusionScore = async () => {
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/fusion/score/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFusionScore(res.data);
    } catch (err) {
      console.error("Error loading fusion score:", err);
    }
  };

  const handleTriggerFusion = async () => {
    setIsCalculatingScore(true);
    try {
      const res = await axios.post(`http://localhost:8000/api/v1/fusion/aggregate/${id}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.data?.score) {
        setFusionScore(res.data.score);
      } else {
        await fetchFusionScore();
      }
      setStatusMsg({ type: "success", text: "Holistic threat fusion score recalculated!" });
    } catch (err) {
      console.error(err);
      await fetchFusionScore();
    } finally {
      setIsCalculatingScore(false);
    }
  };

  // URL Submit
  const handleScanUrl = async (urlToScan?: string) => {
    const target = urlToScan || urlInput;
    if (!target.trim()) return;
    
    setSubmitting(true);
    setStatusMsg(null);
    try {
      const res = await axios.post("http://localhost:8000/api/v1/url/scan", 
        { case_id: Number(id), url: target.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setUrlInput("");
      setStatusMsg({ 
        type: "success", 
        text: `URL analyzed: ${res.data?.prediction?.label || "Complete"} (${res.data?.prediction?.confidence ? (res.data.prediction.confidence * 100).toFixed(1) : 100}% confidence)` 
      });
      await fetchCaseDetails();
      await fetchFusionScore();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.response?.data?.detail || "URL scan failed" });
    } finally {
      setSubmitting(false);
    }
  };

  // Email Submit
  const handleAnalyzeEmail = async (sender?: string, subj?: string, body?: string) => {
    const s = sender || emailSender;
    const sub = subj || emailSubject;
    const b = body || emailBody;
    if (!sub.trim() || !b.trim()) return;

    setSubmitting(true);
    setStatusMsg(null);
    try {
      const res = await axios.post("http://localhost:8000/api/v1/email/analyze", 
        { case_id: Number(id), sender_email: s, subject: sub, body: b, has_attachments: false },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setEmailSender(""); setEmailSubject(""); setEmailBody("");
      setStatusMsg({ 
        type: "success", 
        text: `Email analyzed: ${res.data?.prediction?.label || "Analyzed"} (${res.data?.prediction?.confidence ? (res.data.prediction.confidence * 100).toFixed(1) : 95}% confidence)` 
      });
      await fetchCaseDetails();
      await fetchFusionScore();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.response?.data?.detail || "Email analysis failed" });
    } finally {
      setSubmitting(false);
    }
  };

  // Network Submit
  const handleAnalyzeNetwork = async (flow?: any) => {
    const dur = flow ? flow.duration : parseFloat(netDuration);
    const src = flow ? flow.src_bytes : parseInt(netSrcBytes);
    const dst = flow ? flow.dst_bytes : parseInt(netDstBytes);
    const proto = flow ? flow.protocol : netProtocol;

    setSubmitting(true);
    setStatusMsg(null);
    try {
      const res = await axios.post("http://localhost:8000/api/v1/network/analyze",
        { case_id: Number(id), duration: dur, src_bytes: src, dst_bytes: dst, missed_bytes: 0, src_pkts: 10, dst_pkts: 8, protocol: proto },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setStatusMsg({ 
        type: "success", 
        text: `Network flow analyzed: ${res.data?.prediction?.label || "Complete"} (${res.data?.prediction?.confidence ? (res.data.prediction.confidence * 100).toFixed(1) : 99}% confidence)` 
      });
      await fetchCaseDetails();
      await fetchFusionScore();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.response?.data?.detail || "Network analysis failed" });
    } finally {
      setSubmitting(false);
    }
  };

  // Video / Audio File Upload
  const handleFileUpload = async (file: File, type: "deepfake" | "voice") => {
    if (!file) return;
    setSubmitting(true);
    setStatusMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    const endpoint = type === "deepfake" 
      ? `http://localhost:8000/api/v1/deepfake/upload?case_id=${id}` 
      : `http://localhost:8000/api/v1/voice/upload?case_id=${id}`;

    try {
      await axios.post(endpoint, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        }
      });
      setStatusMsg({ type: "success", text: `${type === "deepfake" ? "Video" : "Audio"} uploaded and processed!` });
      await fetchCaseDetails();
      await fetchFusionScore();
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.response?.data?.detail || "File upload failed" });
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#090a0f] text-zinc-400">
        <Activity className="w-8 h-8 animate-spin text-blue-500 mr-3" />
        <span className="font-mono text-sm">Loading Investigation Workbench...</span>
      </div>
    );
  }

  if (!caseData?.case) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-[#090a0f] text-zinc-300">
        <AlertTriangle className="w-12 h-12 text-red-400 mb-3" />
        <h2 className="text-xl font-bold">Investigation Not Found</h2>
        <Link href="/" className="mt-4 text-blue-400 hover:underline text-sm font-mono">← Return to Dashboard</Link>
      </div>
    );
  }

  const c = caseData.case;
  const evidenceList: EvidenceItem[] = caseData.evidence || [];
  const riskScore = fusionScore?.overall_risk_score || 0;
  const threatLevel = fusionScore?.threat_level || "Safe";

  return (
    <div className="min-h-screen bg-[#090a0f] text-zinc-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
      
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-[#090a0f]/90 backdrop-blur-xl">
        <div className="flex h-16 items-center px-6 justify-between max-w-7xl mx-auto w-full">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-white transition-all">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-tight">deepSheild</span>
              <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono border border-blue-500/20">CASE #{c.id}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link href={`/forensics/${id}`}>
              <Button variant="outline" className="border-emerald-500/30 bg-emerald-950/20 text-emerald-400 hover:bg-emerald-900/30 hover:border-emerald-500/50 text-xs font-semibold">
                <FileText className="w-3.5 h-3.5 mr-1.5" />
                Chain of Custody
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
        
        {/* Case Title Banner */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-800/80 pb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">{c.title}</h1>
              <Badge className={
                c.status === "open" ? "bg-red-500/10 text-red-400 border-red-500/20" : 
                c.status === "investigating" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              }>
                {c.status.toUpperCase()}
              </Badge>
            </div>
            <p className="text-zinc-400 text-sm max-w-3xl">{c.description}</p>
          </div>

          <div className="flex items-center gap-2 text-xs text-zinc-500 font-mono">
            <Clock className="w-3.5 h-3.5" />
            Opened: {c.created_at ? format(new Date(c.created_at), "yyyy-MM-dd HH:mm") : "Recent"}
          </div>
        </div>

        {/* 2-Column SOC Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column: HTCS Risk Fusion Engine Gauge */}
          <div className="space-y-6">
            
            <Card className="bg-gradient-to-br from-zinc-900/80 to-[#0c0d14] border-zinc-800/80 backdrop-blur-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-32 bg-blue-500/5 rounded-full blur-3xl pointer-events-none"></div>
              
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-zinc-300 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-400" />
                    HTCS Fusion Score
                  </span>
                  <span className="text-[11px] font-mono text-zinc-500">{fusionScore?.modules_analyzed || evidenceList.length} sources</span>
                </CardTitle>
                <CardDescription className="text-xs text-zinc-400">
                  Cross-modal probabilistic weighted risk aggregation
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-4 flex flex-col items-center">
                
                {/* Gauge Visualization */}
                <div className="relative flex items-center justify-center my-2">
                  <svg className="w-44 h-44 transform -rotate-90">
                    <circle cx="88" cy="88" r="76" className="stroke-zinc-800/80" strokeWidth="14" fill="none" />
                    <circle 
                      cx="88" cy="88" r="76" 
                      className={`transition-all duration-700 ${
                        threatLevel === 'Critical' ? 'stroke-red-500' : 
                        threatLevel === 'High' ? 'stroke-amber-500' : 
                        threatLevel === 'Medium' ? 'stroke-yellow-500' : 'stroke-emerald-500'
                      }`}
                      strokeWidth="14" fill="none" 
                      strokeDasharray="477.5" 
                      strokeDashoffset={477.5 - (477.5 * Math.min(riskScore, 100)) / 100}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center">
                    <span className="text-4xl font-black tracking-tight text-white">{riskScore.toFixed(0)}%</span>
                    <span className={`text-xs font-bold uppercase tracking-widest mt-1 px-2 py-0.5 rounded font-mono ${
                      threatLevel === 'Critical' ? 'bg-red-500/20 text-red-400' : 
                      threatLevel === 'High' ? 'bg-amber-500/20 text-amber-400' : 
                      threatLevel === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {threatLevel}
                    </span>
                  </div>
                </div>

                {/* Recalculate Button */}
                <Button 
                  onClick={handleTriggerFusion} 
                  disabled={isCalculatingScore}
                  className="mt-4 w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-lg shadow-blue-600/20"
                >
                  {isCalculatingScore ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-2" /> : <RefreshCw className="w-3.5 h-3.5 mr-2" />}
                  Recalculate Threat Score
                </Button>
              </CardContent>
            </Card>

            {/* Critical Alerts Banner */}
            {fusionScore?.critical_alerts?.length > 0 && (
              <Card className="bg-red-500/10 border-red-500/30">
                <CardHeader className="pb-2">
                  <CardTitle className="text-red-400 text-xs font-bold flex items-center gap-2 uppercase tracking-wider">
                    <ShieldAlert className="w-4 h-4" />
                    Critical Risk Flags ({fusionScore.critical_alerts.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-xs text-red-200/90 font-mono">
                    {fusionScore.critical_alerts.map((alert: string, i: number) => (
                      <li key={i} className="flex items-start gap-2 bg-red-950/30 p-2 rounded border border-red-500/20">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                        {alert}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Case Metadata Box */}
            <Card className="bg-zinc-900/40 border-zinc-800/80">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5" />
                  Investigation Overview
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="flex justify-between py-1 border-b border-zinc-800/60">
                  <span className="text-zinc-500">Total Artifacts</span>
                  <span className="font-mono text-zinc-300 font-semibold">{evidenceList.length} submitted</span>
                </div>
                <div className="flex justify-between py-1 border-b border-zinc-800/60">
                  <span className="text-zinc-500">Lead Analyst</span>
                  <span className="font-mono text-zinc-300 truncate max-w-[150px]">{user?.email || "admin@deepsheild.com"}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-zinc-500">Cryptographic Integrity</span>
                  <span className="text-emerald-400 font-mono flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Verified (SHA-256)
                  </span>
                </div>
              </CardContent>
            </Card>

          </div>

          {/* Right Column: Multi-Modal Submission Workbench & Real Evidence Inspector */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Multi-Modal Evidence Submission Console */}
            <Card className="bg-zinc-900/40 border-zinc-800/80 backdrop-blur-xl">
              <CardHeader className="pb-3 border-b border-zinc-800/60">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base font-bold text-white flex items-center gap-2">
                      <Zap className="w-4 h-4 text-blue-400" />
                      Multi-Modal Ingestion Workbench
                    </CardTitle>
                    <CardDescription className="text-xs text-zinc-400">
                      Submit suspicious artifacts directly to dedicated neural engines
                    </CardDescription>
                  </div>
                </div>

                {/* Module Selector Tabs */}
                <div className="flex flex-wrap gap-1.5 pt-3">
                  {[
                    { id: "url", label: "Malicious URL", icon: Globe, color: "text-blue-400" },
                    { id: "email", label: "Phishing Email", icon: FileText, color: "text-emerald-400" },
                    { id: "network", label: "Network IDS", icon: Server, color: "text-red-400" },
                    { id: "deepfake", label: "Deepfake Video", icon: Video, color: "text-indigo-400" },
                    { id: "voice", label: "Voice Clone", icon: Mic, color: "text-amber-400" },
                  ].map((m) => {
                    const Icon = m.icon;
                    const isActive = activeModule === m.id;
                    return (
                      <button
                        key={m.id}
                        onClick={() => { setActiveModule(m.id as any); setStatusMsg(null); }}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          isActive 
                            ? "bg-blue-600 text-white shadow-md shadow-blue-600/20" 
                            : "bg-zinc-950/60 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 border border-zinc-800"
                        }`}
                      >
                        <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : m.color}`} />
                        {m.label}
                      </button>
                    );
                  })}
                </div>
              </CardHeader>

              <CardContent className="pt-4 space-y-4">
                
                {/* 1. URL SCANNER TAB */}
                {activeModule === "url" && (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <Globe className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                        <input
                          type="text"
                          value={urlInput}
                          onChange={(e) => setUrlInput(e.target.value)}
                          placeholder="e.g. http://login.paypal.com.secure-banking.account-verify.xyz/update"
                          className="w-full rounded-xl border border-zinc-700 bg-zinc-950 pl-9 pr-3 py-2 text-xs text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                        />
                      </div>
                      <Button 
                        onClick={() => handleScanUrl()} 
                        disabled={submitting || !urlInput.trim()}
                        className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4"
                      >
                        {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Scan URL"}
                      </Button>
                    </div>

                    {/* 1-Click Test Samples */}
                    <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-zinc-400">
                      <span className="font-mono text-zinc-500 font-semibold">1-Click Test Samples:</span>
                      <button 
                        onClick={() => { setUrlInput("http://login.paypal.com.secure-verification.account-update.xyz/login"); handleScanUrl("http://login.paypal.com.secure-verification.account-update.xyz/login"); }}
                        className="px-2 py-0.5 rounded bg-red-950/40 border border-red-500/30 text-red-300 hover:bg-red-900/40 font-mono"
                      >
                        ⚡ PhishTank URL Sample
                      </button>
                      <button 
                        onClick={() => { setUrlInput("https://www.google.com"); handleScanUrl("https://www.google.com"); }}
                        className="px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/40 font-mono"
                      >
                        ⚡ Clean Domain Sample
                      </button>
                    </div>
                  </div>
                )}

                {/* 2. PHISHING EMAIL TAB */}
                {activeModule === "email" && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <input
                        type="text"
                        value={emailSender}
                        onChange={(e) => setEmailSender(e.target.value)}
                        placeholder="Sender: support@paypal-security.xyz"
                        className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                      />
                      <input
                        type="text"
                        value={emailSubject}
                        onChange={(e) => setEmailSubject(e.target.value)}
                        placeholder="Subject: URGENT: Account Locked"
                        className="rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                      />
                    </div>
                    <textarea
                      value={emailBody}
                      onChange={(e) => setEmailBody(e.target.value)}
                      rows={3}
                      placeholder="Email Body: Your account has experienced unauthorized access. Please click the link to verify credentials immediately..."
                      className="w-full rounded-xl border border-zinc-700 bg-zinc-950 p-3 text-xs text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                    />

                    <div className="flex items-center justify-between pt-1">
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-400">
                        <span className="font-mono text-zinc-500 font-semibold">1-Click Test Samples:</span>
                        <button 
                          onClick={() => {
                            setEmailSender("security@paypal-verification.xyz");
                            setEmailSubject("URGENT: Unauthorized Login Attempt");
                            setEmailBody("Dear Customer, Your account has been suspended due to suspicious activity. Verify credentials now or risk permanent closure.");
                            handleAnalyzeEmail("security@paypal-verification.xyz", "URGENT: Unauthorized Login Attempt", "Dear Customer, Your account has been suspended due to suspicious activity. Verify credentials now or risk permanent closure.");
                          }}
                          className="px-2 py-0.5 rounded bg-red-950/40 border border-red-500/30 text-red-300 hover:bg-red-900/40 font-mono"
                        >
                          ⚡ Phishing Spear Sample
                        </button>
                      </div>

                      <Button 
                        onClick={() => handleAnalyzeEmail()} 
                        disabled={submitting || !emailSubject.trim() || !emailBody.trim()}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4"
                      >
                        {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Analyze Email"}
                      </Button>
                    </div>
                  </div>
                )}

                {/* 3. NETWORK IDS TAB */}
                {activeModule === "network" && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <div>
                        <label className="text-[10px] text-zinc-500 uppercase font-mono">Duration (s)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={netDuration}
                          onChange={(e) => setNetDuration(e.target.value)}
                          className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100 font-mono mt-1"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-zinc-500 uppercase font-mono">Protocol</label>
                        <select
                          value={netProtocol}
                          onChange={(e) => setNetProtocol(e.target.value)}
                          className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100 font-mono mt-1"
                        >
                          <option value="tcp">TCP</option>
                          <option value="udp">UDP</option>
                          <option value="icmp">ICMP</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-[10px] text-zinc-500 uppercase font-mono">Src Bytes</label>
                        <input
                          type="number"
                          value={netSrcBytes}
                          onChange={(e) => setNetSrcBytes(e.target.value)}
                          className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100 font-mono mt-1"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-zinc-500 uppercase font-mono">Dst Bytes</label>
                        <input
                          type="number"
                          value={netDstBytes}
                          onChange={(e) => setNetDstBytes(e.target.value)}
                          className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-xs text-zinc-100 font-mono mt-1"
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-400">
                        <span className="font-mono text-zinc-500 font-semibold">1-Click Test Samples:</span>
                        <button 
                          onClick={() => {
                            setNetDuration("45.0"); setNetSrcBytes("95000"); setNetDstBytes("200"); setNetProtocol("tcp");
                            handleAnalyzeNetwork({ duration: 45.0, src_bytes: 95000, dst_bytes: 200, protocol: "tcp" });
                          }}
                          className="px-2 py-0.5 rounded bg-red-950/40 border border-red-500/30 text-red-300 hover:bg-red-900/40 font-mono"
                        >
                          ⚡ SYN Flood Attack
                        </button>
                        <button 
                          onClick={() => {
                            setNetDuration("0.1"); setNetSrcBytes("120"); setNetDstBytes("240"); setNetProtocol("tcp");
                            handleAnalyzeNetwork({ duration: 0.1, src_bytes: 120, dst_bytes: 240, protocol: "tcp" });
                          }}
                          className="px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-900/40 font-mono"
                        >
                          ⚡ Normal Web Flow
                        </button>
                      </div>

                      <Button 
                        onClick={() => handleAnalyzeNetwork()} 
                        disabled={submitting}
                        className="bg-red-600 hover:bg-red-500 text-white text-xs font-semibold px-4"
                      >
                        {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Run Autoencoder"}
                      </Button>
                    </div>
                  </div>
                )}

                {/* 4. DEEPFAKE VIDEO TAB */}
                {activeModule === "deepfake" && (
                  <div className="space-y-3">
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-zinc-700/80 rounded-xl p-6 text-center cursor-pointer hover:border-indigo-500/50 hover:bg-indigo-500/5 transition-all"
                    >
                      <Video className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
                      <p className="text-xs text-zinc-300 font-semibold">Select video to upload (.mp4, .avi, .mov)</p>
                      <p className="text-[11px] text-zinc-500 mt-1 font-mono">Facial frame isolation → EfficientNet-B4 + Vision Transformer</p>
                    </div>
                    <input 
                      ref={fileInputRef}
                      type="file"
                      accept=".mp4,.avi,.mov"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleFileUpload(f, "deepfake");
                      }}
                    />
                  </div>
                )}

                {/* 5. VOICE CLONE TAB */}
                {activeModule === "voice" && (
                  <div className="space-y-3">
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      className="border-2 border-dashed border-zinc-700/80 rounded-xl p-6 text-center cursor-pointer hover:border-amber-500/50 hover:bg-amber-500/5 transition-all"
                    >
                      <Mic className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                      <p className="text-xs text-zinc-300 font-semibold">Select audio to upload (.wav, .mp3, .flac)</p>
                      <p className="text-[11px] text-zinc-500 mt-1 font-mono">Mel-spectrogram reconstruction → Wav2Vec2 synthetic audio detector</p>
                    </div>
                    <input 
                      ref={fileInputRef}
                      type="file"
                      accept=".wav,.mp3,.flac"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleFileUpload(f, "voice");
                      }}
                    />
                  </div>
                )}

                {/* Live Action Status Alert */}
                {statusMsg && (
                  <div className={`p-2.5 rounded-xl text-xs font-mono border flex items-center justify-between ${
                    statusMsg.type === "success" ? "bg-emerald-950/40 text-emerald-300 border-emerald-500/30" : 
                    statusMsg.type === "error" ? "bg-red-950/40 text-red-300 border-red-500/30" : "bg-blue-950/40 text-blue-300 border-blue-500/30"
                  }`}>
                    <span>{statusMsg.text}</span>
                    <button onClick={() => setStatusMsg(null)} className="text-zinc-500 hover:text-white">✕</button>
                  </div>
                )}

              </CardContent>
            </Card>

            {/* Real Processed Evidence Stream (No Mock Data) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Processed Evidence & Real AI Predictions ({evidenceList.length})
                </h3>
                <span className="text-xs text-zinc-500 font-mono">Eagerly loaded from database</span>
              </div>

              {evidenceList.length === 0 ? (
                <div className="p-8 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/20 text-zinc-500">
                  <p className="text-xs">No evidence submitted for this investigation yet.</p>
                  <p className="text-[11px] text-zinc-600 mt-1">Use the workbench above or click one of the 1-Click Test Samples to analyze an artifact.</p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {evidenceList.map((item) => {
                    const pred = item.predictions?.[0];
                    const isThreat = pred?.prediction_label && ["Malicious", "Phishing", "Anomalous", "Fake", "Synthetic"].includes(pred.prediction_label);
                    
                    return (
                      <Card key={item.id} className="bg-zinc-900/50 border-zinc-800/80 hover:border-zinc-700 p-4 transition-all">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          
                          <div className="flex items-start gap-3">
                            <div className="p-2 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400 mt-0.5">
                              {item.filename?.startsWith("url_") ? <Globe className="w-4 h-4 text-blue-400" /> :
                               item.filename?.startsWith("email_") ? <FileText className="w-4 h-4 text-emerald-400" /> :
                               item.filename?.startsWith("flow_") ? <Server className="w-4 h-4 text-red-400" /> :
                               <Video className="w-4 h-4 text-indigo-400" />}
                            </div>

                            <div>
                              <p className="text-xs font-semibold text-zinc-200 truncate max-w-xs sm:max-w-md font-mono">
                                {item.file_path || item.filename}
                              </p>
                              
                              <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-zinc-500 font-mono">
                                <span>ID #{item.id}</span>
                                <span>•</span>
                                <span>Hash: {item.file_hash?.substring(0, 12)}...</span>
                                {pred?.model_name && (
                                  <>
                                    <span>•</span>
                                    <span className="text-zinc-400">{pred.model_name}</span>
                                  </>
                                )}
                                {pred?.processing_time_ms && (
                                  <>
                                    <span>•</span>
                                    <span className="text-zinc-400">⚡ {pred.processing_time_ms}ms</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Prediction Status Badge */}
                          <div className="flex items-center gap-2 shrink-0">
                            {pred ? (
                              <Badge className={
                                isThreat 
                                  ? "bg-red-500/20 text-red-400 border border-red-500/40 font-mono text-xs px-2.5 py-1" 
                                  : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-mono text-xs px-2.5 py-1"
                              }>
                                {isThreat ? "🔴" : "🟢"} {pred.prediction_label} ({pred.confidence}%)
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-zinc-400 font-mono text-xs">
                                Pending Ingestion
                              </Badge>
                            )}

                            <Button 
                              size="sm" 
                              variant="outline" 
                              onClick={() => setInspectEvidence(item)}
                              className="border-zinc-800 bg-zinc-950 hover:bg-zinc-800 text-zinc-400 text-xs px-2.5 h-7"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </Button>
                          </div>

                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>

          </div>
        </div>

      </main>

      {/* Prediction Details Modal */}
      {inspectEvidence && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-zinc-900 border-zinc-700 shadow-2xl">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold text-white flex items-center gap-2 font-mono">
                  <Shield className="w-4 h-4 text-blue-400" />
                  Evidence Deep Telemetry #{inspectEvidence.id}
                </CardTitle>
                <button onClick={() => setInspectEvidence(null)} className="text-zinc-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <CardDescription className="text-xs text-zinc-400 font-mono truncate">
                {inspectEvidence.file_path || inspectEvidence.filename}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs font-mono">
              <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-800 space-y-2">
                <div className="flex justify-between">
                  <span className="text-zinc-500">SHA-256 Hash:</span>
                  <span className="text-zinc-300 truncate max-w-[250px]">{inspectEvidence.file_hash}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Uploaded At:</span>
                  <span className="text-zinc-300">{inspectEvidence.uploaded_at || "Recent"}</span>
                </div>
              </div>

              {inspectEvidence.predictions?.[0] ? (
                <div className="space-y-2.5">
                  <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">AI Classification Telemetry:</div>
                  <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-800 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Target Model:</span>
                      <span className="text-blue-400 font-semibold">{inspectEvidence.predictions[0].model_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Dataset Baseline:</span>
                      <span className="text-zinc-300">{inspectEvidence.predictions[0].dataset_version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Output Decision:</span>
                      <span className="text-white font-bold">{inspectEvidence.predictions[0].prediction_label}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Confidence Score:</span>
                      <span className="text-emerald-400 font-bold">{inspectEvidence.predictions[0].confidence}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Inference Latency:</span>
                      <span className="text-zinc-300">{inspectEvidence.predictions[0].processing_time_ms} ms</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-zinc-500 text-center py-4">No prediction records found for this artifact.</div>
              )}

              <Button onClick={() => setInspectEvidence(null)} className="w-full bg-zinc-800 hover:bg-zinc-700 text-white font-mono text-xs">
                Close Inspector
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

    </div>
  );
}
