// API configuration
const INGESTOR_BASE_URL = process.env.NEXT_PUBLIC_INGESTOR_URL || 'http://localhost:5000'
const AUTH_BASE_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:5001'

// Auth endpoints
export const authApi = {
  login: async (credentials: {
    user_id: string
    password: string
  }) => {
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/login`, {
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
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({token}),
    })
    
    if (!response.ok) {
      throw new Error('Token verification failed')
    }
    
    return response.json()
  },

  refresh: async () => {
    const response = await makeAuthenticatedRequest(`${AUTH_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Token refresh failed')
    }
    
    return response.json()
  },

  register: async (userData: {
    user_id: string
    email: string
    password: string
    user_Type?: string
    department?: string
  }) => {
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/register`, {
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
  },
  getStatus: async () => {
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/status`)
    return response.json()
  },

  // Admin user management endpoints
  admin: {
    getUsers: async () => {
      const response = await makeAuthenticatedRequest(`${AUTH_BASE_URL}/api/auth/admin/users`)
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to fetch users')
      }
      
      return response.json()
    },

    createUser: async (userData: {
      user_id: string
      email: string
      password?: string
      user_type?: string
      department?: string
    }) => {
      const response = await makeAuthenticatedRequest(`${AUTH_BASE_URL}/api/auth/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to create user')
      }
      
      return response.json()
    },

    updateUser: async (userId: string, userData: {
      email?: string
      user_type?: string
      department?: string
      password?: string
    }) => {
      const response = await makeAuthenticatedRequest(`${AUTH_BASE_URL}/api/auth/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to update user')
      }
      
      return response.json()
    },

    deleteUser: async (userId: string) => {
      const response = await makeAuthenticatedRequest(`${AUTH_BASE_URL}/api/auth/admin/users/${userId}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to delete user')
      }
      
      return response.json()
    },

    resetPassword: async (userId: string, newPassword: string) => {
      const response = await makeAuthenticatedRequest(`${AUTH_BASE_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          new_password: newPassword
        }),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to reset password')
      }
      
      return response.json()
    }
  }
}

// Document endpoints
export const documentApi = {
  upload: async (file: File, metadata: any= {}) => {
    const formData = new FormData()
    formData.append('document', file)
    formData.append('metadata', JSON.stringify(metadata))
    
    const response = await fetch(`${INGESTOR_BASE_URL}/api/receive`, {
      method: 'POST',
      body: formData,
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Upload failed')
    }
    
    return response.json()
  },

  getStatus: async (documentId: string) => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/document/${documentId}/status`)

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to get document status')
    }
    
    return response.json()
  },

  list: async (userId: string) => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/documents/user/${userId}`)
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to fetch documents')
    }
    
    return response.json()
  }
}

// Gmail endpoints
export const gmailApi = {
  search: async (prompt: string) => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/gmail/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Gmail search failed')
    }
    
    return response.json()
  },

  processSelected: async (fileIds: string[]) => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/gmail/process-selected`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_ids: fileIds }),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Gmail processing failed')
    }
    
    return response.json()
  },

  fetch: async () => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/gmail/fetch`, {
      method: 'POST',
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Gmail fetch failed')
    }
    
    return response.json()
  },

  getStatus: async () => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/gmail/status`)
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
  if (typeof window !== 'undefined') {
    window.location.href = '/login'
  }
}

// System status endpoints
export const systemApi = {
  getIngestorStatus: async () => {
    const response = await fetch(`${INGESTOR_BASE_URL}/api/status`)
    return response.json()
  },

  getAuthStatus: async () => {
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/status`)
    return response.json()
  }
}

// Helper function for authenticated requests with automatic token refresh
export const makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken()
  
  if (token) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
    }
  }
  
  const response = await fetch(url, options)
  
  // If we get 401 (unauthorized), try to refresh the token and retry once
  if (response.status === 401 && token) {
    try {
      const refreshResponse = await authApi.refresh()
      const { token: newToken } = refreshResponse
      
      // Update stored token
      setAuthToken(newToken)
      
      // Retry the original request with new token
      options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${newToken}`,
      }
      
      return fetch(url, options)
    } catch (refreshError) {
      // Refresh failed, redirect to login
      removeAuthToken()
      removeUserData()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
      throw new Error('Session expired, please login again')
    }
  }
  
  return response
}
