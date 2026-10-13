import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { DocumentItem, DocumentChunk } from '../../types';
import { UploadCloud, FileText, CheckCircle2, Clock, Eye, AlertCircle, Sparkles } from 'lucide-react';

export const SourcesTab: React.FC = () => {
  const { activeProject, showToast } = useApp();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const loadDocuments = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getDocuments(activeProject.id);
      setDocuments(data);
      if (data.length > 0 && !selectedDoc) {
        setSelectedDoc(data[0]);
      }
    } catch (e) {
      console.error('Error loading documents', e);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [activeProject]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !activeProject) return;
    const file = e.target.files[0];
    setIsUploading(true);
    try {
      const uploaded = await api.uploadDocument(activeProject.id, file);
      showToast(`Document "${file.name}" successfully parsed into structured chunks!`, 'success');
      await loadDocuments();
      setSelectedDoc(uploaded);
    } catch (err) {
      showToast('Document upload failed. Please ensure file is PDF, DOCX, or TXT.', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  const uploadSampleRfp = async () => {
    if (!activeProject) return;
    setIsUploading(true);
    try {
      const sampleContent = `# AI-Powered University Tutor Booking Platform - Client RFP Specification
## 1.0 Executive Summary
The University Academic Excellence Center needs an online platform where students can find tutors, book 1-on-1 sessions, pay online, and receive notifications. Tutors should manage their availability. Admin should monitor users and bookings. The platform should be secure and fast.

## 2.0 Booking & Cancellation Policies
Students can cancel a booking at any time without restriction and receive immediate balance refund.
Note: Section 4.2 states bookings cannot be cancelled within 24 hours of session start.`;

      const blob = new Blob([sampleContent], { type: 'text/markdown' });
      const file = new File([blob], 'Tutor_Booking_Platform_RFP_Specification.md', { type: 'text/markdown' });
      await api.uploadDocument(activeProject.id, file);
      showToast('Sample Tutor Booking RFP specification uploaded and chunked!', 'success');
      await loadDocuments();
    } catch (e) {
      showToast('Failed to upload sample RFP', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div className="glass-panel p-6 rounded-2xl border border-dashed border-indigo-700/50 hover:border-indigo-500/80 transition-all text-center space-y-4">
        <div className="mx-auto h-12 w-12 rounded-full bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
          <UploadCloud className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-white">Upload Stakeholder Requirements Documents</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Drag & drop PDF, DOCX, TXT, or Markdown documents. The Ingestion Agent extracts text, sections, and preserves exact page provenance.
          </p>
        </div>

        <div className="flex items-center justify-center gap-3">
          <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center space-x-2 transition-all shadow-md shadow-indigo-600/30">
            <span>{isUploading ? 'Parsing & Chunking...' : 'Select Document from Computer'}</span>
            <input
              type="file"
              accept=".pdf,.docx,.doc,.txt,.md"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
            />
          </label>

          <button
            onClick={uploadSampleRfp}
            disabled={isUploading}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center space-x-1.5 transition-all"
          >
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>Load Reference RFP</span>
          </button>
        </div>
      </div>

      {/* Document List & Chunk Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Uploaded Documents */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white flex items-center space-x-2">
              <FileText className="h-4 w-4 text-blue-400" />
              <span>Uploaded Sources ({documents.length})</span>
            </h4>
          </div>

          <div className="space-y-2">
            {documents.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                No documents uploaded yet.
              </div>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDoc(doc)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    selectedDoc?.id === doc.id
                      ? 'bg-indigo-950/40 border-indigo-500/80 shadow-md shadow-indigo-950/40'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200 truncate max-w-[200px]">
                      {doc.filename}
                    </span>
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {doc.file_type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                    <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                    <span className="flex items-center text-emerald-400">
                      <CheckCircle2 className="h-3 w-3 mr-1" />
                      Chunked
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right 2 Cols: Chunk Viewer & Provenance Inspector */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                <Eye className="h-4 w-4 text-indigo-400" />
                <span>Document Chunk Inspector & Provenance</span>
              </h4>
              <p className="text-xs text-slate-400">
                {selectedDoc ? `Viewing chunks for ${selectedDoc.filename}` : 'Select a document to inspect its parsed sections'}
              </p>
            </div>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {!selectedDoc || !selectedDoc.chunks || selectedDoc.chunks.length === 0 ? (
              <div className="text-center py-12 text-xs text-slate-500">
                No structured chunks available for this document.
              </div>
            ) : (
              selectedDoc.chunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className="bg-slate-900/90 border border-slate-800/80 p-4 rounded-xl space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-indigo-300">
                        {chunk.section_title || `Section ${chunk.chunk_index}`}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-[10px]">
                      <span className="bg-blue-950/60 border border-blue-800/60 text-blue-400 px-2 py-0.5 rounded-full font-semibold">
                        Page {chunk.page_number}
                      </span>
                      <span className="bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
                        {chunk.token_count} words
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/50">
                    {chunk.content}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
