"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
  redirectTo?: string
}

export default function ProtectedRoute({ 
  children, 
  requireAdmin = false, 
  redirectTo = '/login' 
}: ProtectedRouteProps) {
  const { user, token } = useAuth()
  const router = useRouter()
  const [isChecking, setIsChecking] = useState(true)

  useEffect(() => {
    if (!user || !token) {
      router.replace(redirectTo)
      return
    }

    if (requireAdmin && user.user_type !== 'admin') {
      router.replace('/upload')
      return
    }

    setIsChecking(false)
  }, [user, token, requireAdmin, router, redirectTo])

  if (isChecking || !user || !token || (requireAdmin && user.user_type !== 'admin')) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">
            {requireAdmin ? 'Verifying admin access...' : 'Verifying authentication...'}
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
