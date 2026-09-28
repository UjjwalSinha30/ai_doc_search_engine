import { useState, useRef, useEffect } from "react";
import { 
  Send, 
  Paperclip, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Square,
  FileText,
  Sparkles,
} from "lucide-react";
import { API_BASE } from "../api/api";

export default function ChatInput({ 
  onSend, 
  isStreaming = false, 
  onStop,
}) {
  const [input, setInput] = useState("");
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [showUploadHint, setShowUploadHint] = useState(false);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!isStreaming) {
      textareaRef.current?.focus();
    }
  }, [isStreaming]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
  }, [input]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      setUploadStatus("error");
      onSend?.(`Upload failed: File size exceeds 50MB limit`, {
        type: "file",
        status: "error"
      });
      setTimeout(() => setUploadStatus(null), 5000);
      return;
    }

    setUploadStatus("uploading");
    setUploadedFileName(file.name);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      setUploadStatus("success");
      onSend?.(
        `✓ Successfully added "${file.name}"`,
        {
          type: "file",
          name: file.name,
          status: "success",
          skipAIResponse: true,
        }
      );

      setTimeout(() => {
        setUploadStatus(null);
        setUploadedFileName("");
      }, 3000);
    } catch (err) {
      setUploadStatus("error");
      const msg = err.message || "Upload failed. Please try again.";
      onSend?.(`✗ Upload failed: ${msg}`, {
        type: "file",
        status: "error"
      });
      setTimeout(() => {
        setUploadStatus(null);
        setUploadedFileName("");
      }, 5000);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    onSend?.(input.trim());
    setInput("");
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  return (
    <div className="
      border-t border-gray-200/80 dark:border-gray-800/60
      bg-white/95 dark:bg-gray-950/95
      backdrop-blur-xl
      shadow-[0_-8px_30px_-8px_rgba(0,0,0,0.1)] 
      dark:shadow-[0_-8px_30px_-8px_rgba(0,0,0,0.4)]
      transition-all duration-300
    ">
      <div className="max-w-4xl mx-auto px-4 py-3">
        
        {/* Upload Status */}
        {uploadStatus && (
          <div className={`
            mb-4 px-4 py-3 rounded-xl flex items-center gap-3
            transition-all duration-300
            ${uploadStatus === "uploading" 
              ? "bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800/50" 
              : uploadStatus === "success"
              ? "bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800/50"
              : "bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50"
            }
          `}>
            {uploadStatus === "uploading" && (
              <>
                <Loader2 className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Processing document...
                  </p>
                  <p className="text-xs text-blue-700 dark:text-blue-300 truncate mt-0.5">
                    {uploadedFileName}
                  </p>
                </div>
              </>
            )}
            {uploadStatus === "success" && (
              <>
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-green-900 dark:text-green-100">
                    Document added successfully
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300 truncate mt-0.5">
                    {uploadedFileName}
                  </p>
                </div>
              </>
            )}
            {uploadStatus === "error" && (
              <>
                <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-red-900 dark:text-red-100">
                    Upload failed
                  </p>
                  <p className="text-xs text-red-700 dark:text-red-300 mt-0.5">
                    Please check file and try again
                  </p>
                </div>
              </>
            )}
          </div>
        )}

        {/* Main Input Area */}
        <div
          className="
            relative flex items-end gap-2 rounded-2xl border border-gray-200
            bg-white px-3 py-2 shadow-sm transition-all duration-200
            focus-within:border-indigo-300 focus-within:ring-4 focus-within:ring-indigo-500/10
            dark:border-gray-800 dark:bg-gray-900
          "
          onMouseDown={() => textareaRef.current?.focus()}
          onClick={() => textareaRef.current?.focus()}
        >

          {/* Upload Button */}
          <div 
            className="relative"
            onMouseEnter={() => setShowUploadHint(true)}
            onMouseLeave={() => setShowUploadHint(false)}
          >
            <label className="group relative cursor-pointer">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".pdf,.txt,.docx,.md,.csv"
                className="hidden"
                disabled={isStreaming || uploadStatus === "uploading"}
              />
              <div className={`
                flex h-9 w-9 items-center justify-center
                rounded-lg transition-all duration-200
                ${isStreaming || uploadStatus === "uploading"
                  ? "opacity-40 cursor-not-allowed" 
                  : "hover:scale-105 active:scale-95"
                }
                ${uploadStatus === "uploading" 
                  ? "bg-blue-50 dark:bg-blue-950/40 ring-2 ring-blue-400/50" 
                  : "text-gray-500 hover:bg-gray-100 hover:text-indigo-600 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-indigo-400"
                }
              `}>
                <Paperclip className={`
                  w-5 h-5 transition-colors
                  ${uploadStatus === "uploading"
                    ? "text-blue-600 dark:text-blue-400"
                    : "text-gray-500 dark:text-gray-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400"
                  }
                `} />
              </div>
            </label>

            {/* Upload Tooltip */}
            {showUploadHint && !uploadStatus && (
              <div className="
                absolute -top-24 left-1/2 -translate-x-1/2 w-64
                px-4 py-3 bg-gray-900/95 dark:bg-gray-800/95 rounded-xl
                shadow-2xl backdrop-blur-sm z-50
              ">
                <div className="flex items-start gap-2.5">
                  <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-white text-xs font-semibold mb-1">
                      Add Document
                    </p>
                    <p className="text-gray-300 text-[11px] leading-relaxed">
                      Upload files to let AI use your documents
                    </p>
                  </div>
                </div>
                <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-gray-900/95 dark:bg-gray-800/95 rotate-45" />
              </div>
            )}
          </div>

          {/* Textarea */}
          <div
            className="relative min-w-0 flex-1"
            onClick={() => textareaRef.current?.focus()}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={isStreaming ? "AI is thinking..." : "Type your message..."}
              disabled={isStreaming}
              rows={1}
              className={`
                block w-full resize-none bg-transparent px-1 py-2 text-sm
                focus:outline-none
                placeholder:text-gray-400 dark:placeholder:text-gray-500
                text-gray-900 dark:text-gray-100
                transition-all duration-200
                disabled:opacity-60 disabled:cursor-not-allowed
                scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600
              `}
              style={{ minHeight: "40px", maxHeight: "120px" }}
            />

            {isStreaming && (
              <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-indigo-50 dark:bg-indigo-950/50 rounded-full border border-indigo-200 dark:border-indigo-800">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400 animate-pulse" />
                <span className="text-xs font-medium text-indigo-700 dark:text-indigo-300">
                  AI thinking...
                </span>
              </div>
            )}

            {input.length > 0 && !isStreaming && (
              <div className="absolute bottom-4 right-4 text-xs text-gray-400 dark:text-gray-500 pointer-events-none">
                {input.length}
              </div>
            )}
          </div>

          {/* Send / Stop Button */}
          {isStreaming ? (
            <button
              onClick={onStop}
              title="Stop generation"
              className="
                flex h-9 w-9 flex-shrink-0 items-center justify-center
                rounded-lg bg-red-600
                hover:bg-red-700
                active:scale-95 shadow-sm
                transition-all duration-200 group
              "
            >
              <Square className="w-4 h-4 text-white fill-white group-hover:scale-110 transition-transform" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              title="Send message (Enter)"
              className={`
                flex h-9 w-9 flex-shrink-0 items-center justify-center
                rounded-lg transition-all duration-200 group
                ${input.trim()
                  ? "bg-indigo-600 hover:bg-indigo-700 shadow-sm"
                  : "bg-gray-200 dark:bg-gray-800 cursor-not-allowed opacity-50"
                }
                active:scale-95
              `}
            >
              <Send className={`
                w-4 h-4 text-white transition-transform
                ${input.trim() ? 'group-hover:translate-x-0.5 group-hover:-translate-y-0.5' : ''}
              `} />
            </button>
          )}
        </div>

        {/* Bottom hints */}
        <div className="hidden">
          <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1.5">
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-gray-600 dark:text-gray-300 font-mono text-[10px] border border-gray-300 dark:border-gray-700">
                Enter
              </kbd>
              <span>to send</span>
            </span>
            <span className="text-gray-300 dark:text-gray-700">•</span>
            <span className="flex items-center gap-1.5">
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-gray-600 dark:text-gray-300 font-mono text-[10px] border border-gray-300 dark:border-gray-700">
                Shift+Enter
              </kbd>
              <span>new line</span>
            </span>
          </div>
          
          <div className="flex items-center gap-2 text-gray-400 dark:text-gray-500">
            <span>PDF, DOCX, TXT, MD, CSV • max 50MB</span>
          </div>
        </div>
      </div>
    </div>
  );
}
