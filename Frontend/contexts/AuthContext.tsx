"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi, getAuthToken, setAuthToken, removeAuthToken, getUserData, setUserData, removeUserData } from '@/lib/api'

interface User {
  user_id: string
  user_type: string
  email?: string
  department?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
  refreshAuth: () => Promise<void>
}

interface LoginCredentials {
  user_id: string
  password: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [refreshTimeoutId, setRefreshTimeoutId] = useState<NodeJS.Timeout | null>(null)
  const router = useRouter()

  const isAuthenticated = !!user && !!token

  // Auto-refresh token before expiration
  const scheduleTokenRefresh = (token: string) => {
    try {
      // Clear any existing timeout
      if (refreshTimeoutId) {
        clearTimeout(refreshTimeoutId)
      }

      // Decode token to get expiration time
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expirationTime = payload.exp * 1000 // Convert to milliseconds
      const currentTime = Date.now()
      const timeUntilExpiry = expirationTime - currentTime
      
      // Refresh token 30 minutes before expiration (or immediately if less than 30 min remaining)
      const refreshTime = Math.max(timeUntilExpiry - (30 * 60 * 1000), 1000)
      
      const timeoutId = setTimeout(async () => {
        try {
          const response = await authApi.refresh()
          const { token: newToken, user: userData } = response
          
          setToken(newToken)
          setUser(userData)
          setAuthToken(newToken)
          setUserData(userData)
          
          // Schedule next refresh
          scheduleTokenRefresh(newToken)
        } catch (error) {
          console.warn('Token refresh failed, user may need to login again')
          // Don't automatically logout on refresh failure, let user continue until they try to make a request
        }
      }, refreshTime)

      setRefreshTimeoutId(timeoutId)
    } catch (error) {
      console.warn('Failed to schedule token refresh:', error)
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      // Call the API with the correct format that matches backend
      const response = await authApi.login({
        user_id: credentials.user_id,
        password: credentials.password
      })
      
      const { token: newToken, user: userData } = response
      
      setToken(newToken)
      setUser(userData)
      setAuthToken(newToken)
      setUserData(userData)
      
      // Schedule automatic token refresh
      scheduleTokenRefresh(newToken)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    // Clear any scheduled token refresh
    if (refreshTimeoutId) {
      clearTimeout(refreshTimeoutId)
      setRefreshTimeoutId(null)
    }

    // Clear all authentication data
    setUser(null)
    setToken(null)
    removeAuthToken()
    removeUserData()
    
    // Force redirect to login page
    router.replace('/login')
  }

  const refreshAuth = async () => {
    const storedToken = getAuthToken()
    const storedUser = getUserData()
    
    if (storedToken && storedUser) {
      try {
        // Verify token is still valid
        await authApi.verify(storedToken)
        setToken(storedToken)
        setUser(storedUser)
        
        // Schedule automatic token refresh for existing session
        scheduleTokenRefresh(storedToken)
      } catch (error) {
        // Token is invalid, try to refresh it
        try {
          const response = await authApi.refresh()
          const { token: newToken, user: userData } = response
          
          setToken(newToken)
          setUser(userData)
          setAuthToken(newToken)
          setUserData(userData)
          
          // Schedule next refresh
          scheduleTokenRefresh(newToken)
        } catch (refreshError) {
          // Both verification and refresh failed, clear stored data without redirect
          setUser(null)
          setToken(null)
          removeAuthToken()
          removeUserData()
        }
      }
    }
    setIsLoading(false)
  }

  useEffect(() => {
    refreshAuth()
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated,
        login,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
