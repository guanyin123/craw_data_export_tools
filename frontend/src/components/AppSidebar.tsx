/**
 * 应用侧边栏组件
 */
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  AppstoreOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

const { Sider } = Layout

type MenuItem = {
  key: string
  icon: React.ReactNode
  label: string
  path: string
}

const menuItems: MenuItem[] = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '概览',
    path: '/dashboard',
  },
  {
    key: 'trends',
    icon: <LineChartOutlined />,
    label: '趋势',
    path: '/trends',
  },
  {
    key: 'categories',
    icon: <AppstoreOutlined />,
    label: '分类',
    path: '/categories',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '设置',
    path: '/settings',
  },
]

interface AppSidebarProps {
  collapsed?: boolean
}

export default function AppSidebar({ collapsed = false }: AppSidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const handleMenuClick = ({ key }: { key: string }) => {
    const item = menuItems.find((i) => i.key === key)
    if (item) {
      navigate(item.path)
    }
  }

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      width={200}
      collapsedWidth={80}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 10,
      }}
      trigger={null}
      theme="light"
    >
      <div
        style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#1890ff' }}>
          {collapsed ? 'OD' : 'Opportunity'}
        </span>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname.split('/')[1] || 'dashboard']}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Sider>
  )
}
