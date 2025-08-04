"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { authApi, getAuthToken, setAuthToken, removeAuthToken, getUserData, setUserData, removeUserData } from '@/lib/api'

interface User {
  user_id: string
  user_type: 'single' | 'department'
  email?: string
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
  type: 'single' | 'department'
  userId?: string
  email?: string
  password: string
  captcha: string
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

  const isAuthenticated = !!user && !!token

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await authApi.login(credentials)
      const { token: newToken, user: userData } = response
      
      setToken(newToken)
      setUser(userData)
      setAuthToken(newToken)
      setUserData(userData)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    removeAuthToken()
    removeUserData()
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
      } catch (error) {
        // Token is invalid, clear stored data
        logout()
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
