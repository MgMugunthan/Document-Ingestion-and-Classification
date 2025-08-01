"use client"

import { useState } from "react"
import Layout from "@/components/Layout"
import { Search, Filter, FileText, Download, Eye } from "lucide-react"

interface Document {
  id: string
  name: string
  classification: string
  confidence: number
  dateIngested: string
  size: string
  type: string
}

export default function Documents() {
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState("all")

  const documents: Document[] = [
    {
      id: "1",
      name: "Q1_Financial_Report.pdf",
      classification: "Report",
      confidence: 95,
      dateIngested: "2024-01-15",
      size: "2.4 MB",
      type: "PDF",
    },
    {
      id: "2",
      name: "Invoice_ABC_Corp_001.pdf",
      classification: "Invoice",
      confidence: 88,
      dateIngested: "2024-01-14",
      size: "1.2 MB",
      type: "PDF",
    },
    {
      id: "3",
      name: "Employee_Contract_2024.docx",
      classification: "Contract",
      confidence: 92,
      dateIngested: "2024-01-13",
      size: "856 KB",
      type: "DOCX",
    },
    {
      id: "4",
      name: "Marketing_Proposal.pptx",
      classification: "Proposal",
      confidence: 78,
      dateIngested: "2024-01-12",
      size: "3.1 MB",
      type: "PPTX",
    },
    {
      id: "5",
      name: "Resume_John_Smith.pdf",
      classification: "Resume",
      confidence: 85,
      dateIngested: "2024-01-11",
      size: "945 KB",
      type: "PDF",
    },
    {
      id: "6",
      name: "Purchase_Order_2024_001.pdf",
      classification: "Invoice",
      confidence: 91,
      dateIngested: "2024-01-10",
      size: "1.8 MB",
      type: "PDF",
    },
  ]

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.classification.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterType === "all" || doc.classification.toLowerCase() === filterType.toLowerCase()
    return matchesSearch && matchesFilter
  })

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "bg-green-500"
    if (confidence >= 75) return "bg-yellow-500"
    return "bg-red-500"
  }

  const getFileIcon = (type: string) => {
    return <FileText className="w-5 h-5 text-[#3452D1]" />
  }

  return (
    <Layout>
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Documents</h1>
          <p className="text-gray-600">Manage and view all your processed documents</p>
        </div>

        {/* Filters and Search */}
        <div className="mb-6 flex flex-col md:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filter Dropdown */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="appearance-none pl-10 pr-8 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white min-w-[150px]"
            >
              <option value="all">All Types</option>
              <option value="invoice">Invoice</option>
              <option value="report">Report</option>
              <option value="contract">Contract</option>
              <option value="resume">Resume</option>
              <option value="proposal">Proposal</option>
            </select>
          </div>
        </div>

        {/* Documents Grid/List */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {/* Table Header */}
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4 text-sm font-medium text-gray-500 uppercase tracking-wider">
              <div className="md:col-span-2">Document Name</div>
              <div>Classification</div>
              <div>Confidence</div>
              <div>Date Ingested</div>
              <div>Actions</div>
            </div>
          </div>

          {/* Documents List */}
          <div className="divide-y divide-gray-200">
            {filteredDocuments.map((doc) => (
              <div key={doc.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-center">
                  {/* Document Name */}
                  <div className="md:col-span-2 flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      {getFileIcon(doc.type)}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{doc.name}</p>
                      <p className="text-sm text-gray-500">
                        {doc.size} • {doc.type}
                      </p>
                    </div>
                  </div>

                  {/* Classification */}
                  <div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {doc.classification}
                    </span>
                  </div>

                  {/* Confidence Score */}
                  <div>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getConfidenceColor(doc.confidence)}`}
                          style={{ width: `${doc.confidence}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-900">{doc.confidence}%</span>
                    </div>
                  </div>

                  {/* Date Ingested */}
                  <div>
                    <p className="text-sm text-gray-900">{doc.dateIngested}</p>
                  </div>

                  {/* Actions */}
                  <div>
                    <div className="flex items-center space-x-2">
                      <button className="p-2 text-gray-400 hover:text-[#3452D1] transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-[#3452D1] transition-colors">
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty State */}
          {filteredDocuments.length === 0 && (
            <div className="px-6 py-12 text-center">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
              <p className="text-gray-500">
                {searchTerm || filterType !== "all"
                  ? "Try adjusting your search or filter criteria."
                  : "Upload some documents to get started."}
              </p>
            </div>
          )}
        </div>

        {/* Pagination */}
        {filteredDocuments.length > 0 && (
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-700">
              Showing <span className="font-medium">1</span> to{" "}
              <span className="font-medium">{filteredDocuments.length}</span> of{" "}
              <span className="font-medium">{filteredDocuments.length}</span> results
            </p>
            <div className="flex items-center space-x-2">
              <button className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                Previous
              </button>
              <button className="px-3 py-2 text-sm font-medium text-white bg-[#3452D1] border border-transparent rounded-md hover:bg-blue-700">
                1
              </button>
              <button className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
