import { useState, useRef, useEffect } from "react";
import HeaderWithUserProfile from "../components/navbar";
import Sidebar from "../components/sidebar";
import { Menu } from "lucide-react";
import ChatInput from "../components/ChatInput";
import { useAuth } from "../context/AuthContext";
import { API_BASE } from "../api/api";

function MessageLoading() {
  return (
    <div className="inline-flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
      <span>Reading document</span>
      <span className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:0ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:150ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-gray-400 animate-bounce [animation-delay:300ms]" />
      </span>
    </div>
  );
}

export default function Dashboard() {
  const { user, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [documentsVersion, setDocumentsVersion] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false); // ← NEW
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null); // ← NEW
  const [sessionId, setSessionId] = useState(null);
  
  useEffect(() => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    });
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  // ← NEW: Stop streaming handler
  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleNewMessage = async (text, metadata = null) => {
    const userMsg = {
      id: Date.now(),
      role: "user",
      content: text,
      file: metadata,
    };
    setMessages((prev) => [...prev, userMsg]);

    if (metadata?.skipAIResponse) {
      setDocumentsVersion((v) => v + 1);
      return;
    }

    const aiMsgId = Date.now() + 1;
    setMessages((prev) => [
      ...prev,
      {
        id: aiMsgId,
        role: "assistant",
        content: "",
        citations: [],
        isStreaming: true,
      },
    ]);

    // ← NEW: Create abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;
    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        signal: controller.signal, // ← NEW: Attach signal
        body: JSON.stringify({ 
          message: text, 
          document_id: selectedDocument?.id ?? null,
          session_id: sessionId
        }),
      });

      if (!response.ok) throw new Error("Chat failed");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") continue;

          try {
            const parsed = JSON.parse(data);

            if (parsed.content) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMsgId 
                    ? { ...m, content: m.content + parsed.content } 
                    : m
                )
              );
            }

            if (parsed.citations) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMsgId
                    ? { ...m, citations: parsed.citations }
                    : m
                )
              );
            }
            if (parsed.session_id) {
              setSessionId(parsed.session_id);
            }
          } catch {
            // Silent ignore for streaming chunks
          }
        }
      }
    } catch (err) {
      // Handle abort vs real error
      if (err.name === "AbortError") {
        console.log("Streaming stopped by user");
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMsgId
              ? { ...m, content: m.content || "Sorry, something went wrong." }
              : m
          )
        );
      }
    } finally {
      // ← NEW: Always cleanup
      setIsStreaming(false);
      abortControllerRef.current = null;
      
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId ? { ...m, isStreaming: false } : m
        )
      );
    }
  };

  const handleDocumentSelect = (doc) => {
    setSidebarOpen(false);
    const systemMsg = {
      id: Date.now(),
      role: "system",
      content: `Now chatting about: **${doc.filename}** (${doc.page_count} page${
        doc.page_count !== 1 ? "s" : ""
      })`,
    };
    setMessages((prev) => [...prev, systemMsg]);
    setSelectedDocument(doc);
  };

  const getInitials = () => {
    if (!user) return "??";
    const name = user.name || user.email || "";
    const parts = name.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : name.charAt(0).toUpperCase() || "??";
  };

  const getSourceSummary = (citations = []) => {
    const grouped = new Map();

    citations.forEach((cite) => {
      const source = cite.source || "Unknown source";
      const rawPage = cite.page;
      const numericPage = Number(rawPage);
      const page = Number.isFinite(numericPage) ? numericPage + 1 : rawPage;

      if (!grouped.has(source)) {
        grouped.set(source, { source, pages: new Set(), count: 0 });
      }

      const group = grouped.get(source);
      group.count += 1;
      if (page !== undefined && page !== null && page !== "?") {
        group.pages.add(page);
      }
    });

    return Array.from(grouped.values()).map((group) => ({
      ...group,
      pages: Array.from(group.pages).sort((a, b) => Number(a) - Number(b)),
    }));
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100 overflow-hidden">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed lg:static inset-y-0 left-0 z-50 w-80 max-w-[85vw] bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 
          transform transition-transform duration-300 ease-in-out lg:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} lg:w-[280px]`}
      >
        <Sidebar
          closeSidebar={() => setSidebarOpen(false)}
          onDocumentSelect={handleDocumentSelect}
          documentsVersion={documentsVersion}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Mobile Header */}
        <header className="lg:hidden sticky top-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 -ml-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <Menu className="w-6 h-6 text-gray-700 dark:text-gray-300" />
              </button>
              <h1 className="text-xl font-semibold">MindVault</h1>
            </div>

            <div className="flex items-center gap-4">
              <button className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold text-sm shadow-md hover:bg-indigo-700 transition-all">
                {getInitials()}
              </button>
            </div>
          </div>
        </header>

        {/* Desktop Header */}
        <div className="hidden lg:block sticky top-0 z-30 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm">
          <HeaderWithUserProfile user={user} />
        </div>

        {/* Messages Area */}
        <main className="flex-1 overflow-y-auto px-3 sm:px-5 lg:px-8 py-4 sm:py-6 bg-gradient-to-b from-transparent to-gray-50/50 dark:to-gray-950/50">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <h2 className="text-2xl sm:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-3">
                Your Private AI Assistant
              </h2>
              <p className="text-sm sm:text-[15px] text-gray-600 dark:text-gray-400 max-w-md">
                Upload your documents
              </p>
            </div>
          ) : (
            <div className="mx-auto w-full max-w-3xl">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${
                  msg.role === "user"
                    ? "justify-end"
                    : msg.role === "system"
                    ? "justify-center"
                    : "justify-start"
                } mb-6 animate-fade-in`}
              >
                {msg.role === "system" ? (
                  <div className="px-5 py-2.5 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium shadow-sm">
                    {msg.content}
                  </div>
                ) : (
                  <div
                    className={`max-w-[88%] sm:max-w-2xl px-5 py-4 text-sm sm:text-[15px] leading-relaxed transition-all duration-200
                      ${
                        msg.role === "user"
                          ? "rounded-2xl rounded-br-md bg-indigo-600 text-white shadow-sm"
                          : "rounded-2xl rounded-bl-md bg-white dark:bg-gray-900 border border-gray-200/80 dark:border-gray-800 text-gray-900 dark:text-gray-100 shadow-sm"
                      }`}
                  >
                    <div className="whitespace-pre-wrap">
                      {msg.content || (msg.isStreaming && <MessageLoading />)}
                    </div>

                    {msg.file && (
                      <p className="text-xs mt-2 opacity-80">
                        {msg.file.status === "error" ? "Upload failed" : "Uploaded"}: {msg.file.name}
                      </p>
                    )}

                    {msg.isStreaming && msg.content && (
                      <div className="flex gap-1 mt-2">
                        <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:0ms]"></span>
                        <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:150ms]"></span>
                        <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:300ms]"></span>
                      </div>
                    )}

                    {msg.citations?.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-200/70 dark:border-gray-800">
                        <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-2 tracking-wide uppercase">
                          Sources
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {getSourceSummary(msg.citations).map((cite) => (
                            <span
                              key={cite.source}
                              className="inline-flex max-w-full items-center gap-1.5 rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400"
                            >
                              <span className="truncate max-w-[220px] font-medium text-gray-700 dark:text-gray-300">
                                {cite.source}
                              </span>
                              <span className="text-gray-400 dark:text-gray-500">·</span>
                              <span className="shrink-0 text-gray-500 dark:text-gray-400">
                                {cite.pages.length > 0
                                  ? `p. ${cite.pages.slice(0, 4).join(", ")}${cite.pages.length > 4 ? "+" : ""}`
                                  : `${cite.count} refs`}
                              </span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            </div>
          )}
          <div ref={messagesEndRef} />
        </main>

        {/* Chat Input - Pass isStreaming and stop handler */}
        <div className="sticky bottom-0 z-30 bg-white dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800 shadow-lg">
          <div className="mx-auto w-full max-w-3xl">
            <ChatInput 
              onSend={handleNewMessage} 
              isStreaming={isStreaming}
              onStop={handleStopStreaming}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
