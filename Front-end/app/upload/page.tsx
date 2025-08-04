"use client"

import type React from "react"

import { useState, useCallback } from "react"
import Layout from "@/components/Layout"
import Chatbot from "@/components/Chatbot"
import { Upload, X, Mail, CheckCircle, Clock, AlertCircle, FileText, Zap, Target, ArrowRight } from "lucide-react"

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
  status: "completed" | "processing" | "failed"
}

export default function UploadPage() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [workflowStep, setWorkflowStep] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([
    {
      id: "1",
      fileName: "invoice_2024_001.pdf",
      uploadedTime: "2024-01-15 10:30",
      classification: "Invoice",
      confidence: 95,
      status: "completed",
    },
    {
      id: "2",
      fileName: "report_quarterly.docx",
      uploadedTime: "2024-01-15 09:15",
      classification: "Report",
      confidence: 88,
      status: "completed",
    },
    {
      id: "3",
      fileName: "resume_john_doe.pdf",
      uploadedTime: "2024-01-15 08:45",
      classification: "Resume",
      confidence: 72,
      status: "completed",
    },
  ])

  const workflowSteps = [
    { name: "Ingestion", icon: FileText, description: "Receiving documents" },
    { name: "Extraction", icon: Zap, description: "Extracting content" },
    { name: "Classification", icon: Target, description: "Analyzing document type" },
    { name: "Routing", icon: ArrowRight, description: "Organizing documents" },
  ]

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
    const newFiles = files.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
    }))

    setUploadedFiles((prev) => [...prev, ...newFiles])
    startWorkflow(newFiles)
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const newFiles = files.map((file) => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
    }))

    setUploadedFiles((prev) => [...prev, ...newFiles])
    startWorkflow(newFiles)
  }

  const startWorkflow = (files: UploadedFile[]) => {
    if (files.length === 0) return

    setIsProcessing(true)
    setWorkflowStep(0)

    // Simulate workflow progress
    let step = 0
    const interval = setInterval(() => {
      step++
      setWorkflowStep(step)

      if (step >= workflowSteps.length) {
        clearInterval(interval)
        setIsProcessing(false)

        // Update recent documents list when workflow completes
        setTimeout(() => {
          const newDoc = {
            id: Date.now().toString(),
            fileName: files[0]?.name || "processed_document.pdf",
            uploadedTime: new Date().toLocaleString(),
            classification: "Auto-classified",
            confidence: Math.floor(Math.random() * 20) + 80, // 80-100%
            status: "completed" as const,
          }
          setRecentDocuments((prev) => [newDoc, ...prev.slice(0, 2)])
        }, 1000)
      }
    }, 2500) // 2.5 seconds per step
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

          {/* Uploaded Files */}
          {uploadedFiles.length > 0 && (
            <div className="mt-6 space-y-3">
              <h4 className="font-semibold text-gray-700">Uploaded Files</h4>
              {uploadedFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between bg-white p-4 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Upload className="w-5 h-5 text-[#3452D1]" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">{file.name}</p>
                      <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Connect to Mail Button */}
          <button className="w-full mt-6 bg-[#3452D1] text-white py-4 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2">
            <Mail className="w-5 h-5" />
            <span>Connect to Mail</span>
          </button>

          {/* WORKFLOW PROGRESS - ENHANCED AND CLEARLY VISIBLE */}
          {(isProcessing || workflowStep > 0) && (
            <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border-2 border-blue-200 shadow-lg">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Document Processing Workflow</h3>
                <p className="text-gray-600">Your documents are being processed through our intelligent pipeline</p>
              </div>

              {/* Progress Bar */}
              <div className="relative mb-8">
                <div className="absolute top-1/2 left-0 right-0 h-2 bg-gray-200 rounded-full transform -translate-y-1/2"></div>
                <div
                  className="absolute top-1/2 left-0 h-2 bg-gradient-to-r from-[#3452D1] to-blue-600 rounded-full transform -translate-y-1/2 transition-all duration-1000"
                  style={{ width: `${(workflowStep / workflowSteps.length) * 100}%` }}
                ></div>
              </div>

              {/* Workflow Steps */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {workflowSteps.map((step, index) => {
                  const isActive = index === workflowStep - 1 && isProcessing
                  const isCompleted = index < workflowStep - 1 || (index === workflowStep - 1 && !isProcessing)
                  const isPending = index >= workflowStep

                  return (
                    <div key={step.name} className="text-center">
                      {/* Step Icon */}
                      <div
                        className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-4 transition-all duration-500 ${
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
              </div>
            </div>
          )}
        </div>

        {/* Recent Documents */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h3 className="font-semibold text-gray-800">Recent Documents</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Classification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{doc.fileName}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doc.uploadedTime}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doc.classification}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              doc.confidence >= 80
                                ? "bg-green-500"
                                : doc.confidence >= 60
                                  ? "bg-yellow-500"
                                  : "bg-red-500"
                            }`}
                            style={{ width: `${doc.confidence}%` }}
                          />
                        </div>
                        <span>{doc.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(doc.status)}
                        <span className="capitalize">{doc.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {doc.confidence < 80 && (
                        <button className="text-[#3452D1] hover:text-blue-700 font-medium">Re-classify</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Chatbot />
    </Layout>
  )
}
