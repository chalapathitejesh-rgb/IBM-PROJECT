"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, FileText, UserCircle, Activity, Box, ShieldCheck, Scale } from "lucide-react";
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

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center bg-zinc-950 text-zinc-400">Loading forensic records...</div>;
  }

  const getActionIcon = (action: string) => {
    if (action.includes("CREATE")) return <Box className="w-5 h-5 text-emerald-400" />;
    if (action.includes("ANALYZE") || action.includes("SCAN")) return <Activity className="w-5 h-5 text-blue-400" />;
    if (action.includes("FUSION")) return <ShieldCheck className="w-5 h-5 text-indigo-400" />;
    return <FileText className="w-5 h-5 text-zinc-400" />;
  };

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950">
      <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md">
        <div className="flex h-16 items-center px-6 gap-4">
          <Link href={`/case/${id}`} className="text-zinc-400 hover:text-zinc-50 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-2 border-l border-zinc-800 pl-4">
            <Scale className="h-6 w-6 text-emerald-500" />
            <span className="text-lg font-bold text-zinc-50">Digital Forensics Log</span>
          </div>
        </div>
      </header>

      <main className="flex-1 p-8">
        <div className="mx-auto max-w-4xl space-y-8">
          
          <div className="flex items-center justify-between border-b border-zinc-800 pb-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-zinc-50">Chain of Custody</h1>
              <p className="text-zinc-400 mt-1">Cryptographic audit log for Case #{id}: {forensics?.title}</p>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-center">
              <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Total Events</p>
              <p className="text-2xl font-bold text-emerald-400">{forensics?.total_events || 0}</p>
            </div>
          </div>

          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle>Audit Trail</CardTitle>
              <CardDescription>Immutable record of all evidence handling and AI processing.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative border-l border-zinc-800 ml-3 pl-6 space-y-8 mt-4">
                {forensics?.chain_of_custody?.length === 0 ? (
                  <p className="text-zinc-500 py-4">No events recorded.</p>
                ) : (
                  forensics?.chain_of_custody?.map((log: any, idx: number) => (
                    <div key={idx} className="relative">
                      {/* Timeline Dot */}
                      <span className="absolute -left-[35px] bg-zinc-950 border-2 border-zinc-800 p-1.5 rounded-full z-10 ring-4 ring-zinc-950">
                        {getActionIcon(log.action)}
                      </span>
                      
                      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-colors">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                          <h3 className="font-semibold text-zinc-200 uppercase tracking-wide text-sm">{log.action.replace(/_/g, ' ')}</h3>
                          <span className="text-xs font-mono text-zinc-500 bg-zinc-950 px-2 py-1 rounded">
                            {format(new Date(log.timestamp + 'Z'), 'yyyy-MM-dd HH:mm:ss.SSS')} UTC
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                          <div className="space-y-1">
                            <span className="text-zinc-500 text-xs uppercase tracking-wider">Actor</span>
                            <div className="flex items-center gap-1.5 text-zinc-300">
                              <UserCircle className="w-4 h-4 text-blue-400" />
                              {log.user}
                            </div>
                          </div>
                          
                          <div className="space-y-1">
                            <span className="text-zinc-500 text-xs uppercase tracking-wider">Target Entity</span>
                            <div className="flex items-center gap-1.5 text-zinc-300 font-mono">
                              <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-xs">{log.target_type}</span>
                              #{log.target_id}
                            </div>
                          </div>
                        </div>
                        
                        {log.details && (
                          <div className="mt-4 pt-3 border-t border-zinc-800/50">
                            <p className="text-sm text-zinc-400">{log.details}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
}
