import MainLayout from '../components/layout/MainLayout'
import ChatWindow from '../components/chat/ChatWindow'
import { useDocuments } from '../hooks/useDocuments'

function DashboardPage() {
  useDocuments()

  return (
    <MainLayout>
      <ChatWindow />
    </MainLayout>
  )
}

export default DashboardPage
