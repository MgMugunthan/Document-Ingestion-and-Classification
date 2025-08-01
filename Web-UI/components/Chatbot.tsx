"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Send, Calendar, Clock, Archive, Heart } from "lucide-react"

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState("")
  const [selectedTimeframe, setSelectedTimeframe] = useState("")
  const router = useRouter()

  const handleSendMessage = () => {
    if (message.trim()) {
      router.push(`/ai-tool?message=${encodeURIComponent(message)}`)
    }
  }

  const timeframeOptions = [
    { value: "today", label: "Today", icon: Clock },
    { value: "yesterday", label: "Yesterday", icon: Clock },
    { value: "week", label: "This Week", icon: Calendar },
    { value: "month", label: "This Month", icon: Archive },
  ]

  return (
    <>
      {/* Chatbot Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-14 h-14 md:w-16 md:h-16 bg-[#3452D1] rounded-full shadow-lg flex items-center justify-center text-white hover:shadow-xl transition-all duration-300 hover:scale-110 animate-pulse"
        >
          {/* Puppy Icon using SVG */}
          <svg className="w-8 h-8 md:w-9 md:h-9" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4.5 12a7.5 7.5 0 0015 0 7.5 7.5 0 00-15 0z" />
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-1.5-1.5L10 14l-1.5-1.5L10 11l1.5 1.5L13 11l1.5 1.5L13 14l1.5 1.5L13 17l-1.5-1.5L10 17z" />
            <circle cx="9" cy="9" r="1" />
            <circle cx="15" cy="9" r="1" />
          </svg>
        </button>
      </div>

      {/* Chatbot Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 md:w-96 h-96 bg-white rounded-2xl shadow-2xl border border-gray-200 z-50 flex flex-col">
          {/* Header */}
          <div className="bg-[#3452D1] text-white p-4 rounded-t-2xl">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Heart className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold">Hi! I'm Fetchy</h3>
                <p className="text-sm opacity-90">How can I help you with routing mail documents?</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 p-4 space-y-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-600">
                I can help you route and manage your mail documents efficiently. What would you like to know about
                document processing?
              </p>
            </div>

            {/* Timeframe Selection */}
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Select timeframe:</p>
              <div className="grid grid-cols-2 gap-2">
                {timeframeOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSelectedTimeframe(option.value)}
                    className={`flex items-center space-x-2 p-2 rounded-lg text-sm transition-colors ${
                      selectedTimeframe === option.value
                        ? "bg-[#3452D1] text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    <option.icon className="w-4 h-4" />
                    <span>{option.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask me anything..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
              />
              <button
                onClick={handleSendMessage}
                className="bg-[#3452D1] text-white p-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
