"use client"

import { useState } from "react"
import Layout from "@/components/Layout"
import { FileText, TrendingUp, AlertTriangle, ChevronDown } from "lucide-react"

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState("week")
  const [chartType, setChartType] = useState("line")

  const stats = [
    {
      title: "Documents Ingested",
      value: "1,247",
      change: "+12%",
      changeType: "positive",
      icon: FileText,
    },
    {
      title: "Avg. Confidence Score",
      value: "88%",
      change: "+5%",
      changeType: "positive",
      icon: TrendingUp,
    },
    {
      title: "Review Actions",
      value: "23",
      change: "-8%",
      changeType: "negative",
      icon: AlertTriangle,
    },
  ]

  const processedData = {
    week: [120, 135, 148, 162, 175, 188, 195],
    month: [1200, 1350, 1480, 1620, 1750, 1880, 1950, 2100, 2250, 2400, 2550, 2700],
    year: [14400, 16200, 17760, 19440, 21000, 22560, 23400, 25200, 27000, 28800, 30600, 32400],
  }

  const classificationData = [
    { name: "Invoices", value: 35, color: "#3452D1" },
    { name: "Reports", value: 25, color: "#60A5FA" },
    { name: "Resumes", value: 20, color: "#93C5FD" },
    { name: "Contracts", value: 15, color: "#DBEAFE" },
    { name: "Others", value: 5, color: "#F3F4F6" },
  ]

  return (
    <Layout>
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Dashboard</h1>
          <p className="text-gray-600">Overview of your document processing activities</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  <p className={`text-sm mt-2 ${stat.changeType === "positive" ? "text-green-600" : "text-red-600"}`}>
                    {stat.change} from last period
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <stat.icon className="w-6 h-6 text-[#3452D1]" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Documents Processed Chart */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-800">Documents Processed</h3>
              <div className="relative">
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="appearance-none bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="week">This Week</option>
                  <option value="month">This Month</option>
                  <option value="year">This Year</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Simple Line Chart Visualization */}
            <div className="h-64 flex items-end space-x-2">
              {processedData[timeRange as keyof typeof processedData].map((value, index) => (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-[#3452D1] rounded-t-sm transition-all duration-500 hover:bg-blue-700"
                    style={{
                      height: `${(value / Math.max(...processedData[timeRange as keyof typeof processedData])) * 200}px`,
                    }}
                  />
                  <span className="text-xs text-gray-500 mt-2">
                    {timeRange === "week"
                      ? `Day ${index + 1}`
                      : timeRange === "month"
                        ? `W${index + 1}`
                        : `M${index + 1}`}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Classification Distribution */}
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-800">Documents by Classification</h3>
              <div className="relative">
                <select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value)}
                  className="appearance-none bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 pr-8 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="pie">Pie Chart</option>
                  <option value="bar">Bar Chart</option>
                </select>
                <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {chartType === "pie" ? (
              /* Simple Pie Chart Visualization */
              <div className="flex items-center justify-center h-64">
                <div className="relative w-48 h-48">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    {classificationData.map((item, index) => {
                      const total = classificationData.reduce((sum, d) => sum + d.value, 0)
                      const percentage = (item.value / total) * 100
                      const strokeDasharray = `${percentage} ${100 - percentage}`
                      const strokeDashoffset = classificationData
                        .slice(0, index)
                        .reduce((sum, d) => sum + (d.value / total) * 100, 0)

                      return (
                        <circle
                          key={index}
                          cx="50"
                          cy="50"
                          r="15.915"
                          fill="transparent"
                          stroke={item.color}
                          strokeWidth="8"
                          strokeDasharray={strokeDasharray}
                          strokeDashoffset={-strokeDashoffset}
                          className="transition-all duration-300 hover:stroke-width-10"
                        />
                      )
                    })}
                  </svg>
                </div>
              </div>
            ) : (
              /* Bar Chart Visualization */
              <div className="h-64 flex items-end space-x-4">
                {classificationData.map((item, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center">
                    <div
                      className="w-full rounded-t-lg transition-all duration-500 hover:opacity-80"
                      style={{
                        height: `${(item.value / Math.max(...classificationData.map((d) => d.value))) * 200}px`,
                        backgroundColor: item.color,
                      }}
                    />
                    <span className="text-xs text-gray-500 mt-2 text-center">{item.name}</span>
                    <span className="text-xs font-medium text-gray-700">{item.value}%</span>
                  </div>
                ))}
              </div>
            )}

            {/* Legend */}
            <div className="mt-6 grid grid-cols-2 gap-2">
              {classificationData.map((item, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-gray-600">
                    {item.name}: {item.value}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8 bg-white rounded-xl border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">Recent Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                {
                  action: "Document classified",
                  document: "invoice_2024_001.pdf",
                  time: "2 minutes ago",
                  type: "success",
                },
                { action: "Review required", document: "contract_draft.docx", time: "5 minutes ago", type: "warning" },
                { action: "Document uploaded", document: "report_q1.pdf", time: "10 minutes ago", type: "info" },
                {
                  action: "Classification updated",
                  document: "resume_jane.pdf",
                  time: "15 minutes ago",
                  type: "success",
                },
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      activity.type === "success"
                        ? "bg-green-500"
                        : activity.type === "warning"
                          ? "bg-yellow-500"
                          : "bg-blue-500"
                    }`}
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">{activity.action}</p>
                    <p className="text-sm text-gray-500">{activity.document}</p>
                  </div>
                  <span className="text-xs text-gray-400">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
