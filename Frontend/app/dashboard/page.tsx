"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import useAnalytics from "@/hooks/useAnalytics"
import Layout from "@/components/Layout"
import { FileText, TrendingUp, AlertTriangle, ChevronDown, RefreshCw } from "lucide-react"

export default function Dashboard() {
  const { user, token, isLoading } = useAuth()
  const router = useRouter()
  const [timeRange, setTimeRange] = useState("week")
  const [chartType, setChartType] = useState("pie")
  
  const { 
    stats, 
    loading: analyticsLoading, 
    error: analyticsError,
    refetch: refetchAnalytics,
    getProcessedData,
    getClassificationData,
    getFormattedStats,
    getRecentActivity
  } = useAnalytics()

  // Authentication check - CRITICAL SECURITY FIX
  useEffect(() => {
    // Wait for auth loading to complete before checking authentication
    if (isLoading) return
    
    if (!user || !token) {
      router.replace('/login')
      return
    }
  }, [user, token, isLoading, router])

  // Show loading spinner while checking authentication or loading analytics
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

  const processedData = getProcessedData()
  const classificationData = getClassificationData()
  const formattedStats = getFormattedStats()
  const recentActivity = getRecentActivity()

  return (
    <Layout>
      <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Dashboard</h1>
            <p className="text-gray-600">Overview of your document processing activities</p>
          </div>
          <button
            onClick={refetchAnalytics}
            disabled={analyticsLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${analyticsLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Error State */}
        {analyticsError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">Error loading analytics: {analyticsError}</p>
            <button
              onClick={refetchAnalytics}
              className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {analyticsLoading && (
          <div className="mb-6 p-6 bg-white rounded-xl border border-gray-200">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">Loading analytics...</span>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {formattedStats.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  <p className={`text-sm mt-2 ${stat.changeType === "positive" ? "text-green-600" : stat.changeType === "negative" ? "text-red-600" : "text-gray-500"}`}>
                    {stat.change} from last period
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  {index === 0 && <FileText className="w-6 h-6 text-[#3452D1]" />}
                  {index === 1 && <TrendingUp className="w-6 h-6 text-[#3452D1]" />}
                  {index === 2 && <AlertTriangle className="w-6 h-6 text-[#3452D1]" />}
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

            {/* Simple Bar Chart Visualization */}
            <div className="h-64 flex items-end space-x-2">
              {processedData[timeRange as keyof typeof processedData].length === 0 ? (
                <div className="w-full h-full flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>No data available</p>
                  </div>
                </div>
              ) : (
                processedData[timeRange as keyof typeof processedData].map((value, index) => {
                  const maxValue = Math.max(...processedData[timeRange as keyof typeof processedData])
                  const height = maxValue > 0 ? (value / maxValue) * 200 : 0
                  
                  return (
                    <div key={index} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-[#3452D1] rounded-t-sm transition-all duration-500 hover:bg-blue-700 min-h-[2px]"
                        style={{
                          height: `${Math.max(height, value > 0 ? 2 : 0)}px`,
                        }}
                        title={`${value} documents`}
                      />
                      <span className="text-xs text-gray-500 mt-2">
                        {timeRange === "week"
                          ? `D${index + 1}`
                          : timeRange === "month"
                            ? `W${index + 1}`
                            : `M${index + 1}`}
                      </span>
                    </div>
                  )
                })
              )}
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
                {classificationData.length === 1 && classificationData[0].name === "No Data" ? (
                  <div className="text-center text-gray-500">
                    <TrendingUp className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>No classification data available</p>
                  </div>
                ) : (
                  <div className="relative w-48 h-48">
                    <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                      {classificationData.map((item, index) => {
                        const total = classificationData.reduce((sum, d) => sum + d.value, 0)
                        const percentage = (item.value / total) * 100
                        const strokeDasharray = `${percentage} ${100 - percentage}`
                        const strokeDashoffset = -classificationData
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
                            strokeDashoffset={strokeDashoffset}
                            className="transition-all duration-300 hover:stroke-width-10"
                          >
                            <title>{`${item.name}: ${item.value}%`}</title>
                          </circle>
                        )
                      })}
                    </svg>
                  </div>
                )}
              </div>
            ) : (
              /* Bar Chart Visualization */
              <div className="h-64 flex items-end space-x-4">
                {classificationData.length === 1 && classificationData[0].name === "No Data" ? (
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <TrendingUp className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      <p>No classification data available</p>
                    </div>
                  </div>
                ) : (
                  classificationData.map((item, index) => (
                    <div key={index} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full rounded-t-lg transition-all duration-500 hover:opacity-80"
                        style={{
                          height: `${(item.value / Math.max(...classificationData.map((d) => d.value))) * 200}px`,
                          backgroundColor: item.color,
                          minHeight: '8px'
                        }}
                        title={`${item.name}: ${item.value}%`}
                      />
                      <span className="text-xs text-gray-500 mt-2 text-center truncate w-full" title={item.name}>
                        {item.name.length > 8 ? `${item.name.substring(0, 8)}...` : item.name}
                      </span>
                      <span className="text-xs font-medium text-gray-700">{item.value}%</span>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Legend */}
            {!(classificationData.length === 1 && classificationData[0].name === "No Data") && (
              <div className="mt-6 grid grid-cols-2 gap-2 max-h-24 overflow-y-auto">
                {classificationData.map((item, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-gray-600 truncate" title={item.name}>
                      {item.name}: {item.value}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-8 bg-white rounded-xl border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">Recent Activity</h3>
          </div>
          <div className="p-6">
            {recentActivity.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No recent activity</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
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
                      <p className="text-sm text-gray-500" title={activity.document}>
                        {activity.document.length > 50 
                          ? `${activity.document.substring(0, 50)}...` 
                          : activity.document
                        }
                      </p>
                    </div>
                    <span className="text-xs text-gray-400">{activity.time}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
