import { Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import './PortfolioPage.css'

const projects = [
  {
    id: 'craip',
    title: 'CRAIP',
    subtitle: '4족 보행 로봇 자율주행 및 AI 임무 수행',
    description: 'Unitree Go1 로봇에 Particle Filter 위치 추정, YOLO 물체 인식, MPPI 경로 추종을 구현하고, 자연어 명령(OpenAI)으로 병원 환경 6가지 임무를 수행하는 ROS 2 기반 자율주행 시스템.',
    tech: ['ROS 2', 'Gazebo', 'YOLO', 'MPPI (C++)', 'OpenAI', 'Python'],
    period: '2025 Fall',
    link: '/portfolio/craip',
    highlight: '6 Missions',
  },
  {
    id: 'drobot',
    title: 'Drobot',
    subtitle: 'Drone + Robot 하이브리드 자율주행 시뮬레이션',
    description: 'ROS 2 + Gazebo 기반 4륜 스키드 스티어 + 쿼드콥터 하이브리드 로봇. Nav2 자율주행, SLAM 지도 생성, Jinja2 월드 생성기, YAML 규칙 엔진, AI 실험 에이전트까지 포함한 풀스택 로보틱스 프로젝트.',
    tech: ['ROS 2', 'Gazebo', 'Nav2', 'SLAM', 'PX4', 'Python'],
    period: '2026.01 ~ 진행중',
    link: '/portfolio/drobot',
    highlight: '150+ 테스트',
  },
  {
    id: 'onecheck',
    title: 'OneCheck',
    subtitle: '퇴직급여채무 명부 AI 자동검증 플랫폼',
    description: '수작업 3~4시간 걸리던 사원명부 검증을 5분으로 단축하는 웹 플랫폼. 규칙 기반 + AI 하이브리드 3-Layer 검증 엔진, 사용자 피드백 학습 시스템 구현.',
    tech: ['React', 'TypeScript', 'FastAPI', 'GPT-4o', 'SQLite'],
    period: '2026.01 ~ 02',
    link: '/portfolio/onecheck',
    highlight: '40x 속도 향상',
  },
]

export default function PortfolioPage() {
  return (
    <div className="pm">
      {/* Nav */}
      <nav className="pm-nav">
        <span className="pm-nav-name">Kangjun</span>
        <div className="pm-nav-right">
          <ThemeToggle />
        </div>
      </nav>

      {/* Profile */}
      <section className="pm-profile">
        <div className="pm-profile-inner">
          <div className="pm-avatar">KJ</div>
          <h1 className="pm-name">Kangjun</h1>
          <p className="pm-role">서울대학교 항공우주공학과</p>
          <p className="pm-bio">
            항공우주 시스템의 지능화와 자동화에 관심을 갖고 있으며,
            현장의 반복적인 문제를 소프트웨어로 직접 해결하는 경험을 쌓고 있습니다.
            AI 기반 의사결정 시스템과 데이터 파이프라인 설계를 공부하고 있습니다.
          </p>
          <div className="pm-info-grid">
            <div className="pm-info-item">
              <span className="pm-info-label">Education</span>
              <span className="pm-info-value">서울대학교 항공우주공학과</span>
            </div>
            <div className="pm-info-item">
              <span className="pm-info-label">Interest</span>
              <span className="pm-info-value">Aerospace · Robotics · AI</span>
            </div>
          </div>
          <div className="pm-links">
            <a href="https://github.com/protkjj" target="_blank" rel="noopener noreferrer" className="pm-link">
              GitHub
            </a>
            <a href="mailto:dlrkdwns1589@snu.ac.kr" className="pm-link">
              Email
            </a>
          </div>
        </div>
      </section>

      {/* Skills */}
      <section className="pm-section">
        <div className="pm-section-inner">
          <h2 className="pm-section-title">Skills</h2>
          <div className="pm-skills">
            <div className="pm-skill-group">
              <h4>Programming</h4>
              <div className="pm-tags">
                <span>Python</span><span>C/C++</span><span>TypeScript</span><span>MATLAB</span>
              </div>
            </div>
            <div className="pm-skill-group">
              <h4>AI / ML</h4>
              <div className="pm-tags">
                <span>GPT-4o</span><span>Few-shot Learning</span><span>Pandas</span><span>NumPy</span>
              </div>
            </div>
            <div className="pm-skill-group">
              <h4>Web / System</h4>
              <div className="pm-tags">
                <span>React</span><span>FastAPI</span><span>SQLite</span><span>REST API</span>
              </div>
            </div>
            <div className="pm-skill-group">
              <h4>Tools</h4>
              <div className="pm-tags">
                <span>Git</span><span>Linux</span><span>ROS</span><span>SolidWorks</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Projects */}
      <section className="pm-section pm-section-alt">
        <div className="pm-section-inner">
          <h2 className="pm-section-title">Projects</h2>
          <div className="pm-projects">
            {projects.map((p) => (
              <Link key={p.id} to={p.link} className="pm-project-card">
                <div className="pm-project-top">
                  <div>
                    <h3 className="pm-project-title">{p.title}</h3>
                    <p className="pm-project-subtitle">{p.subtitle}</p>
                  </div>
                  {p.highlight && (
                    <span className="pm-project-badge">{p.highlight}</span>
                  )}
                </div>
                <p className="pm-project-desc">{p.description}</p>
                <div className="pm-project-bottom">
                  <div className="pm-project-techs">
                    {p.tech.map((t) => (
                      <span key={t} className="pm-project-tech">{t}</span>
                    ))}
                  </div>
                  <span className="pm-project-period">{p.period}</span>
                </div>
                <span className="pm-project-arrow">→</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="pm-footer">
        <span>Kangjun · 2026</span>
      </footer>
    </div>
  )
}
