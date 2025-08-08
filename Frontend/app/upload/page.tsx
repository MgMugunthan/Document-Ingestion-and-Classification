"use client"

import type React from "react"

import { useState, useCallback, useEffect } from "react"
import { useRouter } from "next/navigation"
import Layout from "@/components/Layout"
import Chatbot from "@/components/Chatbot"
import { Upload, X, Mail, CheckCircle, Clock, AlertCircle, FileText, Zap, Target, ArrowRight } from "lucide-react"
import { documentApi, getAuthToken, getUserData, gmailApi } from "@/lib/api"
import { useAuth } from "@/contexts/AuthContext"

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
}

interface Document {
  id: string
  fileName: string
  uploadedTime: string
  classification: string
  confidence: number
  status: "completed" | "processing" | "failed" | "uploaded" | "extracted" | "classified" | "routed"
}

interface ProcessingDocument {
  document_id: string
  fileName: string
  currentStep: number
  status: string
  error?: string
}

export default function UploadPage() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [workflowStep, setWorkflowStep] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingDocuments, setProcessingDocuments] = useState<ProcessingDocument[]>([])
  const [error, setError] = useState("")
  const [gmailConnecting, setGmailConnecting] = useState(false)
  const [gmailDisconnecting, setGmailDisconnecting] = useState(false)
  const [gmailConnected, setGmailConnected] = useState(false)
  const [gmailNotification, setGmailNotification] = useState("")
  const { user, token, isLoading } = useAuth()
  const router = useRouter()

  const checkGmailStatus = async () => {
    try {
      const status = await gmailApi.getStatus()
      // Gmail is connected if it's enabled AND has a valid token file
      const isConnected = status.gmail_enabled && status.token_file_exists
      setGmailConnected(isConnected)
      
      if (isConnected) {
        console.log("✅ Gmail already connected")
      } else {
        console.log("📧 Gmail not connected")
      }
    } catch (error) {
      console.error('Failed to check Gmail status:', error)
      setGmailConnected(false)
    }
  }

  const checkForNewGmailDocuments = async () => {
    if (!user || !token || !gmailConnected) return

    try {
      // Get recent documents to find new Gmail ones
      const response = await documentApi.list(user.user_id)
      const allDocs = response.documents || []
      
      // Find documents from last 2 minutes that might be from Gmail 
      // Since we don't have a direct source field, we'll look for very recent documents
      // that weren't manually uploaded (not in our processing list)
      const twoMinutesAgo = new Date(Date.now() - 2 * 60 * 1000)
      const recentGmailDocs = allDocs.filter((doc: any) => {
        const uploadTime = new Date(doc.upload_timestamp)
        const isRecent = uploadTime > twoMinutesAgo
        const notAlreadyTracking = !processingDocuments.find(pd => pd.document_id === doc.document_id)
        // Additional check: document wasn't part of a manual upload session
        const notFromManualUpload = !processingDocuments.length || uploadTime > new Date(Date.now() - 60 * 1000)
        
        return isRecent && notAlreadyTracking && notFromManualUpload
      })

      // Add new Gmail documents to processing list
      if (recentGmailDocs.length > 0) {
        console.log(`📧 Found ${recentGmailDocs.length} new Gmail documents:`, recentGmailDocs)
        
        // Show a notification
        setGmailNotification(`📧 Processing ${recentGmailDocs.length} new document${recentGmailDocs.length > 1 ? 's' : ''} from Gmail...`)
        setTimeout(() => setGmailNotification(""), 5000) // Clear after 5 seconds
        
        const newProcessingDocs = recentGmailDocs.map((doc: any) => ({
          document_id: doc.document_id,
          fileName: doc.document_name,
          currentStep: getStepFromStatus(doc.status || 'uploaded'),
          status: doc.status || 'uploaded' as const
        }))

        // Add to processing documents
        setProcessingDocuments(prev => [...prev, ...newProcessingDocs])
        
        // Start polling for each new document
        newProcessingDocs.forEach((doc: ProcessingDocument) => {
          console.log(`🔄 Starting Gmail document poll: ${doc.document_id}`)
          pollDocumentStatus(doc.document_id)
        })
        
        // Show processing workflow if not already visible
        if (!isProcessing && workflowStep === 0) {
          setWorkflowStep(1)
          setIsProcessing(true)
        }
      }
    } catch (error) {
      console.error('Failed to check for new Gmail documents:', error)
    }
  }

  // Authentication check - redirect to login if not authenticated
  useEffect(() => {
    // Wait for auth loading to complete before checking authentication
    if (isLoading) return
    
    if (!user || !token) {
      router.replace('/login')
      return
    }
  }, [user, token, isLoading, router])

  // Load Gmail status on component mount
  useEffect(() => {
    if (user && token && !isLoading) {
      checkGmailStatus()
      // Check for new Gmail documents every 30 seconds
      const gmailCheckInterval = setInterval(checkForNewGmailDocuments, 30000)
      return () => clearInterval(gmailCheckInterval)
    }
  }, [user, token, isLoading])

  // All useCallback hooks must be declared before any conditional returns
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }, [user, token])

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

  const mapBackendStatus = (backendStatus: string): Document["status"] => {
    switch (backendStatus) {
      case "uploaded": return "uploaded"
      case "extracting": return "processing"
      case "extracted": return "extracted"
      case "classifying": return "processing"
      case "classified": return "classified"
      case "routing": return "processing"
      case "routed": return "completed"
      case "completed": return "completed"
      case "failed": return "failed"
      default: return "processing"
    }
  }

  const workflowSteps = [
    { name: "Ingestion", icon: FileText, description: "Receiving documents" },
    { name: "Extraction", icon: Zap, description: "Extracting content" },
    { name: "Classification", icon: Target, description: "Analyzing document type" },
    { name: "Routing", icon: ArrowRight, description: "Organizing documents" },
  ]

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    handleFiles(files)
  }

  const handleFiles = (files: File[]) => {
    console.log(`📁 Handling ${files.length} files:`, files.map(f => ({ name: f.name, size: f.size, type: f.type })))
    
    const newFiles = files.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
    }))

    setUploadedFiles((prev) => [...prev, ...newFiles])
    uploadFilesToBackend(files)
  }

  const uploadFilesToBackend = async (files: File[]) => {
    if (!user || !token) {
      setError("Please log in to upload files")
      return
    }

    setIsProcessing(true)
    setWorkflowStep(1) // Start with ingestion
    setError("")

    try {
      // Create FileList from files array
      const fileList = files.reduce((dt, file) => {
        dt.items.add(file)
        return dt
      }, new DataTransfer()).files

      // Upload files to backend - upload each file individually
      const uploadPromises = files.map(async (file) => {
        console.log(`🚀 Uploading file: ${file.name}`)
        const uploadResponse = await documentApi.upload(file, { user_id: user.user_id })
        console.log(`📄 Full upload response for ${file.name}:`, JSON.stringify(uploadResponse, null, 2))
        
        if (!uploadResponse.document_id) {
          console.error(`❌ No document_id in response for ${file.name}. Response keys:`, Object.keys(uploadResponse))
          throw new Error(`No document_id received for ${file.name}. Got response: ${JSON.stringify(uploadResponse)}`)
        }
        
        console.log(`✅ Document ID for ${file.name}: ${uploadResponse.document_id}`)
        
        return {
          document_id: uploadResponse.document_id,
          name: file.name,
          status: uploadResponse.status || 'uploaded'
        }
      })
      
      const uploadedDocs = await Promise.all(uploadPromises)
      console.log(`📊 All uploads completed:`, uploadedDocs)

      // Validate all document IDs
      const invalidDocs = uploadedDocs.filter(doc => !doc.document_id)
      if (invalidDocs.length > 0) {
        throw new Error(`Some uploads failed - missing document IDs: ${invalidDocs.map(d => d.name).join(', ')}`)
      }

      // Transform to ProcessingDocument format
      const processingDocs = uploadedDocs.map(doc => ({
        document_id: doc.document_id,
        fileName: doc.name,
        currentStep: 1, // Starting with ingestion
        status: "uploaded" as const
      }))

      setProcessingDocuments(processingDocs)
      console.log(`⚡ Starting to poll ${processingDocs.length} documents with IDs:`, processingDocs.map(d => d.document_id))
      
      // Start polling for status updates
      processingDocs.forEach((doc) => {
        console.log(`📋 Processing doc structure:`, JSON.stringify(doc, null, 2))
        if (doc.document_id && doc.document_id !== 'undefined' && doc.document_id !== 'null') {
          console.log(`🔄 Starting poll for valid document: ${doc.document_id}`)
          pollDocumentStatus(doc.document_id)
        } else {
          console.error(`❌ Invalid document_id for ${doc.fileName}: "${doc.document_id}" (type: ${typeof doc.document_id})`)
        }
      })

    } catch (error) {
      setError(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setIsProcessing(false)
    }
  }

  const pollDocumentStatus = async (documentId: string) => {
    if (!token || !documentId || documentId === 'undefined' || documentId === 'null') {
      console.error(`❌ Cannot poll: invalid documentId. Token: ${!!token}, DocumentId: "${documentId}" (type: ${typeof documentId})`)
      return
    }

    console.log(`🔄 Starting poll for document: ${documentId} (type: ${typeof documentId})`)
    
    const pollInterval = setInterval(async () => {
      try {
        console.log(`📊 Polling status for document: ${documentId}`)
        const statusResponse = await documentApi.getStatus(documentId)
        console.log(`📊 Full status response for ${documentId}:`, JSON.stringify(statusResponse, null, 2))
        
        // Extract status from the response structure
        const status = statusResponse.document?.processing_status || statusResponse.processing_status
        console.log(`📊 Extracted status for ${documentId}: ${status}`)

        if (!status) {
          console.warn(`⚠️ No status found in response for ${documentId}. Response structure:`, Object.keys(statusResponse))
          return
        }

        // Update processing documents
        setProcessingDocuments(prev => 
          prev.map(doc => 
            doc.document_id === documentId 
              ? { 
                  ...doc, 
                  status, 
                  currentStep: getStepFromStatus(status),
                  error: status === 'failed' ? 'Processing failed' : undefined
                }
              : doc
          )
        )

        // Update workflow step based on current processing (use the highest step)
        setProcessingDocuments(currentDocs => {
          const allDocs = currentDocs.map(doc => 
            doc.document_id === documentId 
              ? { ...doc, status, currentStep: getStepFromStatus(status) }
              : doc
          )
          const maxStep = Math.max(...allDocs.map(doc => doc.currentStep))
          setWorkflowStep(maxStep)
          return allDocs
        })

        // Stop polling when processing is complete
        if (status === "completed" || status === "failed" || status === "routed" || status === "needs_action") {
          console.log(`🏁 Document ${documentId} finished with status: ${status}`)
          clearInterval(pollInterval)
          
          // Check if all documents are done processing
          setProcessingDocuments(currentDocs => {
            const updatedDocs = currentDocs.map(doc => 
              doc.document_id === documentId 
                ? { ...doc, status, currentStep: getStepFromStatus(status) }
                : doc
            )
            
            const allDone = updatedDocs.every(doc => 
              doc.status === "completed" || doc.status === "failed" || doc.status === "routed" || doc.status === "needs_action"
            )
            
            if (allDone) {
              setIsProcessing(false)
              
              // Clear uploaded files after a brief delay to let user see completion
              setTimeout(() => {
                setUploadedFiles([])
              }, 2000)
            }
            
            return updatedDocs
          })
        }

      } catch (error) {
        console.error(`❌ Failed to poll document status for ${documentId}:`, error)
        // Stop polling on persistent errors
        if (error instanceof Error && error.message.includes('404')) {
          console.error(`🛑 Stopping polling for ${documentId} due to 404 error`)
          clearInterval(pollInterval)
        }
        // Continue polling for other errors, but limit retries
        setError(`Status check failed for ${documentId}: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    }, 3000) // Poll every 3 seconds for more responsive updates

    // Stop polling after 10 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval)
      setIsProcessing(false)
    }, 600000)
  }

  const getStepFromStatus = (status: string): number => {
    switch (status) {
      case "uploaded": return 1      // Ingestion
      case "extracting": return 2    // Extraction
      case "extracted": return 2     // Extraction complete
      case "classifying": return 3   // Classification  
      case "classified": return 3    // Classification complete
      case "routing": return 4       // Routing
      case "routed": return 4        // Routing complete
      case "completed": return 4     // All done
      case "needs_action": return 2  // Stuck at extraction, needs action
      case "failed": return 0        // Error state
      default: return 1
    }
  }

  const getStepName = (status: string): string => {
    switch (status) {
      case "uploaded": return "Ingesting"
      case "extracting": return "Extracting"
      case "extracted": return "Extracted" 
      case "classifying": return "Classifying"
      case "classified": return "Classified"
      case "routing": return "Routing"
      case "routed": return "Routed"
      case "completed": return "Completed"
      case "needs_action": return "Needs Action"
      case "failed": return "Failed"
      default: return "Processing"
    }
  }

  const startWorkflow = (files: UploadedFile[]) => {
    // This function is now replaced by uploadFilesToBackend
    // but keeping it for backward compatibility
    const fileObjects = files.map(f => new File([], f.name, { type: f.type }))
    handleFiles(fileObjects)
  }

  const removeFile = (id: string) => {
    setUploadedFiles((prev) => prev.filter((file) => file.id !== id))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const handleConnectGmail = async () => {
    if (gmailConnecting) return
    
    setGmailConnecting(true)
    setError("")
    
    try {
      console.log("🔗 Starting Gmail authentication...")
      const response = await gmailApi.startAuth()
      
      if (response.auth_url) {
        console.log("🌐 Opening OAuth URL:", response.auth_url)
        // Open OAuth URL in a new window
        window.open(response.auth_url, 'gmail_auth', 'width=500,height=600')
        
        // Listen for the success callback
        const handleCallback = (event: MessageEvent) => {
          if (event.data && event.data.type === 'gmail_connected') {
            console.log(" Gmail connected successfully!")
            setGmailConnected(true)
            setGmailConnecting(false)
            window.removeEventListener('message', handleCallback)
            // Refresh status to ensure UI is in sync
            checkGmailStatus()
          } else if (event.data && event.data.type === 'gmail_error') {
            console.error(" Gmail OAuth error:", event.data.error)
            setError(`Gmail connection failed: ${event.data.error}`)
            setGmailConnecting(false)
            window.removeEventListener('message', handleCallback)
          }
        }
        
        window.addEventListener('message', handleCallback)
        
        // Set a timeout to stop listening after 5 minutes
        setTimeout(() => {
          window.removeEventListener('message', handleCallback)
          setGmailConnecting(false)
        }, 300000)
        
      } else {
        throw new Error("No authorization URL received")
      }
      
    } catch (error) {
      console.error("❌ Gmail connection failed:", error)
      setError(`Failed to connect Gmail: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setGmailConnecting(false)
    }
  }

  const handleDisconnectGmail = async () => {
    if (gmailDisconnecting || gmailConnecting) return
    
    setGmailDisconnecting(true)
    setError("")
    
    try {
      console.log("🔗 Disconnecting Gmail...")
      const response = await gmailApi.disconnect()
      
      if (response.status === 'success') {
        console.log("✅ Gmail disconnected successfully!")
        setGmailConnected(false)
        setGmailDisconnecting(false)
        // Refresh the status to make sure UI is in sync
        await checkGmailStatus()
      } else {
        throw new Error(response.error || "Disconnect failed")
      }
      
    } catch (error) {
      console.error("❌ Gmail disconnect failed:", error)
      setError(`Failed to disconnect Gmail: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setGmailDisconnecting(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "processing":
        return <Clock className="w-4 h-4 text-yellow-500" />
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  return (
    <Layout>
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Document Upload</h1>
          <p className="text-gray-600">Upload your documents for intelligent classification and processing</p>
        </div>

        {/* Upload Area */}
        <div className="mb-8">
          <div
            className={`border-2 border-dashed rounded-xl p-8 md:p-12 text-center transition-all duration-300 ${
              isDragOver ? "border-[#3452D1] bg-blue-50" : "border-gray-300 hover:border-[#3452D1] hover:bg-blue-50"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 md:w-16 md:h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg md:text-xl font-semibold text-gray-700 mb-2">Drag and drop your files here</h3>
            <p className="text-gray-500 mb-4">or click to browse</p>
            <input type="file" multiple onChange={handleFileInput} className="hidden" id="file-upload" />
            <label
              htmlFor="file-upload"
              className="inline-flex items-center px-6 py-3 bg-[#3452D1] text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
            >
              Choose Files
            </label>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
                <button
                  onClick={() => setError("")}
                  className="ml-auto text-red-400 hover:text-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* Gmail Notification */}
          {gmailNotification && (
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Mail className="h-5 w-5 text-blue-400" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-blue-700">{gmailNotification}</p>
                </div>
                <button
                  onClick={() => setGmailNotification("")}
                  className="ml-auto text-blue-400 hover:text-blue-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}



          {/* Gmail Connection Section */}
          <div className="mt-6">
            {gmailConnected ? (
              <div className="space-y-3">
                {/* Connected Status Indicator */}
                <div className="flex items-center justify-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-green-700 font-medium">Gmail Connected</span>
                  </div>
                </div>
                
                {/* Disconnect Button */}
                <button
                  onClick={handleDisconnectGmail}
                  disabled={gmailDisconnecting}
                  className={`w-full py-3 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2 border-2 ${
                    gmailDisconnecting 
                      ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed' 
                      : 'bg-white text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300 cursor-pointer'
                  }`}
                >
                  {gmailDisconnecting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-transparent"></div>
                      <span>Disconnecting...</span>
                    </>
                  ) : (
                    <>
                      <X className="w-4 h-4" />
                      <span>Disconnect Gmail</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              /* Connect Button */
              <button
                onClick={handleConnectGmail}
                disabled={gmailConnecting}
                className={`w-full py-4 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2 ${
                  gmailConnecting 
                    ? 'bg-gray-400 text-white cursor-not-allowed' 
                    : 'bg-[#3452D1] text-white hover:bg-blue-700 cursor-pointer'
                }`}
              >
                {gmailConnecting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    <span>Connecting...</span>
                  </>
                ) : (
                  <>
                    <Mail className="w-5 h-5" />
                    <span>Connect to Gmail</span>
                  </>
                )}
              </button>
            )}
          </div>          {/* WORKFLOW PROGRESS - ENHANCED AND CLEARLY VISIBLE */}
          {(isProcessing || workflowStep > 0) && (
            <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border-2 border-blue-200 shadow-lg">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Document Processing Workflow</h3>
                <p className="text-gray-600">Your documents are being processed through our intelligent pipeline</p>
              </div>

              {/* Progress Bar */}
              <div className="relative mb-12">
                <div className="absolute top-1/2 left-0 right-0 h-2 bg-gray-200 rounded-full transform -translate-y-1/2 z-10"></div>
                <div
                  className="absolute top-1/2 left-0 h-2 bg-gradient-to-r from-[#3452D1] to-blue-600 rounded-full transform -translate-y-1/2 transition-all duration-1000 z-20"
                  style={{ width: `${(workflowStep / workflowSteps.length) * 100}%` }}
                ></div>
              </div>

              {/* Workflow Steps */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-30">
                {workflowSteps.map((step, index) => {
                  const isActive = index === workflowStep - 1 && isProcessing
                  const isCompleted = index < workflowStep - 1 || (index === workflowStep - 1 && !isProcessing)
                  const isPending = index >= workflowStep

                  return (
                    <div key={step.name} className="text-center relative">
                      {/* Step Icon */}
                      <div
                        className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-6 transition-all duration-500 relative z-40 ${
                          isCompleted
                            ? "bg-green-500 text-white shadow-lg scale-110"
                            : isActive
                              ? "bg-[#3452D1] text-white animate-pulse shadow-xl scale-110"
                              : "bg-gray-200 text-gray-500"
                        }`}
                      >
                        {isCompleted ? (
                          <CheckCircle className="w-8 h-8" />
                        ) : (
                          <step.icon className={`w-8 h-8 ${isActive ? "animate-bounce" : ""}`} />
                        )}
                      </div>

                      {/* Step Info */}
                      <div>
                        <h4
                          className={`text-lg font-semibold mb-2 ${
                            isCompleted ? "text-green-600" : isActive ? "text-[#3452D1]" : "text-gray-500"
                          }`}
                        >
                          {step.name}
                        </h4>
                        <p className="text-sm text-gray-600 mb-2">{step.description}</p>
                        <div
                          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                            isCompleted
                              ? "bg-green-100 text-green-800"
                              : isActive
                                ? "bg-blue-100 text-blue-800 animate-pulse"
                                : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {isCompleted ? `${step.name}ed` : isActive ? `${step.name}ing...` : "Pending"}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Processing Status */}
              <div className="mt-8 p-6 bg-white rounded-xl border border-blue-200">
                <div className="flex items-center justify-center space-x-3">
                  {isProcessing ? (
                    <>
                      <div className="w-3 h-3 bg-[#3452D1] rounded-full animate-pulse"></div>
                      <p className="text-lg font-medium text-[#3452D1]">
                        Processing: {workflowSteps[workflowStep - 1]?.name}ing your documents...
                      </p>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-6 h-6 text-green-500" />
                      <p className="text-lg font-medium text-green-600">
                        All documents have been successfully processed and routed!
                      </p>
                    </>
                  )}
                </div>
                
                {/* Show individual document progress */}
                {processingDocuments.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Processing Documents:</h4>
                    {processingDocuments.map((doc) => (
                      <div key={doc.document_id} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                              <FileText className="w-4 h-4 text-[#3452D1]" />
                            </div>
                            <span className="text-sm font-medium text-gray-800">{doc.fileName}</span>
                          </div>
                          
                          {/* Status Badge */}
                          <div className="flex items-center space-x-2">
                            {doc.status === "routed" || doc.status === "completed" ? (
                              <div className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                <CheckCircle className="w-3 h-3" />
                                <span>{getStepName(doc.status)}</span>
                              </div>
                            ) : doc.status === "needs_action" ? (
                              <div className="flex items-center space-x-1 px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                                <AlertCircle className="w-3 h-3" />
                                <span>Needs Action</span>
                              </div>
                            ) : doc.status === "failed" ? (
                              <div className="flex items-center space-x-1 px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                                <AlertCircle className="w-3 h-3" />
                                <span>Failed</span>
                              </div>
                            ) : (
                              <div className="flex items-center space-x-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                                <span>{getStepName(doc.status)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* Progress Bar for Individual File */}
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                              doc.status === "routed" || doc.status === "completed"
                                ? "bg-green-500"
                                : doc.status === "needs_action"
                                  ? "bg-orange-500"
                                  : doc.status === "failed"
                                    ? "bg-red-500"
                                    : "bg-blue-500"
                            }`}
                            style={{
                              width: `${
                                doc.status === "routed" || doc.status === "completed"
                                  ? 100
                                  : doc.status === "needs_action"
                                    ? 50
                                    : doc.status === "failed"
                                      ? 25
                                      : ((getStepFromStatus(doc.status) - 1) / 4) * 100 + 25
                              }%`,
                            }}
                          ></div>
                        </div>
                        
                        <div className="flex justify-between items-center mt-2">
                          <span className="text-xs text-gray-500">
                            {doc.status === "routed" || doc.status === "completed" ? "Processing complete" :
                             doc.status === "needs_action" ? "Manual intervention required" :
                             doc.status === "failed" ? "Processing failed" :
                             `Currently ${getStepName(doc.status).toLowerCase()}...`}
                          </span>
                          <span className="text-xs text-gray-400">
                            {Math.round(
                              doc.status === "routed" || doc.status === "completed" ? 100 :
                              doc.status === "needs_action" ? 50 :
                              doc.status === "failed" ? 25 :
                              ((getStepFromStatus(doc.status) - 1) / 4) * 100 + 25
                            )}% complete
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <Chatbot />
    </Layout>
  )
}
