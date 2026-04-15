/**
 * 路由配置
 */
import { createBrowserRouter, Navigate } from 'react-router-dom'
import App from '@/App'

// 页面组件（懒加载）
import Dashboard from '@/pages/Dashboard'
import Trends from '@/pages/Trends'
import Categories from '@/pages/Categories'
import KeywordDetail from '@/pages/KeywordDetail'
import Settings from '@/pages/Settings'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'trends',
        element: <Trends />,
      },
      {
        path: 'categories',
        element: <Categories />,
      },
      {
        path: 'keyword/:id',
        element: <KeywordDetail />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
    ],
  },
])
