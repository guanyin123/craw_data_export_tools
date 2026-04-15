/**
 * 概览页面
 */
import { useEffect, useMemo, useCallback, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, message, Select } from 'antd'
import { ReloadOutlined, FilterOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useKeywordStore, useCrawlerStore } from '@/store/useStore'
import { CATEGORY_LABELS, CATEGORY_COLORS, type Keyword, type CategoryType } from '@/types'
import type { ColumnType } from 'antd/es/table'

// 安全的分类标签获取函数
const getCategoryLabel = (category: string | null): string => {
  if (!category) return '未分类'
  if (category in CATEGORY_LABELS) {
    return CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]
  }
  return '未分类'
}

export default function Dashboard() {
  // 当前选中的分类筛选
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  // 使用选择器优化订阅，只订阅需要的状态
  const keywords = useKeywordStore((state) => state.keywords)
  const loading = useKeywordStore((state) => state.loading)
  const total = useKeywordStore((state) => state.total)
  const categoryStats = useKeywordStore((state) => state.categoryStats)
  const refreshKeywords = useKeywordStore((state) => state.refreshKeywords)

  const status = useCrawlerStore((state) => state.status)
  const refreshStatus = useCrawlerStore((state) => state.refreshStatus)
  const crawlerLoading = useCrawlerStore((state) => state.loading)

  // 刷新数据的处理函数（带错误处理）
  const handleRefresh = useCallback(async () => {
    try {
      const params: { limit: number; category?: string } = { limit: 100 }
      if (selectedCategory) {
        params.category = selectedCategory
      }
      await refreshKeywords(params)
    } catch (error) {
      message.error('加载关键词失败')
    }
  }, [refreshKeywords, selectedCategory])

  // 处理分类筛选
  const handleCategoryChange = useCallback(async (category: string | null | undefined) => {
    const normalizedCategory = category === null || category === undefined ? null : category
    setSelectedCategory(normalizedCategory)
    try {
      // 当 category 为 null 时，不传递 category 参数，让后端返回所有数据
      const params: { limit: number; category?: string } = { limit: 100 }
      if (normalizedCategory) {
        params.category = normalizedCategory
      }
      await refreshKeywords(params)
    } catch (error) {
      message.error('加载关键词失败')
    }
  }, [refreshKeywords])

  // 处理分类统计卡片点击
  const handleCategoryClick = useCallback((category: string) => {
    const normalizedCategory = category === '未分类' ? null : category
    handleCategoryChange(normalizedCategory)
  }, [handleCategoryChange])

  // 初始化和自动刷新
  useEffect(() => {
    let mounted = true

    const initializeData = async () => {
      try {
        // 并行初始化关键词和爬虫状态
        await Promise.all([
          refreshKeywords({ limit: 100 }),
          refreshStatus(),
        ])
      } catch (error) {
        if (mounted) {
          message.error('初始化数据失败')
        }
      }
    }

    initializeData()

    // 清理函数：防止内存泄漏
    return () => {
      mounted = false
    }
  }, [refreshKeywords, refreshStatus])

  // 使用 useMemo 稳定 columns 引用，避免不必要的重渲染
  const columns: ColumnType<Keyword>[] = useMemo(() => [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: unknown, __: Keyword, index: number) => index + 1,
    },
    {
      title: '关键词',
      dataIndex: 'word',
      key: 'word',
      width: 150,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category: string | null) => (
        <Tag
          color={category ? CATEGORY_COLORS[category] : 'default'}
        >
          {getCategoryLabel(category)}
        </Tag>
      ),
    },
    {
      title: '出现次数',
      dataIndex: 'count',
      key: 'count',
      width: 100,
      sorter: (a, b) => a.count - b.count,
      defaultSortOrder: 'descend',
    },
    {
      title: '最后出现',
      dataIndex: 'last_seen',
      key: 'last_seen',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
  ], [])

  // 格式化最后抓取时间
  const lastRunDisplay = useMemo(() => {
    return status.last_run ? dayjs(status.last_run).format('YYYY-MM-DD HH:mm') : '-'
  }, [status.last_run])

  // 生成分类筛选选项
  const categoryOptions = useMemo(() => {
    const options = [
      { label: '全部', value: undefined },
      ...Object.entries(CATEGORY_LABELS).map(([key, label]) => ({
        label,
        value: key,
      })),
      { label: '未分类', value: 'OTHER' },
    ]
    return options
  }, [])

  // Select 组件的值（将 null 转换为 undefined）
  const selectValue = selectedCategory === null ? undefined : selectedCategory

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <h2>概览</h2>
        <Button
          icon={<ReloadOutlined />}
          loading={loading || crawlerLoading}
          onClick={handleRefresh}
          aria-label="刷新数据"
        >
          刷新
        </Button>
      </Space>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="关键词总数" value={total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="最后抓取"
              value={lastRunDisplay}
              style={{ fontSize: '14px' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="上次抓取数量"
              value={status.last_count || 0}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="爬虫状态"
              value={status.is_running ? '运行中' : '空闲'}
              valueStyle={{ color: status.is_running ? '#52c41a' : '#8c8c8c' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 分类统计 */}
      <Card
        title={
          <Space>
            <span>分类统计</span>
            <Button
              type="text"
              size="small"
              icon={<FilterOutlined />}
              onClick={() => handleCategoryChange(null)}
              style={{ fontSize: '12px', color: '#999' }}
              aria-label="清除分类筛选"
            >
              {selectedCategory ? '清除筛选' : '点击分类筛选'}
            </Button>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        <Row gutter={16}>
          {Object.entries(categoryStats).map(([category, count]) => {
            const isSelected = selectedCategory === category ||
              (selectedCategory === 'OTHER' && !category) ||
              (selectedCategory === null && false)
            const categoryLabel = getCategoryLabel(category)
            return (
              <Col span={3} key={category}>
                <div
                  onClick={() => handleCategoryClick(category || 'OTHER')}
                  role="button"
                  tabIndex={0}
                  aria-label={`筛选 ${categoryLabel} 分类 (${count} 个关键词)`}
                  aria-pressed={isSelected}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      handleCategoryClick(category || 'OTHER')
                    }
                  }}
                  style={{
                    cursor: 'pointer',
                    padding: '8px',
                    borderRadius: '4px',
                    backgroundColor: isSelected ? `${CATEGORY_COLORS[category] || '#8c8c8c'}20` : 'transparent',
                    transition: 'background-color 0.2s',
                  }}
                >
                  <Statistic
                    title={categoryLabel}
                    value={count}
                    valueStyle={{
                      color: CATEGORY_COLORS[category] || '#8c8c8c',
                      fontSize: '20px'
                    }}
                  />
                </div>
              </Col>
            )
          })}
        </Row>
      </Card>

      {/* 关键词榜单 */}
      <Card
        title={
          <Space>
            <span>热门关键词</span>
            {selectedCategory && (
              <Tag color={CATEGORY_COLORS[selectedCategory]}>
                {getCategoryLabel(selectedCategory)}: {keywords.length}
              </Tag>
            )}
            <Select
              value={selectValue}
              onChange={(value) => handleCategoryChange(value ?? null)}
              options={categoryOptions}
              style={{ width: 120 }}
              size="small"
              placeholder="选择分类"
            />
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={keywords}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>
    </div>
  )
}
