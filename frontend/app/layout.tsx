import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'control-surface-agent',
  description: 'A control surface for supervised AI decision workflows.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
