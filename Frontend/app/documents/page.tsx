'use client'

import { useState, useEffect } from 'react'
import Layout from "@/components/Layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { 
  FileText, 
  Search, 
  Filter, 
  Eye, 
  Trash2, 
  RefreshCw, 
  Download,
  ArrowUpDown,
  MoreHorizontal,
  Route,
  Tag,
  Calendar,
  HardDrive,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react'
import { useToast } from "@/hooks/use-toast"
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { documentApi } from '@/lib/api'

interface Document {
  document_id: string
  user_id: string
  document_name: string
  original_filename: string
  file_path: string
  file_size: number
  file_size_formatted: string
  file_extension: string
  upload_timestamp: string
  processing_status: string
  classification_type: string
  classification_confidence: string
  classification_method: string
  confidence_score: number
  routed_path: string
  final_path: string
  updated_at: string
  created_at: string
}

interface DocumentType {
  type: string
  count: number
}

interface RouteOption {
  routes: { [key: string]: string }
  folders: string[]
  default_folder: string
  needs_action_folder: string
}

export default function DocumentsPage() {
  // Authentication must be first
  const { user, token, isLoading } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  
  // State hooks - all must be called every render
  const [documents, setDocuments] = useState<Document[]>([])
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([])
  const [routeOptions, setRouteOptions] = useState<RouteOption | null>(null)
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  
  // Filters and pagination
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [sortBy, setSortBy] = useState('upload_timestamp')
  const [sortOrder, setSortOrder] = useState('DESC')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  
  // Modal states
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [showViewModal, setShowViewModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showRerouteModal, setShowRerouteModal] = useState(false)
  const [showReclassifyModal, setShowReclassifyModal] = useState(false)
  
  // Form states
  const [newRoute, setNewRoute] = useState('')
  const [newFolder, setNewFolder] = useState('')
  const [newClassification, setNewClassification] = useState('')

  // Authentication check - redirect to login if not authenticated
  useEffect(() => {
    // Wait for auth loading to complete before checking authentication
    if (isLoading) return
    
    if (!user || !token) {
      router.replace('/login')
      return
    }
  }, [user, token, isLoading, router])

  // Helper function for safe JSON parsing
  const safeJsonParse = async (response: Response, context: string) => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const text = await response.text()
    try {
      return JSON.parse(text)
    } catch (parseError) {
      console.error(`JSON parse error in ${context}:`, parseError)
      console.error('Response text:', text)
      throw new Error(`Invalid JSON response from ${context}`)
    }
  }

  // Load documents function
  const loadDocuments = async () => {
    if (!user || !token) return
    
    try {
      setLoading(true)
      
      // Use the proper documentApi to get documents
      const result = await documentApi.list(user.user_id)
      
      if (result.documents) {
        // Map API response to Document interface
        const mappedDocs = result.documents.map((doc: any) => ({
          ...doc,
          document_name: doc.original_filename || doc.document_name || 'Unknown Document',
          confidence_score: doc.classification_confidence ? parseFloat(doc.classification_confidence) : 0,
          routed_path: doc.final_path || doc.routed_path
        }))

        // Filter documents based on search and status
        let filteredDocs = mappedDocs
        
        // Apply search filter
        if (searchTerm) {
          filteredDocs = filteredDocs.filter((doc: Document) => 
            doc.document_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            doc.classification_type?.toLowerCase().includes(searchTerm.toLowerCase())
          )
        }
        
        // Apply status filter
        if (selectedStatus && selectedStatus !== 'all') {
          filteredDocs = filteredDocs.filter((doc: Document) => 
            doc.processing_status === selectedStatus
          )
        }
        
        // Apply type filter
        if (selectedType && selectedType !== 'all') {
          filteredDocs = filteredDocs.filter((doc: Document) => 
            doc.classification_type === selectedType
          )
        }
        
        // Apply sorting
        filteredDocs.sort((a: Document, b: Document) => {
          let aValue: any, bValue: any
          
          switch (sortBy) {
            case 'upload_timestamp':
              aValue = new Date(a.upload_timestamp).getTime()
              bValue = new Date(b.upload_timestamp).getTime()
              break
            case 'document_name':
              aValue = a.document_name.toLowerCase()
              bValue = b.document_name.toLowerCase()
              break
            case 'file_size':
              aValue = a.file_size
              bValue = b.file_size
              break
            case 'confidence_score':
              aValue = a.confidence_score || 0
              bValue = b.confidence_score || 0
              break
            default:
              aValue = a.upload_timestamp
              bValue = b.upload_timestamp
          }
          
          if (sortOrder === 'ASC') {
            return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
          } else {
            return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
          }
        })
        
        // Apply pagination
        const startIndex = (currentPage - 1) * pageSize
        const paginatedDocs = filteredDocs.slice(startIndex, startIndex + pageSize)
        
        setDocuments(paginatedDocs)
        setTotalCount(filteredDocs.length)
        
        console.log(`📄 Loaded ${result.documents.length} documents, showing ${paginatedDocs.length} after filters`)
      } else {
        throw new Error('No documents data in response')
      }
    } catch (error) {
      console.error('Error loading documents:', error)
      toast({
        title: "Error",
        description: `Failed to load documents: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Load document types function
  const loadDocumentTypes = async () => {
    if (!user || !token) return
    
    try {
      // Get documents to extract types
      const result = await documentApi.list(user.user_id)
      
      if (result.documents) {
        // Extract unique document types from the documents
        const types = result.documents.reduce((acc: DocumentType[], doc: Document) => {
          if (doc.classification_type) {
            const existingType = acc.find(t => t.type === doc.classification_type)
            if (existingType) {
              existingType.count++
            } else {
              acc.push({ type: doc.classification_type, count: 1 })
            }
          }
          return acc
        }, [])
        
        setDocumentTypes(types)
        console.log(`📊 Found ${types.length} document types:`, types)
      }
    } catch (error) {
      console.error('Error loading document types:', error)
    }
  }

  // Load route options function
  const loadRouteOptions = async () => {
    if (!user || !token) return
    
    try {
      const response = await fetch('/api/documents/routes', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.routes) {
          setRouteOptions(result.routes)
          console.log('📁 Loaded route options from server:', result.routes)
        } else {
          throw new Error('Failed to get routes from server')
        }
      } else {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Error loading route options:', error)
      // Fallback to default routes if server fails
      const defaultRoutes = {
        routes: {
          "resume": "resumes",
          "cv": "resumes",
          "receipt": "receipts",
          "invoice": "invoices",
          "bill": "bills"
        },
        folders: ["resumes", "receipts", "invoices", "bills", "others"],
        default_folder: "others",
        needs_action_folder: "needs_action"
      }
      setRouteOptions(defaultRoutes)
      console.log('📁 Using fallback route options')
    }
  }

  // Effect to load data when authenticated
  useEffect(() => {
    if (user && token) {
      loadDocuments()
      loadDocumentTypes()
      loadRouteOptions()
    }
  }, [currentPage, searchTerm, selectedType, selectedStatus, sortBy, sortOrder, user, token])

  // Handler functions
  const handleDelete = async () => {
    if (!selectedDocument || !user || !token) return
    
    try {
      const response = await fetch(`/api/documents/${selectedDocument.document_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      const result = await response.json()
      
      if (result.success) {
        toast({
          title: "Success",
          description: result.message,
        })
        loadDocuments()
        setShowDeleteModal(false)
        setSelectedDocument(null)
      } else {
        throw new Error(result.error || 'Failed to delete document')
      }
    } catch (error) {
      console.error('Error deleting document:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete document",
        variant: "destructive",
      })
    }
  }

  const handleReroute = async () => {
    if (!selectedDocument || !user || !token) return
    
    if (!newRoute && !newFolder) {
      toast({
        title: "Error", 
        description: "Please select a route or enter a custom folder",
        variant: "destructive"
      })
      return
    }
    
    try {
      const body: any = {}
      if (newRoute) body.route = newRoute
      if (newFolder) body.folder = newFolder
      
      const response = await fetch(`/api/documents/${selectedDocument.document_id}/reroute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body)
      })
      
      const result = await response.json()
      
      if (result.success) {
        toast({
          title: "Success",
          description: result.message,
        })
        loadDocuments()
        setShowRerouteModal(false)
        setSelectedDocument(null)
        setNewRoute('')
        setNewFolder('')
      } else {
        throw new Error(result.error || 'Failed to reroute document')
      }
    } catch (error) {
      console.error('Error rerouting document:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to reroute document",
        variant: "destructive",
      })
    }
  }

  const handleReclassify = async () => {
    if (!selectedDocument || !newClassification || !user || !token) return
    
    try {
      const response = await fetch(`/api/documents/${selectedDocument.document_id}/reclassify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_classification: newClassification })
      })
      
      const result = await response.json()
      
      if (result.success) {
        toast({
          title: "Success",
          description: result.message,
        })
        loadDocuments()
        setShowReclassifyModal(false)
        setSelectedDocument(null)
        setNewClassification('')
      } else {
        throw new Error(result.error)
      }
    } catch (error) {
      console.error('Error reclassifying document:', error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to reclassify document",
        variant: "destructive",
      })
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    const diffInDays = Math.floor(diffInHours / 24)

    // Show relative time for recent uploads
    if (diffInHours < 1) {
      const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
      if (diffInMinutes < 1) return 'Just now'
      return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`
    } else if (diffInDays < 7) {
      return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`
    }

    // For older dates, show formatted date and time in local timezone
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    })
  }

  const formatAbsoluteDate = (dateString: string): string => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      timeZoneName: 'short'
    })
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
      case 'routed':
        return 'default'
      case 'processing':
      case 'extracted':
      case 'classified':
        return 'secondary'
      case 'error':
      case 'failed':
      case 'needs_action':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'routed':
        return <CheckCircle className="h-4 w-4" />
      case 'processing':
      case 'extracted':
      case 'classified':
        return <Clock className="h-4 w-4" />
      case 'error':
      case 'failed':
      case 'needs_action':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  // Show loading spinner while checking authentication
  if (isLoading || !user || !token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">
            {isLoading ? "Loading..." : "Verifying authentication..."}
          </p>
        </div>
      </div>
    )
  }

  const totalPages = Math.ceil(totalCount / pageSize)

  return (
    <Layout>
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 text-gray-800">
            {user?.user_type === 'admin' ? 'Document Management' : 'My Documents'}
          </h1>
          <p className="text-gray-600">
            {user?.user_type === 'admin' 
              ? 'View, filter, and manage all classified documents from all users'
              : 'View, filter, and manage your classified documents'
            }
          </p>
        </div>

        {/* Filters and Search */}
        <Card className="mb-6 shadow-sm border-gray-200">
          <CardHeader className="bg-gray-50 border-b border-gray-200">
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Filter className="h-5 w-5 text-[#3452D1]" />
              Filters & Search
            </CardTitle>
          </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div>
              <Label htmlFor="search">Search Documents</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="search"
                  placeholder="Search by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Type Filter */}
            <div>
              <Label htmlFor="type">Document Type</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger>
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types</SelectItem>
                  {documentTypes.map((type) => (
                    <SelectItem key={type.type} value={type.type}>
                      {type.type} ({type.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Status Filter */}
            <div>
              <Label htmlFor="status">Status</Label>
              <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="uploaded">Uploaded</SelectItem>
                  <SelectItem value="extracted">Extracted</SelectItem>
                  <SelectItem value="classified">Classified</SelectItem>
                  <SelectItem value="routed">Routed</SelectItem>
                  <SelectItem value="needs_action">Needs Action</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort */}
            <div>
              <Label htmlFor="sort">Sort By</Label>
              <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
                const [field, order] = value.split('-')
                setSortBy(field)
                setSortOrder(order)
              }}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="upload_timestamp-DESC">Newest First</SelectItem>
                  <SelectItem value="upload_timestamp-ASC">Oldest First</SelectItem>
                  <SelectItem value="document_name-ASC">Name A-Z</SelectItem>
                  <SelectItem value="document_name-DESC">Name Z-A</SelectItem>
                  <SelectItem value="file_size-DESC">Largest First</SelectItem>
                  <SelectItem value="file_size-ASC">Smallest First</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <Button onClick={loadDocuments} variant="outline" size="sm" className="border-[#3452D1] text-[#3452D1] hover:bg-[#3452D1] hover:text-white">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button 
              onClick={() => {
                setSearchTerm('')
                setSelectedType('all')
                setSelectedStatus('all')
                setSortBy('upload_timestamp')
                setSortOrder('DESC')
                setCurrentPage(1)
              }}
              variant="outline" 
              size="sm"
              className="border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card className="shadow-md bg-white">
        <CardHeader className="bg-gray-50">
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2 text-[#3452D1]">
              <FileText className="h-5 w-5" />
              Documents ({totalCount})
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <TooltipProvider>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No documents found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Document</th>
                      <th className="text-left p-2">Type</th>
                      <th className="text-left p-2">Status</th>
                      <th className="text-left p-2">Size</th>
                      <th className="text-left p-2">Upload Date</th>
                      <th className="text-left p-2">Confidence</th>
                      <th className="text-left p-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => (
                      <tr key={doc.document_id} className="border-b hover:bg-gray-50">
                        <td className="p-2">
                          <div>
                            <div className="font-medium">{doc.document_name}</div>
                            <div className="text-sm text-gray-500">{doc.file_extension}</div>
                          </div>
                        </td>
                        <td className="p-2">
                          <Badge variant="outline">
                            {doc.classification_type || 'Unknown'}
                          </Badge>
                        </td>
                        <td className="p-2">
                          <Badge variant={getStatusBadgeVariant(doc.processing_status)}>
                            <span className="flex items-center gap-1">
                              {getStatusIcon(doc.processing_status)}
                              {doc.processing_status}
                            </span>
                          </Badge>
                        </td>
                        <td className="p-2 text-sm">
                          {formatFileSize(doc.file_size)}
                        </td>
                        <td className="p-2 text-sm">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="cursor-help">
                                {formatDate(doc.upload_timestamp)}
                              </span>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{formatAbsoluteDate(doc.upload_timestamp)}</p>
                            </TooltipContent>
                          </Tooltip>
                        </td>
                        <td className="p-2 text-sm">
                          {doc.confidence_score ? 
                            <span className={`px-2 py-1 rounded text-xs ${
                              doc.confidence_score >= 0.8 ? 'bg-green-100 text-green-800' :
                              doc.confidence_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {(doc.confidence_score * 100).toFixed(1)}%
                            </span>
                          : 'N/A'}
                        </td>
                        <td className="p-2">
                          <div className="flex gap-1">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedDocument(doc)
                                    setShowViewModal(true)
                                  }}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>View Details</p>
                              </TooltipContent>
                            </Tooltip>
                            
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedDocument(doc)
                                    setShowRerouteModal(true)
                                  }}
                                >
                                  <Route className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Re-route Document</p>
                              </TooltipContent>
                            </Tooltip>
                            
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedDocument(doc)
                                    setShowReclassifyModal(true)
                                  }}
                                >
                                  <Tag className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Re-classify Document</p>
                              </TooltipContent>
                            </Tooltip>
                            
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedDocument(doc)
                                    setShowDeleteModal(true)
                                  }}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>Delete Document</p>
                              </TooltipContent>
                            </Tooltip>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-between items-center mt-4">
                <div className="text-sm text-gray-600">
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} documents
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <span className="px-3 py-1 text-sm">
                    Page {currentPage} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </TooltipProvider>
        </CardContent>
      </Card>

      {/* View Modal */}
      <Dialog open={showViewModal} onOpenChange={setShowViewModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Document Details</DialogTitle>
          </DialogHeader>
          {selectedDocument && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Document Name</Label>
                  <p className="text-sm font-medium">{selectedDocument.document_name}</p>
                </div>
                <div>
                  <Label>File Type</Label>
                  <p className="text-sm">{selectedDocument.file_extension}</p>
                </div>
                <div>
                  <Label>Classification</Label>
                  <p className="text-sm">{selectedDocument.classification_type || 'Unknown'}</p>
                </div>
                <div>
                  <Label>Confidence Score</Label>
                  <p className="text-sm">{selectedDocument.confidence_score ? `${(selectedDocument.confidence_score * 100).toFixed(1)}%` : 'N/A'}</p>
                </div>
                <div>
                  <Label>File Size</Label>
                  <p className="text-sm">{formatFileSize(selectedDocument.file_size)}</p>
                </div>
                <div>
                  <Label>Status</Label>
                  <Badge variant={getStatusBadgeVariant(selectedDocument.processing_status)}>
                    {selectedDocument.processing_status}
                  </Badge>
                </div>
                <div>
                  <Label>Upload Date</Label>
                  <p className="text-sm">{formatAbsoluteDate(selectedDocument.upload_timestamp)}</p>
                </div>
                <div>
                  <Label>Last Updated</Label>
                  <p className="text-sm">{formatAbsoluteDate(selectedDocument.updated_at)}</p>
                </div>
              </div>
              <div>
                <Label>File Path</Label>
                <p className="text-sm bg-gray-100 p-2 rounded text-xs break-all">
                  {selectedDocument.file_path}
                </p>
              </div>
              {selectedDocument.routed_path && (
                <div>
                  <Label>Routed Path</Label>
                  <p className="text-sm bg-gray-100 p-2 rounded text-xs break-all">
                    {selectedDocument.routed_path}
                  </p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Modal */}
      <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Document</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedDocument?.document_name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reroute Modal */}
      <Dialog open={showRerouteModal} onOpenChange={setShowRerouteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reroute Document</DialogTitle>
            <DialogDescription>
              Choose a new route for "{selectedDocument?.document_name}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Predefined Routes</Label>
              <Select value={newRoute} onValueChange={setNewRoute}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a route" />
                </SelectTrigger>
                <SelectContent>
                  {routeOptions && Object.entries(routeOptions.routes).map(([key, value]) => (
                    <SelectItem key={key} value={key}>
                      {key} → {value}
                    </SelectItem>
                  ))}
                  {routeOptions && (
                    <>
                      <SelectItem value="others">others → {routeOptions.default_folder}</SelectItem>
                      <SelectItem value="needs_action">needs_action → {routeOptions.needs_action_folder}</SelectItem>
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Or Custom Folder</Label>
              <Input
                placeholder="Enter folder name"
                value={newFolder}
                onChange={(e) => setNewFolder(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRerouteModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleReroute}>
              Reroute
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reclassify Modal */}
      <Dialog open={showReclassifyModal} onOpenChange={setShowReclassifyModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reclassify Document</DialogTitle>
            <DialogDescription>
              Enter a new classification for "{selectedDocument?.document_name}"
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>New Classification Type</Label>
              <Input
                placeholder="e.g., invoice, contract, receipt"
                value={newClassification}
                onChange={(e) => setNewClassification(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReclassifyModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleReclassify}>
              Reclassify
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </Layout>
  )
}
