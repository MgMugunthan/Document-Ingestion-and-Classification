"use client"

import type React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Eye, EyeOff, Shield, Users, User, RefreshCw, Sparkles, Lock, Mail } from "lucide-react"

export default function Login() {
  const [activeTab, setActiveTab] = useState("single")
  const [singleUser, setSingleUser] = useState({ userId: "", password: "" })
  const [department, setDepartment] = useState({ email: "", password: "" })
  const [captcha, setCaptcha] = useState({ single: "", department: "" })
  const [showPassword, setShowPassword] = useState({ single: false, department: false })
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

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

    // Validate captcha
    const currentCaptcha = type === "single" ? captcha.single : captcha.department
    const expectedCaptcha = type === "single" ? captchaCode.single : captchaCode.department

    if (currentCaptcha.toUpperCase() !== expectedCaptcha) {
      alert("Invalid captcha. Please try again.")
      refreshCaptcha(type)
      setIsLoading(false)
      return
    }

    // Simulate login process
    setTimeout(() => {
      setIsLoading(false)
      router.push("/upload")
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
      </div>

      {/* Floating Particles */}
      <div className="absolute inset-0">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-white rounded-full opacity-20 animate-bounce"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${3 + Math.random() * 2}s`,
            }}
          />
        ))}
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl shadow-2xl mb-6 relative">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-purple-500 rounded-3xl blur opacity-75 animate-pulse"></div>
            <div className="relative w-16 h-16 bg-white rounded-2xl flex items-center justify-center">
              <svg className="w-10 h-10 text-[#3452D1]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
              </svg>
            </div>
            <Sparkles className="absolute -top-2 -right-2 w-6 h-6 text-yellow-300 animate-spin" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Dokmanic
          </h1>
          <p className="text-blue-200 text-lg">Intelligent Document Processing</p>
        </div>

        {/* Login Form with Creative Design */}
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
          {/* Tab Headers */}
          <div className="flex relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 opacity-20"></div>
            <button
              onClick={() => setActiveTab("single")}
              className={`flex-1 py-6 px-6 text-sm font-medium transition-all duration-300 relative z-10 flex items-center justify-center space-x-2 ${
                activeTab === "single"
                  ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg"
                  : "text-blue-200 hover:text-white hover:bg-white/10"
              }`}
            >
              <User className="w-5 h-5" />
              <span>Single User</span>
            </button>
            <button
              onClick={() => setActiveTab("department")}
              className={`flex-1 py-6 px-6 text-sm font-medium transition-all duration-300 relative z-10 flex items-center justify-center space-x-2 ${
                activeTab === "department"
                  ? "bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg"
                  : "text-blue-200 hover:text-white hover:bg-white/10"
              }`}
            >
              <Users className="w-5 h-5" />
              <span>Department</span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-8">
            {activeTab === "single" ? (
              <form onSubmit={(e) => handleLogin(e, "single")} className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="userId" className="block text-sm font-medium text-blue-100">
                    User ID
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-blue-300" />
                    <input
                      id="userId"
                      type="text"
                      value={singleUser.userId}
                      onChange={(e) => setSingleUser({ ...singleUser, userId: e.target.value })}
                      className="w-full pl-10 pr-4 py-4 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-white placeholder-blue-200 backdrop-blur-sm"
                      placeholder="Enter your user ID"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="singlePassword" className="block text-sm font-medium text-blue-100">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-blue-300" />
                    <input
                      id="singlePassword"
                      type={showPassword.single ? "text" : "password"}
                      value={singleUser.password}
                      onChange={(e) => setSingleUser({ ...singleUser, password: e.target.value })}
                      className="w-full pl-10 pr-12 py-4 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-white placeholder-blue-200 backdrop-blur-sm"
                      placeholder="Enter your password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => ({ ...prev, single: !prev.single }))}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-blue-300 hover:text-white transition-colors"
                    >
                      {showPassword.single ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Enhanced Captcha */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-blue-100">Security Verification</label>
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 rounded-xl font-mono text-xl tracking-wider text-white border-2 border-dashed border-white/30 shadow-lg">
                        {captchaCode.single}
                      </div>
                      <Shield className="absolute -top-2 -right-2 w-6 h-6 text-yellow-300" />
                    </div>
                    <button
                      type="button"
                      onClick={() => refreshCaptcha("single")}
                      className="p-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors border border-white/20"
                    >
                      <RefreshCw className="w-5 h-5 text-blue-300" />
                    </button>
                    <input
                      type="text"
                      value={captcha.single}
                      onChange={(e) => setCaptcha({ ...captcha, single: e.target.value })}
                      className="flex-1 px-4 py-4 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-transparent text-white placeholder-blue-200 backdrop-blur-sm"
                      placeholder="Enter code"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-4 px-6 rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 focus:ring-4 focus:ring-blue-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                      Authenticating...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <span>Sign In</span>
                      <Sparkles className="w-5 h-5" />
                    </div>
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={(e) => handleLogin(e, "department")} className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="email" className="block text-sm font-medium text-blue-100">
                    Department Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-300" />
                    <input
                      id="email"
                      type="email"
                      value={department.email}
                      onChange={(e) => setDepartment({ ...department, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-4 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-200 text-white placeholder-purple-200 backdrop-blur-sm"
                      placeholder="department@company.com"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="deptPassword" className="block text-sm font-medium text-blue-100">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-300" />
                    <input
                      id="deptPassword"
                      type={showPassword.department ? "text" : "password"}
                      value={department.password}
                      onChange={(e) => setDepartment({ ...department, password: e.target.value })}
                      className="w-full pl-10 pr-12 py-4 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-200 text-white placeholder-purple-200 backdrop-blur-sm"
                      placeholder="Enter department password"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => ({ ...prev, department: !prev.department }))}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-300 hover:text-white transition-colors"
                    >
                      {showPassword.department ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Enhanced Captcha */}
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-blue-100">Security Verification</label>
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="bg-gradient-to-r from-purple-600 to-pink-600 px-6 py-4 rounded-xl font-mono text-xl tracking-wider text-white border-2 border-dashed border-white/30 shadow-lg">
                        {captchaCode.department}
                      </div>
                      <Shield className="absolute -top-2 -right-2 w-6 h-6 text-yellow-300" />
                    </div>
                    <button
                      type="button"
                      onClick={() => refreshCaptcha("department")}
                      className="p-3 bg-white/10 rounded-xl hover:bg-white/20 transition-colors border border-white/20"
                    >
                      <RefreshCw className="w-5 h-5 text-purple-300" />
                    </button>
                    <input
                      type="text"
                      value={captcha.department}
                      onChange={(e) => setCaptcha({ ...captcha, department: e.target.value })}
                      className="flex-1 px-4 py-4 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-purple-400 focus:border-transparent text-white placeholder-purple-200 backdrop-blur-sm"
                      placeholder="Enter code"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white py-4 px-6 rounded-xl font-medium hover:from-purple-600 hover:to-pink-700 focus:ring-4 focus:ring-purple-200 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-1"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                      Authenticating...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center space-x-2">
                      <span>Sign In</span>
                      <Sparkles className="w-5 h-5" />
                    </div>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Footer Text */}
        <div className="text-center mt-8">
          <p className="text-blue-200 text-sm">Secure • Intelligent • Efficient</p>
        </div>
      </div>
    </div>
  )
}
