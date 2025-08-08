"use client"

import React, { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/contexts/AuthContext'
import { authApi } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { 
  Users, 
  UserPlus, 
  Edit, 
  Trash2, 
  Key, 
  Shield, 
  Search,
  Plus,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

interface User {
  user_id: string
  email: string
  user_type: string
  department: string
  created_at: string | null
  last_login: string | null
}

export default function AdminDashboard() {
  const { user } = useAuth()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  // Form states
  const [formData, setFormData] = useState({
    user_id: '',
    email: '',
    password: '',
    user_type: 'user',
    department: ''
  })
  const [newPassword, setNewPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [successMessage, setSuccessMessage] = useState("")
  const [isAuthChecking, setIsAuthChecking] = useState(true)

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await authApi.admin.getUsers()
      setUsers(response.users)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to fetch users')
    } finally {
      setLoading(false)
    }
  }

  // Check if user is admin - this useEffect must be after all state declarations
  useEffect(() => {
    if (!user || user.user_type !== 'admin') {
      router.push('/upload')
      return
    }
    setIsAuthChecking(false)
    fetchUsers()
  }, [user, router])

  // Show loading spinner while checking authentication
  if (isAuthChecking || !user || user.user_type !== 'admin') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying admin access...</p>
        </div>
      </div>
    )
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await authApi.admin.createUser(formData)
      setSuccessMessage(response.temporary_password 
        ? `User created successfully! Temporary password: ${response.temporary_password}`
        : 'User created successfully!'
      )
      setShowCreateModal(false)
      setFormData({ user_id: '', email: '', password: '', user_type: 'user', department: '' })
      await fetchUsers()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to create user')
    }
  }

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedUser) return
    
    try {
      const updateData = {
        email: formData.email,
        user_type: formData.user_type,
        department: formData.department,
        ...(formData.password && { password: formData.password })
      }
      
      await authApi.admin.updateUser(selectedUser.user_id, updateData)
      setSuccessMessage('User updated successfully!')
      setShowEditModal(false)
      setSelectedUser(null)
      await fetchUsers()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update user')
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return
    
    try {
      await authApi.admin.deleteUser(selectedUser.user_id)
      setSuccessMessage('User deleted successfully!')
      setShowDeleteModal(false)
      setSelectedUser(null)
      await fetchUsers()
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to delete user')
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedUser) return
    
    try {
      await authApi.admin.resetPassword(selectedUser.user_id, newPassword)
      setSuccessMessage('Password reset successfully!')
      setShowPasswordModal(false)
      setSelectedUser(null)
      setNewPassword('')
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to reset password')
    }
  }

  const openEditModal = (user: User) => {
    setSelectedUser(user)
    setFormData({
      user_id: user.user_id,
      email: user.email,
      password: '',
      user_type: user.user_type,
      department: user.department
    })
    setShowEditModal(true)
  }

  const openPasswordModal = (user: User) => {
    setSelectedUser(user)
    setNewPassword('')
    setShowPasswordModal(true)
  }

  const openDeleteModal = (user: User) => {
    setSelectedUser(user)
    setShowDeleteModal(true)
  }

  const filteredUsers = users.filter(user =>
    user.user_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.department.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (!user || user.user_type !== 'admin') {
    return <div>Access denied. Admin rights required.</div>
  }

  return (
    <Layout>
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Shield className="text-blue-600" />
                Admin Dashboard
              </h1>
              <p className="text-gray-600 mt-2">Manage users and system access</p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors"
            >
              <UserPlus size={20} />
              Add User
            </button>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <AlertCircle size={20} />
            {error}
            <button onClick={() => setError("")} className="ml-auto text-red-500 hover:text-red-700">×</button>
          </div>
        )}

        {successMessage && (
          <div className="mb-6 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
            <CheckCircle size={20} />
            {successMessage}
            <button onClick={() => setSuccessMessage("")} className="ml-auto text-green-500 hover:text-green-700">×</button>
          </div>
        )}

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg w-full focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
              <Users size={24} />
              Users ({filteredUsers.length})
            </h2>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading users...</p>
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {searchTerm ? 'No users found matching your search.' : 'No users found.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredUsers.map((user) => (
                    <tr key={user.user_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{user.user_id}</div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          user.user_type === 'admin' 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {user.user_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {user.department || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.last_login 
                          ? new Date(user.last_login).toLocaleDateString()
                          : 'Never'
                        }
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => openEditModal(user)}
                            className="text-blue-600 hover:text-blue-900 p-1"
                            title="Edit user"
                          >
                            <Edit size={16} />
                          </button>
                          <button
                            onClick={() => openPasswordModal(user)}
                            className="text-yellow-600 hover:text-yellow-900 p-1"
                            title="Reset password"
                          >
                            <Key size={16} />
                          </button>
                          {user.user_id !== 'admin' && (
                            <button
                              onClick={() => openDeleteModal(user)}
                              className="text-red-600 hover:text-red-900 p-1"
                              title="Delete user"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Create User Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Create New User</h3>
              <form onSubmit={handleCreateUser}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
                    <input
                      type="text"
                      required
                      value={formData.user_id}
                      onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password <span className="text-gray-500">(leave empty for auto-generated)</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">User Type</label>
                    <select
                      value={formData.user_type}
                      onChange={(e) => setFormData({ ...formData, user_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                    <input
                      type="text"
                      value={formData.department}
                      onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Create User
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false)
                      setFormData({ user_id: '', email: '', password: '', user_type: 'user', department: '' })
                    }}
                    className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit User Modal */}
        {showEditModal && selectedUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Edit User: {selectedUser.user_id}</h3>
              <form onSubmit={handleUpdateUser}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      New Password <span className="text-gray-500">(leave empty to keep current)</span>
                    </label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">User Type</label>
                    <select
                      value={formData.user_type}
                      onChange={(e) => setFormData({ ...formData, user_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                    <input
                      type="text"
                      value={formData.department}
                      onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Update User
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false)
                      setSelectedUser(null)
                    }}
                    className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Reset Password Modal */}
        {showPasswordModal && selectedUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">Reset Password: {selectedUser.user_id}</h3>
              <form onSubmit={handleResetPassword}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                    <input
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      minLength={6}
                    />
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700 transition-colors"
                  >
                    Reset Password
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowPasswordModal(false)
                      setSelectedUser(null)
                      setNewPassword('')
                    }}
                    className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && selectedUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4 text-red-600">Delete User</h3>
              <p className="text-gray-700 mb-6">
                Are you sure you want to delete user <strong>{selectedUser.user_id}</strong>? 
                This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleDeleteUser}
                  className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors"
                >
                  Delete User
                </button>
                <button
                  onClick={() => {
                    setShowDeleteModal(false)
                    setSelectedUser(null)
                  }}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
    </Layout>
  )
}
