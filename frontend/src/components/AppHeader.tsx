/**
 * 应用头部组件
 */
import { Layout, Button, Space } from 'antd'
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'
import { useAppStore } from '@/store/useStore'

const { Header } = Layout

export default function AppHeader() {
  // 使用选择器只订阅需要的状态
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed)
  const setSidebarCollapsed = useAppStore((state) => state.setSidebarCollapsed)

  return (
    <Header
      style={{
        padding: '0 16px',
        background: '#fff',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <Space>
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
        <h1 style={{ fontSize: '18px', margin: 0 }}>商机发现</h1>
      </Space>

      <Space>
        <span style={{ color: '#8c8c8c' }}>MVP v0.1.0</span>
      </Space>
    </Header>
  )
}
