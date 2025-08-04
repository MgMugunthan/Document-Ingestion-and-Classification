"use client"

import type React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Shield, Mail, RefreshCw, Lock } from "lucide-react"
import { useAuth } from "@/contexts/AuthContext"

export default function Login() {
  const [activeTab, setActiveTab] = useState("single")
  const [singleUser, setSingleUser] = useState({ userId: "", password: "" })
  const [department, setDepartment] = useState({ email: "", password: "" })
  const [captcha, setCaptcha] = useState({ single: "", department: "" })
  const [showPassword, setShowPassword] = useState({ single: false, department: false })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()
  const { login } = useAuth()

  // Simple captcha generation
  const generateCaptcha = () => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    let result = ""
    for (let i = 0; i < 5; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  const [captchaCode, setCaptchaCode] = useState({
    single: generateCaptcha(),
    department: generateCaptcha(),
  })

  const refreshCaptcha = (type: "single" | "department") => {
    setCaptchaCode((prev) => ({
      ...prev,
      [type]: generateCaptcha(),
    }))
    setCaptcha((prev) => ({
      ...prev,
      [type]: "",
    }))
  }

  const handleLogin = async (e: React.FormEvent, type: "single" | "department") => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      // Validate captcha
      const currentCaptcha = type === "single" ? captcha.single : captcha.department
      const expectedCaptcha = type === "single" ? captchaCode.single : captchaCode.department

      if (currentCaptcha.toUpperCase() !== expectedCaptcha) {
        setError("Invalid captcha. Please try again.")
        refreshCaptcha(type)
        setIsLoading(false)
        return
      }

      // Prepare credentials
      const credentials = {
        type,
        password: type === "single" ? singleUser.password : department.password,
        captcha: currentCaptcha,
        ...(type === "single" 
          ? { userId: singleUser.userId } 
          : { email: department.email }
        )
      }

      // Use real authentication
      await login(credentials)
      
      // Redirect on successful login
      router.push("/upload")

    } catch (error) {
      setIsLoading(false)
      setError(`Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      refreshCaptcha(type)
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
          {/* Tab Headers */}
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab("single")}
              className={`flex-1 py-4 px-6 text-sm font-medium transition-all duration-300 flex items-center justify-center space-x-2 ${
                activeTab === "single"
                  ? "bg-[#3452D1] text-white"
                  : "bg-gray-50 text-gray-600 hover:text-gray-800 hover:bg-gray-100"
              }`}
            >
              <Mail className="w-4 h-4" />
              <span>Single User Login</span>
            </button>
            <button
              onClick={() => setActiveTab("department")}
              className={`flex-1 py-4 px-6 text-sm font-medium transition-all duration-300 flex items-center justify-center space-x-2 ${
                activeTab === "department"
                  ? "bg-[#3452D1] text-white"
                  : "bg-gray-50 text-gray-600 hover:text-gray-800 hover:bg-gray-100"
              }`}
            >
              <Mail className="w-4 h-4" />
              <span>Department Login</span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-8">
            {activeTab === "single" ? (
              <form onSubmit={(e) => handleLogin(e, "single")} className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="userId" className="block text-sm font-medium text-gray-700">
                    User ID
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="userId"
                      type="text"
                      value={singleUser.userId}
                      onChange={(e) => setSingleUser({ ...singleUser, userId: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500"
                      placeholder="Enter your user ID"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="singlePassword" className="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="singlePassword"
                      type={showPassword.single ? "text" : "password"}
                      value={singleUser.password}
                      onChange={(e) => setSingleUser({ ...singleUser, password: e.target.value })}
                      className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500"
                      placeholder="Enter your password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => ({ ...prev, single: !prev.single }))}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      {showPassword.single ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Enhanced Captcha */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Security Verification</label>
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="bg-gray-100 px-4 py-3 rounded-lg font-mono text-lg tracking-wider border-2 border-dashed border-gray-300 text-gray-800">
                        {captchaCode.single}
                      </div>
                      <Shield className="absolute -top-2 -right-2 w-5 h-5 text-[#3452D1]" />
                    </div>
                    <button
                      type="button"
                      onClick={() => refreshCaptcha("single")}
                      className="p-3 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors border border-gray-300"
                    >
                      <RefreshCw className="w-4 h-4 text-gray-600" />
                    </button>
                    <input
                      type="text"
                      value={captcha.single}
                      onChange={(e) => setCaptcha({ ...captcha, single: e.target.value })}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent text-gray-900 placeholder-gray-500"
                      placeholder="Enter code"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-[#3452D1] text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Signing in...
                    </div>
                  ) : (
                    "Sign In"
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={(e) => handleLogin(e, "department")} className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Department Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="email"
                      type="email"
                      value={department.email}
                      onChange={(e) => setDepartment({ ...department, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500"
                      placeholder="department@company.com"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="deptPassword" className="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="deptPassword"
                      type={showPassword.department ? "text" : "password"}
                      value={department.password}
                      onChange={(e) => setDepartment({ ...department, password: e.target.value })}
                      className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500"
                      placeholder="Enter department password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => ({ ...prev, department: !prev.department }))}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      {showPassword.department ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Enhanced Captcha */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">Security Verification</label>
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="bg-gray-100 px-4 py-3 rounded-lg font-mono text-lg tracking-wider border-2 border-dashed border-gray-300 text-gray-800">
                        {captchaCode.department}
                      </div>
                      <Shield className="absolute -top-2 -right-2 w-5 h-5 text-[#3452D1]" />
                    </div>
                    <button
                      type="button"
                      onClick={() => refreshCaptcha("department")}
                      className="p-3 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors border border-gray-300"
                    >
                      <RefreshCw className="w-4 h-4 text-gray-600" />
                    </button>
                    <input
                      type="text"
                      value={captcha.department}
                      onChange={(e) => setCaptcha({ ...captcha, department: e.target.value })}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#3452D1] focus:border-transparent text-gray-900 placeholder-gray-500"
                      placeholder="Enter code"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-[#3452D1] text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Signing in...
                    </div>
                  ) : (
                    "Sign In"
                  )}
                </button>
              </form>
            )}
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
