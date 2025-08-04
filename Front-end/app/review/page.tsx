"use client"

import { useState } from "react"
import Layout from "@/components/Layout"
import { AlertTriangle, Check, X, Plus, ChevronDown } from "lucide-react"

interface ReviewDocument {
  id: string
  name: string
  suggestedClassification: string
  confidence: number
  currentClassification: string
  dateUploaded: string
  size: string
}

export default function Review() {
  const [documents, setDocuments] = useState<ReviewDocument[]>([
    {
      id: "1",
      name: "Quarterly_Budget_2024.xlsx",
      suggestedClassification: "Financial Report",
      confidence: 72,
      currentClassification: "Unclassified",
      dateUploaded: "2024-01-15",
      size: "1.8 MB",
    },
    {
      id: "2",
      name: "Vendor_Agreement_Draft.pdf",
      suggestedClassification: "Contract",
      confidence: 68,
      currentClassification: "Legal Document",
      dateUploaded: "2024-01-14",
      size: "2.1 MB",
    },
    {
      id: "3",
      name: "Project_Timeline.docx",
      suggestedClassification: "Project Document",
      confidence: 75,
      currentClassification: "Report",
      dateUploaded: "2024-01-13",
      size: "945 KB",
    },
    {
      id: "4",
      name: "Employee_Handbook_2024.pdf",
      suggestedClassification: "Policy Document",
      confidence: 69,
      currentClassification: "Manual",
      dateUploaded: "2024-01-12",
      size: "3.2 MB",
    },
  ])

  const [showCreateFolder, setShowCreateFolder] = useState<string | null>(null)
  const [newFolderName, setNewFolderName] = useState("")

  const availableFolders = [
    "Financial Reports",
    "Contracts",
    "HR Documents",
    "Project Files",
    "Legal Documents",
    "Policies",
    "Invoices",
    "Reports",
  ]

  const handleAcceptSuggestion = (id: string) => {
    setDocuments((docs) =>
      docs.map((doc) => (doc.id === id ? { ...doc, currentClassification: doc.suggestedClassification } : doc)),
    )
  }

  const handleRejectSuggestion = (id: string) => {
    setDocuments((docs) => docs.filter((doc) => doc.id !== id))
  }

  const handleManualClassification = (id: string, classification: string) => {
    setDocuments((docs) => docs.map((doc) => (doc.id === id ? { ...doc, currentClassification: classification } : doc)))
  }

  const handleCreateFolder = (docId: string) => {
    if (newFolderName.trim()) {
      handleManualClassification(docId, newFolderName.trim())
      setNewFolderName("")
      setShowCreateFolder(null)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "bg-green-500"
    if (confidence >= 60) return "bg-yellow-500"
    return "bg-red-500"
  }

  return (
    <Layout>
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Review & Classification</h1>
          <p className="text-gray-600">Review documents that need manual classification or re-routing</p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Review</p>
                <p className="text-2xl font-bold text-gray-900">{documents.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Check className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Reviewed Today</p>
                <p className="text-2xl font-bold text-gray-900">12</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <X className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Avg. Confidence</p>
                <p className="text-2xl font-bold text-gray-900">71%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Documents Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">Documents Requiring Review</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Suggested Classification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Classification
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <AlertTriangle className="w-5 h-5 text-[#3452D1]" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{doc.name}</p>
                          <p className="text-sm text-gray-500">
                            {doc.size} • {doc.dateUploaded}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          {doc.suggestedClassification}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="relative">
                        <select
                          value={doc.currentClassification}
                          onChange={(e) => handleManualClassification(doc.id, e.target.value)}
                          className="appearance-none bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value={doc.currentClassification}>{doc.currentClassification}</option>
                          {availableFolders.map((folder) => (
                            <option key={folder} value={folder}>
                              {folder}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getConfidenceColor(doc.confidence)}`}
                            style={{ width: `${doc.confidence}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900">{doc.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleAcceptSuggestion(doc.id)}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          title="Accept suggestion"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleRejectSuggestion(doc.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Reject suggestion"
                        >
                          <X className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setShowCreateFolder(doc.id)}
                          className="p-2 text-[#3452D1] hover:bg-blue-50 rounded-lg transition-colors"
                          title="Create new folder"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Empty State */}
          {documents.length === 0 && (
            <div className="px-6 py-12 text-center">
              <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">All caught up!</h3>
              <p className="text-gray-500">No documents require review at this time.</p>
            </div>
          )}
        </div>

        {/* Create New Folder Modal */}
        {showCreateFolder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Create New Folder</h3>
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Enter folder name..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
                autoFocus
              />
              <div className="flex space-x-3">
                <button
                  onClick={() => handleCreateFolder(showCreateFolder)}
                  className="flex-1 bg-[#3452D1] text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateFolder(null)
                    setNewFolderName("")
                  }}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
