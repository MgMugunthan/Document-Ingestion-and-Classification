// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5002/api'
const AUTH_BASE_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:5001/api'

// Auth endpoints
export const authApi = {
  login: async (credentials: {
    type: 'single' | 'department'
    userId?: string
    email?: string
    password: string
    captcha: string
  }) => {
    const response = await fetch(`${AUTH_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Login failed')
    }
    
    return response.json()
  },

  verify: async (token: string) => {
    const response = await fetch(`${AUTH_BASE_URL}/auth/verify`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error('Token verification failed')
    }
    
    return response.json()
  },

  register: async (userData: {
    userId: string
    email?: string
    password: string
    userType: 'single' | 'department'
    department?: string
  }) => {
    const response = await fetch(`${AUTH_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Registration failed')
    }
    
    return response.json()
  }
}

// Document endpoints
export const documentApi = {
  upload: async (files: FileList, userId: string, token: string) => {
    const formData = new FormData()
    
    Array.from(files).forEach((file) => {
      formData.append('files', file)
    })
    formData.append('user_id', userId)
    
    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Upload failed')
    }
    
    return response.json()
  },

  getStatus: async (documentId: string, token: string) => {
    const response = await fetch(`${API_BASE_URL}/documents/status/${documentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to get document status')
    }
    
    return response.json()
  },

  list: async (userId: string, token: string, limit = 10, offset = 0) => {
    const response = await fetch(
      `${API_BASE_URL}/documents/list?user_id=${userId}&limit=${limit}&offset=${offset}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to fetch documents')
    }
    
    return response.json()
  }
}

// Utility functions
export const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

export const setAuthToken = (token: string): void => {
  if (typeof window === 'undefined') return
  localStorage.setItem('auth_token', token)
}

export const removeAuthToken = (): void => {
  if (typeof window === 'undefined') return
  localStorage.removeItem('auth_token')
}

export const getUserData = (): any | null => {
  if (typeof window === 'undefined') return null
  const userData = localStorage.getItem('user_data')
  return userData ? JSON.parse(userData) : null
}

export const setUserData = (userData: any): void => {
  if (typeof window === 'undefined') return
  localStorage.setItem('user_data', JSON.stringify(userData))
}

export const removeUserData = (): void => {
  if (typeof window === 'undefined') return
  localStorage.removeItem('user_data')
}

export const logout = (): void => {
  removeAuthToken()
  removeUserData()
  window.location.href = '/login'
}
