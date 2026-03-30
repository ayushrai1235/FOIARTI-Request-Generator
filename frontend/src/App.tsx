import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, FileText, CheckCircle2, Clock, CheckCircle, Loader2, Download, Table, CalendarClock } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

interface RequestData {
  id: string;
  agency_key: string;
  agency_name: string;
  jurisdiction: string;
  subject: string;
  requester_name: string;
  date_sent: string;
  response_due: string;
  status: 'SENT' | 'RESPONDED' | 'OVERDUE' | 'CLOSED' | 'FOLLOWED_UP';
  output_file: string;
  n8n_notified: number;
}

interface AgencyConfig {
  full_name: string;
  jurisdiction: string;
  foia_officer: string;
  foia_email: string;
  mailing_address: string;
  city_state_zip: string;
  online_portal: string;
}

interface StatuteConfig {
  law_name: string;
  short_name: string;
  citation: string;
  fee_waiver_citation: string;
  exemption_citation: string;
  response_days: number;
  response_day_type: string;
  letter_prefix: string;
  template: string;
  application_fee?: string;
  application_fee_currency?: string;
}

export default function App() {
  const [requests, setRequests] = useState<RequestData[]>([]);
  const [agenciesConfig, setAgenciesConfig] = useState<Record<string, AgencyConfig>>({});
  const [statutesConfig, setStatutesConfig] = useState<Record<string, StatuteConfig>>({});
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [formData, setFormData] = useState({
    agency: '',
    jurisdiction: '',
    records: '',
    name: '',
    email: '',
    pdf: false
  });
  const [selectedRequest, setSelectedRequest] = useState<RequestData | null>(null);

  useEffect(() => {
    fetchConfig();
    fetchRequests();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API_BASE}/config`);
      const agencies = res.data.agencies || {};
      const statutes = res.data.statutes || {};
      setAgenciesConfig(agencies);
      setStatutesConfig(statutes);
      
      const firstAgencyKey = Object.keys(agencies)[0] || '';
      setFormData(prev => ({
        ...prev,
        agency: firstAgencyKey,
        jurisdiction: agencies[firstAgencyKey]?.jurisdiction || ''
      }));
    } catch (err) {
      console.error("Failed to fetch config", err);
    }
  };

  const fetchRequests = async () => {
    try {
      const res = await axios.get(`${API_BASE}/requests`);
      setRequests(res.data);
    } catch (err) {
      console.error("Failed to fetch requests", err);
    }
  };

  const handleAgencyChange = (agencyKey: string) => {
    const defaultJurisdiction = agenciesConfig[agencyKey]?.jurisdiction || '';
    setFormData(prev => ({ ...prev, agency: agencyKey, jurisdiction: defaultJurisdiction }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/generate`, formData);
      await fetchRequests();
      setFormData({ ...formData, records: '' });
      alert("Request generated and sent to n8n successfully!");
    } catch (err: any) {
      alert("Error: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/demo`);
      console.log("Demo Response:", res.data);
      await fetchRequests();
      alert("Demo requests completed successfully!");
    } catch (err: any) {
      alert("Demo Error: " + (err.response?.data?.detail || err.message));
    } finally {
      setDemoLoading(false);
    }
  };

  const handleStatusChange = async (id: string, newStatus: string) => {
    try {
      await axios.patch(`${API_BASE}/status/${id}`, { status: newStatus });
      fetchRequests();
    } catch (err) {
      alert("Failed to update status");
    }
  };

  const handleExportExcel = () => {
    window.location.href = `${API_BASE}/export/excel`;
  };

  const StatusBadge = ({ status }: { status: RequestData['status'] }) => {
    const colors: Record<string, string> = {
      SENT: "bg-[var(--color-sent)]/10 text-[var(--color-sent)] border-[var(--color-sent)]/20",
      RESPONDED: "bg-[var(--color-responded)]/10 text-[var(--color-responded)] border-[var(--color-responded)]/20",
      OVERDUE: "bg-[var(--color-overdue)]/10 text-[var(--color-overdue)] border-[var(--color-overdue)]/20",
      CLOSED: "bg-[var(--color-closed)]/10 text-[var(--color-closed)] border-[var(--color-closed)]/20",
      FOLLOWED_UP: "bg-blue-100 text-blue-800 border-blue-200"
    };
    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[status] || "bg-gray-100 text-gray-800"}`}>
        {status}
      </span>
    );
  };

  const selectedStatute = statutesConfig[formData.jurisdiction];

  return (
    <div className="min-h-screen bg-[var(--color-canvas)] text-[var(--color-text-main)] pb-20">
      
      {/* Header */}
      <header className="glass sticky top-0 z-10 ghost-border border-b px-8 py-5">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-primary)] flex items-center gap-2">
            <FileText className="h-6 w-6" />
            FOIARTI Workspace
          </h1>
          <div className="text-sm font-medium text-[var(--color-text-muted)] tracking-wider uppercase">
            Ethereal Flux Design
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 mt-12 space-y-12">
        
        {/* Top Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* Form Card */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="lg:col-span-2 bg-[var(--color-surface)] shadow-soft rounded-2xl p-8"
          >
            <h2 className="text-2xl font-bold mb-2">Interactive Mode</h2>
            <p className="text-[var(--color-text-muted)] mb-8 max-w-lg">
              Generate legally compliant public records requests based on jurisdiction statutes.
            </p>

            <form onSubmit={handleSubmit} className="space-y-6">
              {selectedStatute && (
                <div className="bg-[var(--color-canvas)] p-4 rounded-xl border border-[var(--color-primary)]/20 flex gap-3 items-start mb-6 text-sm text-[var(--color-primary)]">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Applicable Law: </span>
                    {selectedStatute.law_name} ({selectedStatute.short_name}). 
                    Response expected in <span className="font-bold">{selectedStatute.response_days} {selectedStatute.response_day_type} days</span>.
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Agency</label>
                  <select 
                    value={formData.agency}
                    onChange={(e) => handleAgencyChange(e.target.value)}
                    className="w-full bg-[var(--color-surface-dim)] rounded-xl px-4 py-3 focus:bg-[var(--color-surface)] focus:ring-2 focus:ring-[var(--color-primary)] outline-none transition-all ghost-border"
                  >
                    {Object.entries(agenciesConfig).map(([k, v]) => (
                      <option key={k} value={k}>{v.full_name}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Jurisdiction</label>
                  <input 
                    type="text"
                    value={formData.jurisdiction ? formData.jurisdiction.charAt(0).toUpperCase() + formData.jurisdiction.slice(1) : ''}
                    disabled
                    className="w-full bg-[var(--color-surface-dim)] rounded-xl px-4 py-3 opacity-70 outline-none ghost-border font-medium cursor-not-allowed text-[var(--color-text-muted)]"
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Records Requested</label>
                  <textarea 
                    value={formData.records}
                    onChange={(e) => setFormData({...formData, records: e.target.value})}
                    required
                    rows={4}
                    placeholder="Describe the records you are seeking..."
                    className="w-full bg-[var(--color-surface-dim)] rounded-xl px-4 py-3 focus:bg-[var(--color-surface)] focus:ring-2 focus:ring-[var(--color-primary)] outline-none transition-all ghost-border resize-none"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Your Name</label>
                  <input 
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                    placeholder="Jane Doe"
                    className="w-full bg-[var(--color-surface-dim)] rounded-xl px-4 py-3 focus:bg-[var(--color-surface)] focus:ring-2 focus:ring-[var(--color-primary)] outline-none transition-all ghost-border"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)]">Your Email</label>
                  <input 
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                    placeholder="jane@example.com"
                    className="w-full bg-[var(--color-surface-dim)] rounded-xl px-4 py-3 focus:bg-[var(--color-surface)] focus:ring-2 focus:ring-[var(--color-primary)] outline-none transition-all ghost-border"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-[var(--color-outline)]/20">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className={`w-12 h-6 rounded-full transition-colors flex items-center px-1 ${formData.pdf ? 'bg-[var(--color-primary)]' : 'bg-gray-300'}`}>
                    <div className={`w-4 h-4 bg-white rounded-full transition-transform ${formData.pdf ? 'translate-x-6' : 'translate-x-0'}`} />
                  </div>
                  <span className="text-sm font-medium">Generate PDF Attachment</span>
                  <input 
                    type="checkbox"
                    checked={formData.pdf}
                    onChange={(e) => setFormData({...formData, pdf: e.target.checked})}
                    className="sr-only"
                  />
                </label>

                <button 
                  type="submit"
                  disabled={loading || !formData.agency}
                  className="gradient-primary text-white px-8 py-3 rounded-full font-semibold flex items-center gap-2 hover:brightness-110 active:scale-95 transition-all disabled:opacity-70 disabled:pointer-events-none"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin"/> : <Send className="w-5 h-5" />}
                  Dispatch Request
                </button>
              </div>
            </form>
          </motion.section>

          {/* Demo Card */}
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex flex-col gap-6"
          >
            <div className="bg-[var(--color-surface-dim)] ghost-border rounded-2xl p-8 flex flex-col justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">Demo Mode</h2>
                <p className="text-[var(--color-text-muted)] mb-8">
                  This system automates public records requests by generating legally formatted letters, sending them to agencies, and tracking responses with automated follow-ups.
                </p>
                
                <ul className="space-y-4 mb-8">
                  <li className="flex items-center gap-3 text-sm">
                    <CheckCircle className="w-5 h-5 text-[var(--color-primary)]" />
                    Generates 5 distinct requests
                  </li>
                  <li className="flex items-center gap-3 text-sm">
                    <CheckCircle className="w-5 h-5 text-[var(--color-primary)]" />
                    Saves automatically to SQLite/Neon
                  </li>
                  <li className="flex items-center gap-3 text-sm">
                    <CheckCircle className="w-5 h-5 text-[var(--color-primary)]" />
                    Triggers n8n Workflow automatically
                  </li>
                </ul>
              </div>

              <button 
                onClick={handleDemo}
                disabled={demoLoading}
                className="w-full bg-[var(--color-surface)] ghost-border text-[var(--color-primary)] px-8 py-3 rounded-full font-bold hover:bg-gray-50 transition-colors disabled:opacity-50 flex justify-center items-center gap-2"
              >
                {demoLoading ? <Loader2 className="w-5 h-5 animate-spin"/> : "Run Demo Generation"}
              </button>
            </div>

            <div className="bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/20 rounded-2xl p-6 text-[var(--color-primary)]">
              <h3 className="font-bold flex items-center gap-2 mb-2">
                <CalendarClock className="w-5 h-5" />
                Dailly Automated Follow-ups
              </h3>
              <p className="text-sm opacity-90 leading-relaxed">
                Your n8n automation scheduler is active. The system continually evaluates overdue statuses and auto-dispatches follow-up emails each day at exactly <strong>9:00 AM</strong>.
              </p>
            </div>
          </motion.section>
        </div>

        {/* Data Table */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-[var(--color-surface)] shadow-soft rounded-2xl overflow-hidden"
        >
          <div className="p-6 border-b border-[var(--color-outline)]/20 bg-[var(--color-surface)] flex justify-between items-center">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Table className="w-5 h-5 text-[var(--color-primary)]" />
              Active Tracking Dashboard
            </h3>
            
            <button 
              onClick={handleExportExcel}
              className="px-4 py-2 bg-[var(--color-surface-dim)] hover:bg-gray-100 rounded-lg text-sm font-bold flex items-center gap-2 transition-colors ghost-border"
            >
              <Download className="w-4 h-4" />
              Export to Excel
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-surface-dim)]/50">
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20">Request ID</th>
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20">Agency</th>
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20">Jurisdiction</th>
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20">Date Sent</th>
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20">Due Date</th>
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20">Status</th>
                  <th className="p-4 text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-outline)]/20 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-outline)]/10">
                {requests.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-[var(--color-text-muted)]">No active requests found. Create one above!</td>
                  </tr>
                ) : (
                  requests.map((req, i) => (
                    <tr key={req.id || i} className="hover:bg-[var(--color-surface-dim)]/30 transition-colors group cursor-pointer" onClick={() => setSelectedRequest(req)}>
                      <td className="p-4 text-sm font-medium">{String(req.id).split('-')[0]}..</td>
                      <td className="p-4 text-sm font-bold text-[var(--color-primary)]">{req.agency_name}</td>
                      <td className="p-4 text-sm capitalize">{req.jurisdiction}</td>
                      <td className="p-4 text-sm text-[var(--color-text-muted)]">
                        <div className="flex items-center gap-1.5"><Clock className="w-3 h-3"/> {req.date_sent}</div>
                      </td>
                      <td className="p-4 text-sm font-medium">{req.response_due}</td>
                      <td className="p-4">
                        <StatusBadge status={req.status} />
                      </td>
                      <td className="p-4 text-right">
                        <select 
                          className="text-xs bg-transparent ghost-border rounded px-2 py-1 outline-none"
                          value={req.status}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => handleStatusChange(req.id, e.target.value)}
                        >
                          <option value="SENT">Sent</option>
                          <option value="RESPONDED">Responded</option>
                          <option value="OVERDUE">Overdue</option>
                          <option value="FOLLOWED_UP">Followed Up</option>
                          <option value="CLOSED">Closed</option>
                        </select>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </motion.section>

      </main>

      {/* Detail Modal Overlay */}
      <AnimatePresence>
        {selectedRequest && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/40 backdrop-blur-sm"
            onClick={() => setSelectedRequest(null)}
          >
            <motion.div 
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-[var(--color-surface)] w-full max-w-2xl max-h-[85vh] overflow-hidden rounded-2xl shadow-xl flex flex-col ghost-border"
            >
              <div className="p-6 border-b border-[var(--color-outline)]/20 flex justify-between items-start bg-[var(--color-surface-dim)]/50">
                <div>
                  <h3 className="text-xl font-bold">{selectedRequest.agency_name}</h3>
                  <p className="text-sm text-[var(--color-text-muted)] mt-1">{selectedRequest.id}</p>
                </div>
                <StatusBadge status={selectedRequest.status} />
              </div>
              
              <div className="p-6 overflow-y-auto space-y-6 flex-1">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[var(--color-surface-dim)] p-4 rounded-xl">
                    <p className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-bold mb-1">Subject</p>
                    <p className="text-sm">{selectedRequest.subject}</p>
                  </div>
                  <div className="bg-[var(--color-surface-dim)] p-4 rounded-xl">
                    <p className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-bold mb-1">Requester</p>
                    <p className="text-sm">{selectedRequest.requester_name}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-bold mb-3 flex items-center gap-2"><FileText className="w-4 h-4"/> Saved Document</h4>
                  <div className="bg-gray-50 border border-[var(--color-outline)] rounded-xl p-4 font-mono text-xs whitespace-pre-wrap max-h-64 overflow-y-auto text-gray-800">
                    File Path: {selectedRequest.output_file}
                    <br/><br/>
                    (Check the output directory for the generated text/pdf files.)
                  </div>
                </div>
              </div>

              <div className="p-6 border-t border-[var(--color-outline)]/20 bg-[var(--color-surface-dim)]/30 flex justify-end">
                <button 
                  onClick={() => setSelectedRequest(null)}
                  className="px-6 py-2 rounded-full font-bold bg-white ghost-border hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
