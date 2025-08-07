"use client"

import type React from "react"

import { useState } from "react"
import { usePathname } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { Menu, X, Upload, BarChart3, FileText, Eye, Bot, Shield, LogOut } from "lucide-react"
import { useAuth } from "@/contexts/AuthContext"

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const { user, logout } = useAuth()

  const navigation = [
    { name: "Upload", href: "/upload", icon: Upload },
    { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
    { name: "Documents", href: "/documents", icon: FileText },
    { name: "Review", href: "/review", icon: Eye },
    { name: "AI Tool", href: "/ai-tool", icon: Bot },
  ]

  // Add admin link if user is admin
  if (user?.user_type === 'admin') {
    navigation.push({ name: "Admin", href: "/admin", icon: Shield })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="bg-white p-2 rounded-lg shadow-lg border border-gray-200"
        >
          {sidebarOpen ? <X className="h-6 w-6 text-gray-600" /> : <Menu className="h-6 w-6 text-gray-600" />}
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-20 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <Image src="/dokmanic-logo.png" alt="Dokmanic Logo" width={40} height={40} className="object-contain" />
              <span className="text-xl font-bold text-gray-800">Dokmanic</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 group ${
                    isActive
                      ? "bg-[#3452D1] text-white shadow-lg"
                      : "text-gray-600 hover:bg-blue-50 hover:text-[#3452D1]"
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 transition-transform duration-200 group-hover:scale-110 ${
                      isActive ? "text-white" : "text-gray-400 group-hover:text-[#3452D1]"
                    }`}
                  />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 min-w-0 flex-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  user?.user_type === 'admin' ? 'bg-purple-600' : 'bg-[#3452D1]'
                }`}>
                  <span className="text-white text-sm font-medium">
                    {user?.user_id ? user.user_id.charAt(0).toUpperCase() : 'U'}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {user?.user_id || 'User'}
                    {user?.user_type === 'admin' && (
                      <span className="ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                        Admin
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 truncate" title={user?.email || 'user@dokmanic.com'}>
                    {user?.email || 'user@dokmanic.com'}
                  </p>
                </div>
              </div>
              <button
                onClick={logout}
                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black bg-opacity-50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main content */}
      <div className="lg:pl-64">
        <main className="min-h-screen">{children}</main>
      </div>
    </div>
  )
}
