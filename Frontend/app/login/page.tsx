"use client"

import type React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Shield, Mail, Lock } from "lucide-react"
import { useAuth } from "@/contexts/AuthContext"


export default function Login() {
  const [credentials, setCredentials] = useState({ user_id: "", password: "" })
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()
  const { login } = useAuth()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      // Simple login with user_id and password
      await login({
        user_id: credentials.user_id,
        password: credentials.password
      })
      
      // Redirect on successful login
      router.push("/upload")

    } catch (error) {
      setIsLoading(false)
      setError(`Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 relative">
      {/* Subtle Background Pattern */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-blue-50 opacity-50"></div>

      {/* Floating Elements for Visual Interest */}
      <div className="absolute top-20 left-20 w-32 h-32 bg-blue-100 rounded-full opacity-20 animate-pulse"></div>
      <div className="absolute bottom-20 right-20 w-24 h-24 bg-[#3452D1] rounded-full opacity-10 animate-pulse animation-delay-2000"></div>
      <div className="absolute top-1/2 left-10 w-16 h-16 bg-gray-200 rounded-full opacity-30 animate-bounce"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-white rounded-2xl shadow-lg mb-6 border border-gray-200">
            <svg className="w-12 h-12 text-[#3452D1]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome to Dokmanic</h1>
          <p className="text-gray-600">Intelligent Document Processing System</p>
        </div>

        {/* Login Form with Clean Design */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          {/* Simple Header */}
          <div className="bg-[#3452D1] text-white py-4 px-6">
            <h2 className="text-lg font-medium flex items-center space-x-2">
              <Mail className="w-5 h-5" />
              <span>Login to Document System</span>
            </h2>
          </div>

          {/* Simple Login Form */}
          <div className="p-8">
            <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="user_id" className="block text-sm font-medium text-gray-700">
                  User ID
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="user_id"
                    type="text"
                    value={credentials.user_id}
                    onChange={(e) => setCredentials({ ...credentials, user_id: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500"
                    placeholder="Enter your user ID (e.g., admin)"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={credentials.password}
                    onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500"
                    placeholder="Enter your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 text-red-500">⚠️</div>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-[#3452D1] text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-[#3452D1] focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Signing in...</span>
                  </div>
                ) : (
                  "Sign In"
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Security Notice */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500 flex items-center justify-center space-x-2">
            <Shield className="w-4 h-4" />
            <span>Secure login protected by advanced encryption</span>
          </p>
        </div>
      </div>
    </div>
  )
}
