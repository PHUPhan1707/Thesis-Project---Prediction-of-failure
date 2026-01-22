import './App.css'

interface FeatureCard {
  id: string;
  title: string;
  description: string;
  icon: string;
  status: 'mvp' | 'extended';
  priority?: string;
}

function App() {
  const mvpFeatures: FeatureCard[] = [
    {
      id: '1',
      title: 'Cảnh Báo Sớm Học Viên',
      description: 'Phân tích các chỉ số như tần suất truy cập, điểm quiz, tiến độ nộp bài, mức độ tương tác để đưa ra cảnh báo phân loại theo mức độ (cao/trung bình/thấp)',
      icon: '🚨',
      status: 'mvp',
      priority: 'Bắt buộc'
    },
    {
      id: '2',
      title: 'Danh Sách Học Viên Cần Quan Tâm',
      description: 'Dashboard hiển thị danh sách học viên cần quan tâm với thông tin chi tiết và gợi ý hành động can thiệp',
      icon: '👥',
      status: 'mvp',
      priority: 'Bắt buộc'
    },
    {
      id: '3',
      title: 'Tích Hợp Open edX',
      description: 'Tích hợp vào giao diện giảng viên của Open edX dưới dạng trang riêng hoặc plugin',
      icon: '🔌',
      status: 'mvp',
      priority: 'Bắt buộc'
    }
  ];

  const extendedFeatures: FeatureCard[] = [
    {
      id: '4',
      title: 'Phân Tích Nội Dung Khó',
      description: 'Tổng hợp câu hỏi forum theo chủ đề, phát hiện video hoặc quiz có tỷ lệ bỏ qua cao hoặc sai nhiều',
      icon: '📊',
      status: 'extended'
    },
    {
      id: '5',
      title: 'So Sánh Hiệu Quả Giảng Dạy',
      description: 'Báo cáo xu hướng qua các kỳ học để giảng viên cải tiến nội dung',
      icon: '📈',
      status: 'extended'
    },
    {
      id: '6',
      title: 'Phân Nhóm Học Viên Tự Động',
      description: 'Clustering để gửi thông báo hoặc tài liệu phù hợp cho từng nhóm',
      icon: '🎯',
      status: 'extended'
    },
    {
      id: '7',
      title: 'Dashboard Tổng Quan',
      description: 'Trang chủ hiển thị các chỉ số quan trọng và việc cần làm trong ngày',
      icon: '🏠',
      status: 'extended'
    },
    {
      id: '8',
      title: 'Phân Tích Engagement',
      description: 'Thống kê xem video, tương tác forum, thời gian học để đánh giá chất lượng từng phần học liệu',
      icon: '💡',
      status: 'extended'
    }
  ];

  return (
    <div className="app">
      {/* Hero Section */}
      <header className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-text">Open edX Analytics Platform</span>
          </div>
          <h1 className="hero-title">
            Xây dựng hệ thống phân tích dữ liệu và hỗ trợ quyết định cho giảng viên trên nền tảng Open edX
          </h1>
          <p className="hero-description">
            Nghiên cứu và phát triển hệ thống dashboard giúp giảng viên theo dõi và can thiệp kịp thời trong quá trình giảng dạy trực tuyến.
            Hệ thống tích hợp vào nền tảng Open edX hiện có của trường, khai thác dữ liệu học tập để cung cấp thông tin hỗ trợ giảng viên ra quyết định.
          </p>
        </div>
        <div className="hero-decoration">
          <div className="decoration-circle circle-1"></div>
          <div className="decoration-circle circle-2"></div>
          <div className="decoration-circle circle-3"></div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* MVP Features Section */}
        <section className="features-section">
          <div className="section-header">
            <h2 className="section-title">
              <span className="title-icon">⭐</span>
              Yêu Cầu Bắt Buộc (MVP)
            </h2>
            <p className="section-subtitle">Các chức năng cốt lõi cần được triển khai</p>
          </div>
          <div className="features-grid">
            {mvpFeatures.map((feature) => (
              <div key={feature.id} className="feature-card mvp-card">
                <div className="card-header">
                  <div className="card-icon">{feature.icon}</div>
                  <span className="card-badge mvp-badge">{feature.priority}</span>
                </div>
                <h3 className="card-title">{feature.title}</h3>
                <p className="card-description">{feature.description}</p>
                <div className="card-footer">
                  <span className="card-status mvp-status">MVP</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Extended Features Section */}
        <section className="features-section">
          <div className="section-header">
            <h2 className="section-title">
              <span className="title-icon">🚀</span>
              Yêu Cầu Mở Rộng
            </h2>
            <p className="section-subtitle">Các tính năng nâng cao tùy theo năng lực và thời gian</p>
          </div>
          <div className="features-grid">
            {extendedFeatures.map((feature) => (
              <div key={feature.id} className="feature-card extended-card">
                <div className="card-header">
                  <div className="card-icon">{feature.icon}</div>
                  <span className="card-badge extended-badge">Tùy chọn</span>
                </div>
                <h3 className="card-title">{feature.title}</h3>
                <p className="card-description">{feature.description}</p>
                <div className="card-footer">
                  <span className="card-status extended-status">Mở rộng</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>© 2025 Hệ thống Phân tích Dữ liệu Open edX - Dự án Nghiên cứu</p>
      </footer>
    </div>
  )
}

export default App
