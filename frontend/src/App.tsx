/**
 * 根组件
 */
import { Outlet } from 'react-router-dom'
import { Layout } from 'antd'
import AppHeader from '@/components/AppHeader'
import AppSidebar from '@/components/AppSidebar'
import { useAppStore } from '@/store/useStore'

const { Content } = Layout

// 侧边栏宽度常量（与 Ant Design Sider 默认宽度一致）
const SIDEBAR_WIDTH = 200
const SIDEBAR_COLLAPSED_WIDTH = 80

export default function App() {
  // 使用选择器只订阅需要的状态，避免不必要的重渲染
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed)

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <AppSidebar collapsed={sidebarCollapsed} />
      <Layout
        style={{
          marginLeft: sidebarCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH,
          height: '100vh',
          overflow: 'hidden',
          transition: 'margin-left 0.2s',
        }}
      >
        <AppHeader />
        <Content
          style={{
            margin: '16px',
            padding: '24px',
            background: '#fff',
            borderRadius: '8px',
            height: 'calc(100vh - 64px - 32px)', // 固定高度
            overflowY: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
