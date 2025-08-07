"use client"

import { useEffect } from "react"
import { CheckCircle } from "lucide-react"

export default function GmailConnectedPage() {
  useEffect(() => {
    // Notify the parent window that Gmail connection was successful
    if (window.opener) {
      window.opener.postMessage({ type: 'gmail_connected' }, '*')
      window.close()
    } else {
      // If not opened in a popup, redirect to upload page after a delay
      setTimeout(() => {
        window.location.href = '/upload'
      }, 3000)
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Gmail Connected Successfully!</h1>
        <p className="text-gray-600 mb-4">
          Your Gmail account has been connected. You can now receive documents directly from your email attachments.
        </p>
        <p className="text-sm text-gray-500">
          This window will close automatically...
        </p>
      </div>
    </div>
  )
}
