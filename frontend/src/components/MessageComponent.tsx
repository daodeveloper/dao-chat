"use client"

import React, { useState, useRef, useEffect, ReactNode } from 'react';
import { UserIcon } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components as MarkdownComponents } from 'react-markdown';
import FeedbackModal from './FeedbackModal';

const ThumbIcon = ({ type, active }: { type: 'up' | 'down'; active: boolean }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none"
    stroke="currentColor" 
    strokeWidth="2"
    strokeLinecap="round" 
    strokeLinejoin="round"
    className={`h-5 w-5 transition-all duration-200 ${active ? 'fill-current text-blue-500' : 'text-gray-400'}`}
  >
    {type === 'up' ? (
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
    ) : (
      <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
    )}
  </svg>
);

interface Message {
  role: 'user' | 'bot';
  content: string;
  id?: number;
}

interface MessageComponentProps {
  message: Message;
  isDarkMode: boolean;
  isStreaming: boolean;
}

interface ComponentProps {
  children?: ReactNode;
  className?: string;
  href?: string;
  inline?: boolean;
}

const MessageComponent: React.FC<MessageComponentProps> = ({ message, isDarkMode, isStreaming }) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);

  const preprocessMarkdown = (content: string) => {
    // Fix numbered headers (like ####1)
    let processed = content.replace(/####(\d+)/g, (_, num) => `#### ${num}`);
    return processed;
  };

  useEffect(() => {
    if (contentRef.current && isStreaming) {
      const scrollContainer = contentRef.current.closest('.custom-scrollbar');
      if (scrollContainer) {
        scrollContainer.scrollTo({
          top: scrollContainer.scrollHeight,
          behavior: 'auto'
        });
      }
    }
  }, [isStreaming, message.content]);

  const handleFeedback = async (type: 'up' | 'down') => {
    if (!message.id) return;
    
    try {
      const response = await fetch(`/api/message/${message.id}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          thumbs_up: type === 'up',
          thumbs_down: type === 'down',
        }),
      });

      if (response.ok) {
        setFeedback(type === feedback ? null : type);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const handleDetailedFeedback = async (rating: number, feedback: string, email: string) => {
    if (!message.id) return;
    
    try {
      await fetch(`/api/message/${message.id}/detailed-feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rating,
          feedback_text: feedback,
          email,
        }),
      });
    } catch (error) {
      console.error('Error submitting detailed feedback:', error);
    } finally {
      setShowFeedbackModal(false);
    }
  };

  const renderContent = () => {
    if (message.role === 'user') {
      return <p className="text-sm sm:text-base break-words whitespace-pre-wrap">{message.content}</p>;
    }

    const components: Partial<MarkdownComponents> = {
      p: ({ children }: ComponentProps) => (
        <p className="mb-4 text-sm sm:text-base leading-relaxed break-words last:mb-0">{children}</p>
      ),
      a: ({ href, children }: ComponentProps) => (
        <a 
          href={href}
          className="text-blue-500 hover:underline break-words" 
          target="_blank" 
          rel="noopener noreferrer"
        >
          {children}
        </a>
      ),
      ul: ({ children }: ComponentProps) => (
        <ul className="list-disc pl-4 sm:pl-6 mb-4 space-y-2 last:mb-0">{children}</ul>
      ),
      ol: ({ children }: ComponentProps) => (
        <ol className="list-decimal pl-4 sm:pl-6 mb-4 space-y-2 last:mb-0">{children}</ol>
      ),
      li: ({ children }: ComponentProps) => (
        <li className="text-sm sm:text-base leading-relaxed">
          {children}
        </li>
      ),
      strong: ({ children }: ComponentProps) => (
        <strong className="font-semibold">
          {children}
        </strong>
      ),
      em: ({ children }: ComponentProps) => (
        <em className="italic">{children}</em>
      ),
      h1: ({ children }: ComponentProps) => (
        <h1 className="text-xl font-bold mb-4">{children}</h1>
      ),
      h2: ({ children }: ComponentProps) => (
        <h2 className="text-lg font-semibold mb-3">{children}</h2>
      ),
      h3: ({ children }: ComponentProps) => (
        <h3 className="text-base font-medium mb-2">{children}</h3>
      ),
      h4: ({ children }: ComponentProps) => (
        <h4 className="text-base font-medium mb-2">{children}</h4>
      ),
      code: ({ className, children, inline }: ComponentProps) => {
        const match = /language-(\w+)/.exec(className || '');
        return inline ? (
          <code className={`font-mono text-sm px-1.5 py-0.5 rounded ${
            isDarkMode ? "bg-gray-800 text-gray-100" : "bg-gray-100 text-gray-800"
          }`}>
            {children}
          </code>
        ) : (
          <pre className={`rounded-lg p-4 mb-4 overflow-x-auto ${
            isDarkMode ? "bg-gray-800" : "bg-gray-100"
          }`}>
            <code className={`language-${match?.[1] || ''} block text-sm font-mono ${
              isDarkMode ? "text-gray-100" : "text-gray-800"
            }`}>
              {children}
            </code>
          </pre>
        );
      },
      table: ({ children }: ComponentProps) => (
        <div className="w-full overflow-x-auto mb-4 -mx-2 sm:mx-0">
          <div className="inline-block min-w-full align-middle p-2">
            <div className="overflow-hidden border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                {children}
              </table>
            </div>
          </div>
        </div>
      ),
      thead: ({ children }: ComponentProps) => (
        <thead className={`${isDarkMode ? "bg-gray-800" : "bg-gray-50"}`}>
          {children}
        </thead>
      ),
      tbody: ({ children }: ComponentProps) => (
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {children}
        </tbody>
      ),
      tr: ({ children }: ComponentProps) => (
        <tr className={`${isDarkMode ? "hover:bg-gray-700/50" : "hover:bg-gray-50"} transition-colors`}>
          {children}
        </tr>
      ),
      th: ({ children }: ComponentProps) => (
        <th className={`px-3 py-2 sm:px-4 sm:py-3 text-left text-sm font-semibold uppercase tracking-wider border-b border-r last:border-r-0 ${
          isDarkMode 
            ? "bg-gray-800 text-gray-300 border-gray-700" 
            : "bg-gray-50 text-gray-700 border-gray-200"
        }`}
        style={{ minWidth: '120px' }}>
          {children}
        </th>
      ),
      td: ({ children }: ComponentProps) => (
        <td className={`px-3 py-2 sm:px-4 sm:py-3 text-sm border-b border-r last:border-r-0 ${
          isDarkMode 
            ? "bg-gray-800 text-gray-300 border-gray-700" 
            : "bg-white text-gray-700 border-gray-200"
        }`}
        style={{ minWidth: '120px' }}>
          {children}
        </td>
      ),
      blockquote: ({ children }: ComponentProps) => (
        <blockquote className={`border-l-4 pl-4 my-4 italic text-sm sm:text-base ${
          isDarkMode 
            ? "border-gray-600 text-gray-300" 
            : "border-gray-300 text-gray-700"
        }`}>
          {children}
        </blockquote>
      ),
      hr: () => (
        <hr className="my-6 border-t border-gray-200 dark:border-gray-700" />
      )
    };

    return (
      <div ref={contentRef} className="w-full overflow-hidden">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          className="markdown-content"
          components={components}
        >
          {preprocessMarkdown(message.content)}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <>
      <div className={`flex flex-col mb-2 ${message.role === "user" ? "items-end" : "items-start"} w-full`}>
        <div className={`flex items-start ${message.role === "user" ? "justify-end" : "justify-start"} w-full px-2 sm:px-0`}>
          {message.role === "bot" && (
            <div className="w-6 h-6 mr-2 flex-shrink-0 mt-1">
              <img 
                src="/emblem.svg" 
                alt="DAO PropTech Emblem" 
                className={`w-full h-full ${isDarkMode ? 'invert' : ''}`}
              />
            </div>
          )}
          <div className={`rounded-lg p-2 sm:p-3 ${
            message.role === "user" 
              ? "bg-[#ADFF2F] text-black max-w-[85%] sm:max-w-[75%]" 
              : isDarkMode 
                ? "bg-gray-700 w-full" 
                : "bg-gray-200 w-full"
          }`}>
            {renderContent()}
          </div>
          {message.role === "user" && <UserIcon className="w-5 h-5 sm:w-6 sm:h-6 ml-2 text-[#ADFF2F] flex-shrink-0 mt-1" />}
        </div>
        {message.role === 'bot' && !isStreaming && (
          <div className="flex items-center gap-2 mt-1 ml-8">
            <button 
              onClick={() => handleFeedback('up')}
              className="feedback-btn p-1 rounded-full transition-all duration-200 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="Thumbs up"
            >
              <ThumbIcon type="up" active={feedback === 'up'} />
            </button>
            <button 
              onClick={() => handleFeedback('down')}
              className="feedback-btn p-1 rounded-full transition-all duration-200 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="Thumbs down"
            >
              <ThumbIcon type="down" active={feedback === 'down'} />
            </button>
          </div>
        )}
      </div>
      <FeedbackModal 
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleDetailedFeedback}
      />
    </>
  );
};

export default MessageComponent;