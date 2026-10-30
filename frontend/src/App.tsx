import { useState, useRef, useEffect } from "react";
import { Header, type NavTab } from "@/components/Header/Header";
import { Sidebar } from "@/components/Sidebar/Sidebar";
import { LandingHero } from "@/components/Chat/LandingHero";
import { MessageItem } from "@/components/Chat/MessageItem";
import { QueryInput } from "@/components/Chat/QueryInput";
import { LoadingIndicator } from "@/components/Chat/LoadingIndicator";
import { InspectorPanel, type InspectorTab } from "@/components/Inspector/InspectorPanel";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { OverviewPage } from "@/components/Overview/OverviewPage";
import { ComparisonView } from "@/components/Views/ComparisonView";
import { ArchitectureView } from "@/components/Views/ArchitectureView";
import { useChat } from "@/hooks/useChat";
import { AlertTriangle } from "lucide-react";
import type { ChatMessage } from "@/types";

export default function App() {
  const [currentNav, setCurrentNav] = useState<NavTab>("overview");

  const {
    messages,
    isLoading,
    currentStage,
    activeMessage,
    error,
    activeTab,
    setActiveTab,
    setActiveMessage,
    sendMessage,
    clearChat,
  } = useChat();

  const [isRightPanelOpen, setIsRightPanelOpen] = useState(() => {
    return typeof window !== "undefined" ? window.innerWidth >= 1200 : true;
  });
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages container
  useEffect(() => {
    if (currentNav === "demo") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading, currentNav]);

  // If there's an active message or new messages arrive, default the inspector to it
  useEffect(() => {
    if (!activeMessage && messages.length > 0) {
      const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
      if (lastAssistant) {
        setActiveMessage(lastAssistant);
      }
    }
  }, [messages, activeMessage, setActiveMessage]);

  const handleInspectMessage = (
    msg: ChatMessage,
    tab?: InspectorTab
  ) => {
    setActiveMessage(msg);
    if (tab) setActiveTab(tab);
    setIsRightPanelOpen(true);
  };

  const handleSelectHistoricalMessage = (msg: ChatMessage) => {
    setActiveMessage(msg);
    setIsRightPanelOpen(true);
    setIsMobileSidebarOpen(false);
  };

  const handleNavigate = (tab: NavTab) => {
    if (tab === "evidence") {
      setActiveTab("evidence");
      setIsRightPanelOpen(true);
      setCurrentNav("demo");
      return;
    }
    setCurrentNav(tab);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#F5F1E8] text-[#1F1F1F] font-sans transition-colors">
      {/* Top Navigation Header with Minimal Labels */}
      <Header
        currentNav={currentNav}
        onSelectNav={handleNavigate}
        isRightPanelOpen={isRightPanelOpen}
        onToggleRightPanel={() => setIsRightPanelOpen((prev) => !prev)}
        onToggleSidebar={() => setIsMobileSidebarOpen((prev) => !prev)}
      />

      {/* Main App Body */}
      <div className="flex flex-1 h-[calc(100vh-3.5rem)] overflow-hidden relative">
        {/* Render Overview Landing Page */}
        {currentNav === "overview" && (
          <main className="flex-1 h-full overflow-hidden">
            <ErrorBoundary fallbackTitle="Overview page encountered an issue">
              <OverviewPage onNavigate={handleNavigate} />
            </ErrorBoundary>
          </main>
        )}

        {/* Render Baseline Comparison Page */}
        {currentNav === "comparison" && (
          <main className="flex-1 h-full overflow-hidden">
            <ErrorBoundary fallbackTitle="Comparison page encountered an issue">
              <ComparisonView onNavigate={handleNavigate} />
            </ErrorBoundary>
          </main>
        )}

        {/* Render System Architecture Page */}
        {currentNav === "architecture" && (
          <main className="flex-1 h-full overflow-hidden">
            <ErrorBoundary fallbackTitle="Architecture page encountered an issue">
              <ArchitectureView onNavigate={handleNavigate} />
            </ErrorBoundary>
          </main>
        )}

        {/* Render Interactive Demo (Chat & Intelligence Inspector) */}
        {currentNav === "demo" && (
          <>
            {/* Left Sidebar (Desktop & Mobile Drawer) */}
            <div className="hidden md:block shrink-0">
              <Sidebar
                messages={messages}
                onNewChat={clearChat}
                onSelectMessage={handleSelectHistoricalMessage}
                activeMessageId={activeMessage?.id}
              />
            </div>

            {/* Mobile Drawer Overlay */}
            {isMobileSidebarOpen && (
              <div className="fixed inset-0 z-40 md:hidden flex">
                <div
                  className="fixed inset-0 bg-black/30 backdrop-blur-sm"
                  onClick={() => setIsMobileSidebarOpen(false)}
                />
                <div className="relative z-50 w-72 bg-[#F5F1E8] h-full shadow-2xl">
                  <Sidebar
                    messages={messages}
                    onNewChat={() => {
                      clearChat();
                      setIsMobileSidebarOpen(false);
                    }}
                    onSelectMessage={(msg) => {
                      handleSelectHistoricalMessage(msg);
                      setIsMobileSidebarOpen(false);
                    }}
                    activeMessageId={activeMessage?.id}
                  />
                </div>
              </div>
            )}

            {/* Center Main Chat Area */}
            <main className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#F5F1E8]">
              {/* Dismissible Error Banner */}
              {error && (
                <div className="bg-white border-b border-[#E5DED3] px-4 py-2.5 text-xs text-[#6B2E46] flex items-center justify-between z-10 shrink-0">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                </div>
              )}

              {/* Scrollable Chat Feed */}
              <div className="flex-1 overflow-y-auto px-2 py-4">
                <ErrorBoundary fallbackTitle="Could not display conversation history">
                  {messages.length === 0 ? (
                    <LandingHero onSelectQuestion={(q) => sendMessage(q)} />
                  ) : (
                    <div className="space-y-4 pb-4">
                      {messages.map((msg) => (
                        <MessageItem
                          key={msg.id}
                          message={msg}
                          onInspectMessage={handleInspectMessage}
                        />
                      ))}

                      {/* Pipeline Animated Loading Indicator */}
                      {isLoading && <LoadingIndicator currentStage={currentStage} />}
                      <div ref={messagesEndRef} />
                    </div>
                  )}
                </ErrorBoundary>
              </div>

              {/* Bottom Fixed Input Box */}
              <div className="shrink-0 bg-gradient-to-t from-[#F5F1E8] via-[#F5F1E8]/90 to-transparent pt-4">
                <QueryInput
                  onSend={(q) => sendMessage(q)}
                  isLoading={isLoading}
                />
              </div>
            </main>

            {/* Right Intelligence Inspector Panel */}
            {isRightPanelOpen && (
              <div className="shrink-0 animate-fade-in">
                <ErrorBoundary fallbackTitle="Inspector panel encountered an issue">
                  <InspectorPanel
                    message={activeMessage}
                    activeTab={activeTab}
                    onTabChange={(tab) => setActiveTab(tab)}
                    onClose={() => setIsRightPanelOpen(false)}
                  />
                </ErrorBoundary>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
