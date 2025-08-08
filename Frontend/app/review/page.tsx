"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import Layout from "@/components/Layout"
import { AlertTriangle, Check, X, Eye, FileText, Clock, RotateCcw, Trash2, Tag, Download, HardDrive, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"

// Define the document type based on backend response
interface ReviewDocument {
  document_id: string
  original_filename: string
  user_id: string
  upload_method: string
  file_size: number
  document_classification: string
  classification_confidence: number
  classification_method: string
  status: string
  final_path: string
  created_at: string
  updated_at: string
  file_type: string
}

interface RouteOptions {
  routes: Record<string, string>
  default_folder: string
  needs_action_folder: string
}

interface ReclassifyModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (classification: string) => void
  routeOptions: RouteOptions | null
}

function ReclassifyModal({ isOpen, onClose, onSubmit, routeOptions }: ReclassifyModalProps) {
  const [selectedRoute, setSelectedRoute] = useState("")
  const [customClassification, setCustomClassification] = useState("")

  if (!isOpen) return null

  const handleSubmit = () => {
    const classification = selectedRoute === "__manual__" ? customClassification : selectedRoute
    if (classification.trim()) {
      onSubmit(classification.trim())
      setSelectedRoute("")
      setCustomClassification("")
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96 max-w-90vw">
        <h3 className="text-lg font-semibold mb-4">Reclassify Document</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Predefined Classifications</label>
            <select 
              className="w-full border border-gray-300 rounded px-3 py-2"
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
            >
              <option value="">Select a classification...</option>
              {routeOptions && Object.keys(routeOptions.routes).map((routeKey) => (
                <option key={routeKey} value={routeKey}>
                  {routeKey} → {routeOptions.routes[routeKey]}
                </option>
              ))}
              {routeOptions && (
                <>
                  <option value="others">others → {routeOptions.default_folder}</option>
                  <option value="needs_action">needs_action → {routeOptions.needs_action_folder}</option>
                </>
              )}
              <option value="__manual__">Custom...</option>
            </select>
          </div>

          {selectedRoute === "__manual__" && (
            <div>
              <label className="block text-sm font-medium mb-2">Custom Classification</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded px-3 py-2"
                placeholder="e.g., contract, report, memo"
                value={customClassification}
                onChange={(e) => setCustomClassification(e.target.value)}
              />
            </div>
          )}
        </div>

        <div className="flex space-x-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedRoute || (selectedRoute === "__manual__" && !customClassification.trim())}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Reclassify
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Review() {
  const { user, token, isLoading } = useAuth()
  const router = useRouter()
  const { toast } = useToast()
  const [documents, setDocuments] = useState<ReviewDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [routeOptions, setRouteOptions] = useState<RouteOptions | null>(null)
  const [reclassifyModal, setReclassifyModal] = useState<{isOpen: boolean, documentId: string}>({
    isOpen: false,
    documentId: ""
  })
  const [deleteModal, setDeleteModal] = useState<{isOpen: boolean, documentId: string, filename: string}>({
    isOpen: false,
    documentId: "",
    filename: ""
  })

  // Fetch documents that need review
  useEffect(() => {
    if (user && token) {
      fetchReviewDocuments()
      fetchAvailableRoutes()
    }
  }, [user, token])

  const fetchReviewDocuments = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/documents/review')
      const data = await response.json()
      
      if (data.success) {
        setDocuments(data.documents)
      } else {
        setError(data.error || 'Failed to fetch documents')
      }
    } catch (err) {
      setError('Error fetching documents')
      console.error('Error fetching review documents:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchAvailableRoutes = async () => {
    try {
      const response = await fetch('/api/documents/routes')
      const data = await response.json()
      if (data.success && data.routes) {
        setRouteOptions(data.routes as RouteOptions)
      }
    } catch (err) {
      console.error('Error fetching routes:', err)
    }
  }

  const handleViewDocument = async (document: ReviewDocument) => {
    try {
      // Open document in new tab/window for viewing
      window.open(`/api/documents/${document.document_id}/download`, '_blank')
    } catch (err) {
      console.error('Error viewing document:', err)
      alert('Error opening document')
    }
  }

  const handleReclassify = async (documentId: string, newClassification: string) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/reclassify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          new_classification: newClassification
        })
      })

      const data = await response.json()
      
      if (data.success) {
        // Remove the document from the review list since it's been processed
        setDocuments(prev => prev.filter(doc => doc.document_id !== documentId))
        toast({
          title: "Success",
          description: `Document successfully reclassified as '${newClassification}'`,
        })
      } else {
        toast({
          title: "Error", 
          description: data.error || 'Failed to reclassify document',
          variant: "destructive",
        })
      }
    } catch (err) {
      console.error('Error reclassifying document:', err)
      toast({
        title: "Error",
        description: "Failed to reclassify document. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async (documentId: string) => {    
    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      })

      const data = await response.json()
      
      if (data.success) {
        // Remove the document from the review list
        setDocuments(prev => prev.filter(doc => doc.document_id !== documentId))
        toast({
          title: "Success",
          description: "Document deleted successfully",
        })
      } else {
        toast({
          title: "Error",
          description: data.error || 'Failed to delete document',
          variant: "destructive",
        })
      }
    } catch (err) {
      console.error('Error deleting document:', err)
      toast({
        title: "Error",
        description: "Failed to delete document. Please try again.",
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

    // For older dates, show formatted date
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

  const handleView = async (documentId: string) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/view`)
      const data = await response.json()
      
      if (data.success) {
        // Open the file in a new tab
        window.open(`/api/documents/${documentId}/download`, '_blank')
      } else {
        alert(data.error || 'File not found')
      }
    } catch (err) {
      console.error('Error viewing document:', err)
      alert('Error viewing document')
    }
  }

  const handleDownload = async (documentId: string) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/download`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'document'
        
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        alert('Failed to download document')
      }
    } catch (err) {
      console.error('Error downloading document:', err)
      alert('Error downloading document')
    }
  }

  // Authentication check - CRITICAL SECURITY FIX
  useEffect(() => {
    // Wait for auth loading to complete before checking authentication
    if (isLoading) return
    
    if (!user || !token) {
      router.replace('/login')
      return
    }
  }, [user, token, isLoading, router])

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

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        
        {/* Documents Table */}
        <Card className="shadow-md bg-white">
          <CardHeader className="bg-gray-50">
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center gap-2 text-[#3452D1]">
                <AlertTriangle className="h-5 w-5" />
                Documents for Review ({documents.length})
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
                  <Check className="h-12 w-12 text-green-400 mx-auto mb-4" />
                  <p className="text-gray-600">No documents require review</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Document</th>
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
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                <FileText className="h-4 w-4 text-blue-600" />
                              </div>
                              <div>
                                <div className="font-medium text-sm">{doc.original_filename}</div>
                                <div className="text-xs text-gray-500">{doc.file_type}</div>
                              </div>
                            </div>
                          </td>
                          <td className="p-2">
                            <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                              <span className="flex items-center gap-1">
                                <AlertTriangle className="h-3 w-3" />
                                Needs Action
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
                                  {formatDate(doc.created_at)}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{formatAbsoluteDate(doc.created_at)}</p>
                              </TooltipContent>
                            </Tooltip>
                          </td>
                          <td className="p-2 text-sm">
                            {doc.classification_confidence > 0 ? 
                              <span className={`px-2 py-1 rounded text-xs ${
                                doc.classification_confidence >= 80 ? 'bg-green-100 text-green-800' :
                                doc.classification_confidence >= 60 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {doc.classification_confidence.toFixed(1)}%
                              </span>
                            : <span className="text-gray-400 text-xs">Unprocessed</span>}
                          </td>
                          <td className="p-2">
                            <div className="flex gap-1">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleView(doc.document_id)}
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>View Document</p>
                                </TooltipContent>
                              </Tooltip>
                              
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setReclassifyModal({isOpen: true, documentId: doc.document_id})}
                                  >
                                    <Tag className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Reclassify Document</p>
                                </TooltipContent>
                              </Tooltip>
                              
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleDownload(doc.document_id)}
                                  >
                                    <Download className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p>Download Document</p>
                                </TooltipContent>
                              </Tooltip>
                              
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => setDeleteModal({isOpen: true, documentId: doc.document_id, filename: doc.original_filename})}
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
            </TooltipProvider>
          </CardContent>
        </Card>
      </div>

      {/* Reclassify Modal */}
      <ReclassifyModal
        isOpen={reclassifyModal.isOpen}
        onClose={() => setReclassifyModal({isOpen: false, documentId: ""})}
        onSubmit={(classification) => handleReclassify(reclassifyModal.documentId, classification)}
        routeOptions={routeOptions}
      />

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteModal.isOpen} onOpenChange={(open) => setDeleteModal(prev => ({ ...prev, isOpen: open }))}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <Trash2 className="h-5 w-5" />
              Delete Document
            </DialogTitle>
            <DialogDescription className="pt-2">
              Are you sure you want to delete <span className="font-medium">"{deleteModal.filename}"</span>? 
              This action cannot be undone and the document will be permanently removed.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setDeleteModal({isOpen: false, documentId: "", filename: ""})}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                handleDelete(deleteModal.documentId)
                setDeleteModal({isOpen: false, documentId: "", filename: ""})
              }}
              className="gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Delete Document
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  )
}
