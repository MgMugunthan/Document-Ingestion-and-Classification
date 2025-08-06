"use client"

import React, { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface AuthGuardProps {
  children: React.ReactNode
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // Don't redirect while auth is loading
    if (isLoading) return

    // Define public routes that don't require authentication
    const publicRoutes = ['/login', '/register']
    const isPublicRoute = publicRoutes.includes(pathname)

    if (!isAuthenticated && !isPublicRoute) {
      // User is not authenticated and trying to access protected route
      router.replace('/login')
    } else if (isAuthenticated && pathname === '/login') {
      // User is authenticated but on login page, redirect to upload
      router.replace('/upload')
    }
  }, [isAuthenticated, isLoading, pathname, router])

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3452D1] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
