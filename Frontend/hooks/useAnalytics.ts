import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface DashboardStats {
  total_documents: number
  avg_confidence: number
  needs_review_count: number
  by_classification: Array<{ classification_type: string; count: number }>
  by_status: Array<{ processing_status: string; count: number }>
  daily_processed: Array<{ date: string; count: number }>
  monthly_processed: Array<{ month: string; count: number }>
  recent_activity: Array<{
    document_id: string
    original_filename: string
    processing_status: string
    classification_type: string
    upload_timestamp: string
    uploaded_by: string
  }>
}

interface ProcessedData {
  week: number[]
  month: number[]
  year: number[]
}

interface ClassificationData {
  name: string
  value: number
  color: string
}

const useAnalytics = () => {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalytics = async () => {
    if (!user) return

    try {
      setLoading(true)
      const response = await fetch(`http://localhost:5000/api/analytics/dashboard?user_id=${user.user_id}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch analytics')
      }

      const result = await response.json()
      
      if (result.success) {
        setStats(result.data)
        setError(null)
      } else {
        throw new Error(result.error || 'Failed to fetch analytics')
      }
    } catch (err) {
      console.error('Analytics fetch error:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [user])

  // Transform data for charts
  const getProcessedData = (): ProcessedData => {
    if (!stats) return { week: [], month: [], year: [] }

    // Fill in missing days for the week view (last 7 days)
    const today = new Date()
    const weekData: number[] = []
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)
      const dateString = date.toISOString().split('T')[0]
      
      const dayData = stats.daily_processed.find(d => d.date === dateString)
      weekData.push(dayData ? dayData.count : 0)
    }

    // Fill in missing months for the month view (last 12 months)
    const monthData: number[] = []
    
    for (let i = 11; i >= 0; i--) {
      const date = new Date(today)
      date.setMonth(date.getMonth() - i)
      const monthString = date.toISOString().substring(0, 7) // YYYY-MM format
      
      const monthItem = stats.monthly_processed.find(d => 
        d.month.startsWith(monthString)
      )
      monthData.push(monthItem ? monthItem.count : 0)
    }

    // For year view, use monthly data as well
    const yearData = [...monthData]

    return {
      week: weekData,
      month: monthData,
      year: yearData
    }
  }

  const getClassificationData = (): ClassificationData[] => {
    if (!stats || !stats.by_classification.length) {
      return [
        { name: "No Data", value: 100, color: "#F3F4F6" }
      ]
    }

    const colors = ["#3452D1", "#60A5FA", "#93C5FD", "#DBEAFE", "#F3F4F6"]
    const total = stats.by_classification.reduce((sum, item) => sum + item.count, 0)

    return stats.by_classification.map((item, index) => ({
      name: item.classification_type || 'Unclassified',
      value: Math.round((item.count / total) * 100),
      color: colors[index % colors.length]
    }))
  }

  const getFormattedStats = () => {
    if (!stats) {
      return [
        {
          title: "Documents Ingested",
          value: "0",
          change: "0%",
          changeType: "neutral" as const,
        },
        {
          title: "Avg. Confidence Score",
          value: "0%",
          change: "0%",
          changeType: "neutral" as const,
        },
        {
          title: "Review Actions",
          value: "0",
          change: "0%",
          changeType: "neutral" as const,
        },
      ]
    }

    return [
      {
        title: "Documents Ingested",
        value: stats.total_documents.toLocaleString(),
        change: "+0%", // TODO: Calculate change from previous period
        changeType: "positive" as const,
      },
      {
        title: "Avg. Confidence Score",
        value: `${Math.round(stats.avg_confidence * 100)}%`,
        change: "+0%", // TODO: Calculate change from previous period
        changeType: "positive" as const,
      },
      {
        title: "Review Actions",
        value: stats.needs_review_count.toString(),
        change: "+0%", // TODO: Calculate change from previous period
        changeType: stats.needs_review_count > 0 ? "negative" as const : "positive" as const,
      },
    ]
  }

  const getRecentActivity = () => {
    if (!stats?.recent_activity) return []

    return stats.recent_activity.map(activity => {
      const date = new Date(activity.upload_timestamp)
      const timeAgo = getTimeAgo(date)
      
      let actionText = "Document uploaded"
      let type = "info"
      
      if (activity.processing_status === "classified") {
        actionText = "Document classified"
        type = "success"
      } else if (activity.processing_status === "needs_review") {
        actionText = "Review required"
        type = "warning"
      } else if (activity.processing_status === "routed") {
        actionText = "Document processed"
        type = "success"
      }

      return {
        action: actionText,
        document: activity.original_filename,
        time: timeAgo,
        type
      }
    })
  }

  const getTimeAgo = (date: Date): string => {
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return "Just now"
    if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`
    
    const diffInDays = Math.floor(diffInHours / 24)
    if (diffInDays < 30) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`
    
    return date.toLocaleDateString()
  }

  return {
    stats,
    loading,
    error,
    refetch: fetchAnalytics,
    getProcessedData,
    getClassificationData,
    getFormattedStats,
    getRecentActivity
  }
}

export default useAnalytics
