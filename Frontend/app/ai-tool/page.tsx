"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import Layout from "@/components/Layout"
import { Send, Bot, User, Calendar, Clock, Archive } from "lucide-react"

interface Message {
  id: string
  type: "user" | "bot"
  content: string
  timestamp: Date
}

export default function AITool() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [selectedTimeframe, setSelectedTimeframe] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const searchParams = useSearchParams()

  const timeframeOptions = [
    { value: "today", label: "Today", icon: Clock },
    { value: "yesterday", label: "Yesterday", icon: Clock },
    { value: "week", label: "This Week", icon: Calendar },
    { value: "month", label: "This Month", icon: Archive },
  ]

  useEffect(() => {
    const initialMessage = searchParams.get("message")
    if (initialMessage) {
      setMessages([
        {
          id: "1",
          type: "user",
          content: initialMessage,
          timestamp: new Date(),
        },
        {
          id: "2",
          type: "bot",
          content:
            "Hello! I'm Fetchy, your document assistant. I can help you analyze your documents, find specific information, and provide insights about your document processing activities. What would you like to know?",
          timestamp: new Date(),
        },
      ])
    } else {
      setMessages([
        {
          id: "1",
          type: "bot",
          content:
            "Hello! I'm Fetchy, your document assistant. I can help you analyze your documents, find specific information, and provide insights about your document processing activities. What would you like to know?",
          timestamp: new Date(),
        },
      ])
    }
  }, [searchParams])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputMessage,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputMessage("")
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        content: generateBotResponse(inputMessage, selectedTimeframe),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botResponse])
      setIsTyping(false)
    }, 1500)
  }

  const generateBotResponse = (message: string, timeframe: string) => {
    const lowerMessage = message.toLowerCase()

    if (lowerMessage.includes("document") && lowerMessage.includes("count")) {
      return `Based on your ${timeframe || "recent"} activity, you have processed 247 documents. This includes 89 invoices, 62 reports, 45 contracts, and 51 other document types.`
    }

    if (lowerMessage.includes("confidence") || lowerMessage.includes("accuracy")) {
      return `Your average confidence score ${timeframe ? `for ${timeframe}` : "overall"} is 88%. Most documents are classified with high confidence, with only 12% requiring manual review.`
    }

    if (lowerMessage.includes("invoice")) {
      return `I found 89 invoices ${timeframe ? `from ${timeframe}` : "in your system"}. The average processing confidence for invoices is 92%. Would you like me to show you any specific invoice details?`
    }

    if (lowerMessage.includes("report")) {
      return `You have 62 reports ${timeframe ? `from ${timeframe}` : "processed"}. Most reports are classified with 85% average confidence. The most common report types are financial reports and project status updates.`
    }

    if (lowerMessage.includes("help") || lowerMessage.includes("what can you do")) {
      return `I can help you with:
      
• Document statistics and analytics
• Finding specific documents by type or date
• Confidence score analysis
• Classification insights
• Processing workflow status
• Document search and filtering

Just ask me anything about your documents!`
    }

    return `I understand you're asking about "${message}". Let me analyze your document data${timeframe ? ` for ${timeframe}` : ""}... Based on your current document processing activities, I can provide insights about classification accuracy, document types, and processing trends. Could you be more specific about what information you'd like to know?`
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  return (
    <Layout>
      <div className="h-screen flex flex-col bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 md:p-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-[#3452D1] rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-800">Fetchy AI Assistant</h1>
              <p className="text-sm text-gray-500">Your intelligent document companion</p>
            </div>
          </div>
        </div>

        {/* Timeframe Selection */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center space-x-2 overflow-x-auto">
            <span className="text-sm font-medium text-gray-600 whitespace-nowrap">Context:</span>
            {timeframeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedTimeframe(option.value)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors ${
                  selectedTimeframe === option.value
                    ? "bg-[#3452D1] text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <option.icon className="w-4 h-4" />
                <span>{option.label}</span>
              </button>
            ))}
            <button
              onClick={() => setSelectedTimeframe("")}
              className={`px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-colors ${
                selectedTimeframe === "" ? "bg-[#3452D1] text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              All Time
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`flex items-start space-x-3 max-w-3xl ${
                  message.type === "user" ? "flex-row-reverse space-x-reverse" : ""
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === "user" ? "bg-[#3452D1] text-white" : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {message.type === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.type === "user"
                      ? "bg-[#3452D1] text-white"
                      : "bg-white border border-gray-200 text-gray-800"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-2 ${message.type === "user" ? "text-blue-100" : "text-gray-500"}`}>
                    {formatTime(message.timestamp)}
                  </p>
                </div>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-3xl">
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-gray-600" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.1s" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                      style={{ animationDelay: "0.2s" }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 p-4 md:p-6">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your documents..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={1}
                style={{ minHeight: "44px", maxHeight: "120px" }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping}
              className="bg-[#3452D1] text-white p-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Actions */}
          <div className="mt-4 flex flex-wrap gap-2">
            {[
              "Show document count",
              "What's my confidence score?",
              "Find recent invoices",
              "Help me understand reports",
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => setInputMessage(suggestion)}
                className="px-3 py-1.5 text-sm bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
