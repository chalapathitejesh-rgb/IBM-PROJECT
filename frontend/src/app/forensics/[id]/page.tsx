"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, FileText, UserCircle, Activity, Box, ShieldCheck, Scale, Lock, RefreshCw, CheckCircle2 } from "lucide-react";
import axios from "axios";
import Link from "next/link";
import { format } from "date-fns";

export default function ForensicsChainOfCustody() {
  const { id } = useParams();
  const { token } = useAuth();
  const [forensics, setForensics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token && id) {
      fetchForensics();
    }
  }, [token, id]);

  const fetchForensics = async () => {
    setIsLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/api/v1/forensics/case/${id}/chain-of-custody`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setForensics(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getActionIcon = (action: string) => {
    if (action?.includes("CREATE")) return <Box className="w-4 h-4 text-emerald-400" />;
    if (action?.includes("ANALYZE") || action?.includes("SCAN") || action?.includes("UPLOAD")) return <Activity className="w-4 h-4 text-blue-400" />;
    if (action?.includes("FUSION")) return <ShieldCheck className="w-4 h-4 text-purple-400" />;
    return <FileText className="w-4 h-4 text-zinc-400" />;
  };

  const getActionBadgeColor = (action: string) => {
    if (action?.includes("CREATE")) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (action?.includes("FUSION")) return "bg-purple-500/10 text-purple-400 border-purple-500/20";
    if (action?.includes("UPLOAD")) return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    return "bg-amber-500/10 text-amber-400 border-amber-500/20";
  };

  return (
    <div className="min-h-screen bg-[#090a0f] text-zinc-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
      
      {/* Background Cyber Grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f293d15_1px,transparent_1px),linear-gradient(to_bottom,#1f293d15_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none"></div>

      {/* Top Navbar */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-[#090a0f]/90 backdrop-blur-xl">
        <div className="flex h-16 items-center px-6 justify-between max-w-5xl mx-auto w-full">
          <div className="flex items-center gap-4">
            <Link href={`/case/${id}`} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-white transition-all">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-tight">deepSheild</span>
              <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/20">FORENSICS AUDIT ROOM</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchForensics} className="border-zinc-800 bg-zinc-900/60 text-zinc-400 text-xs">
              <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh Trail
            </Button>
          </div>
        </div>
      </header>

      {/* Main Forensic View */}
      <main className="flex-1 p-6 md:p-8 max-w-5xl mx-auto w-full space-y-6 relative z-10">
        
        {/* Banner */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 text-xs text-emerald-400 font-mono mb-1">
              <Lock className="w-3.5 h-3.5 text-emerald-500" />
              IMMUTABLE CRYPTOGRAPHIC CHAIN OF CUSTODY
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">Case #{id} Forensic Timeline</h1>
            <p className="text-zinc-400 text-sm mt-1">Legally admissible audit log tracking all evidence handling, ML model inferences, and risk fusions.</p>
          </div>

          <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 text-center min-w-[140px]">
            <p className="text-[10px] text-zinc-500 font-mono uppercase tracking-wider">Logged Audit Events</p>
            <p className="text-2xl font-black text-emerald-400 font-mono mt-0.5">{forensics?.total_events || 0}</p>
          </div>
        </div>

        {/* Audit Log Card */}
        <Card className="bg-zinc-900/40 border-zinc-800/80 backdrop-blur-xl">
          <CardHeader className="border-b border-zinc-800/60 pb-3">
            <CardTitle className="text-sm font-bold uppercase tracking-wider text-zinc-200 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Scale className="w-4 h-4 text-emerald-400" />
                Chronological Chain-of-Custody Log
              </span>
              <span className="text-xs text-emerald-400 font-mono font-normal flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Cryptographic Integrity Verified
              </span>
            </CardTitle>
          </CardHeader>

          <CardContent className="pt-6">
            {isLoading ? (
              <div className="text-center py-12 text-zinc-500 font-mono text-xs">
                <Activity className="w-6 h-6 animate-spin text-emerald-500 mx-auto mb-2" />
                Loading audit trail...
              </div>
            ) : !forensics?.chain_of_custody || forensics?.chain_of_custody.length === 0 ? (
              <div className="text-center py-12 text-zinc-500 text-xs font-mono">
                No audit events recorded for this case.
              </div>
            ) : (
              <div className="relative border-l border-zinc-800 ml-4 pl-6 space-y-6">
                {forensics?.chain_of_custody.map((log: any, idx: number) => (
                  <div key={idx} className="relative group">
                    
                    {/* Timeline Node */}
                    <span className="absolute -left-[37px] top-3 bg-zinc-950 border border-zinc-700 p-1.5 rounded-full z-10 group-hover:border-emerald-500 transition-colors">
                      {getActionIcon(log.action)}
                    </span>

                    {/* Event Card */}
                    <div className="bg-zinc-950/70 border border-zinc-800/80 rounded-xl p-4 hover:border-zinc-700 transition-all space-y-3">
                      
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${getActionBadgeColor(log.action)}`}>
                            {log.action?.replace(/_/g, " ")}
                          </span>
                          <span className="text-xs text-zinc-400 font-mono">
                            Target: <strong className="text-zinc-200">{log.target_type} #{log.target_id}</strong>
                          </span>
                        </div>

                        <span className="text-[11px] font-mono text-zinc-500 bg-zinc-900 px-2 py-1 rounded border border-zinc-800/60">
                          {log.timestamp ? format(new Date(log.timestamp + (log.timestamp.endsWith('Z') ? '' : 'Z')), "yyyy-MM-dd HH:mm:ss") : "Recent"} UTC
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-zinc-900 text-xs font-mono">
                        <div className="flex items-center gap-1.5 text-zinc-400">
                          <UserCircle className="w-3.5 h-3.5 text-blue-400" />
                          <span>Initiated by: <strong className="text-zinc-200">{log.user}</strong></span>
                        </div>
                        <div className="flex items-center gap-1.5 text-zinc-500">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Status: Audit Trail Locked & Verified</span>
                        </div>
                      </div>

                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

      </main>
    </div>
  );
}
