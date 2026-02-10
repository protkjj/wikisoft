import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import './PortfolioOneCheck.css' // 같은 pf- 스타일 재사용

export default function PortfolioDrobot() {
  const [navOpen, setNavOpen] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) entry.target.classList.add('visible')
        })
      },
      { threshold: 0.08, rootMargin: '0px 0px -40px 0px' }
    )
    document.querySelectorAll('.pf-animate').forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <div className="pf">
      {/* Navigation */}
      <nav className="pf-nav">
        <div className="pf-nav-left">
          <Link to="/portfolio" className="pf-logo">KJ</Link>
          <span className="pf-nav-divider">/</span>
          <span className="pf-nav-project">Drobot</span>
        </div>
        <button className="pf-nav-toggle" onClick={() => setNavOpen(!navOpen)}>
          {navOpen ? '\u2715' : '\u2630'}
        </button>
        <div className={`pf-nav-right ${navOpen ? 'open' : ''}`}>
          <a href="#overview" onClick={() => setNavOpen(false)}>Overview</a>
          <a href="#architecture" onClick={() => setNavOpen(false)}>Architecture</a>
          <a href="#tech" onClick={() => setNavOpen(false)}>Tech</a>
          <a href="#results" onClick={() => setNavOpen(false)}>Results</a>
          <ThemeToggle />
        </div>
      </nav>

      {/* Hero */}
      <section className="pf-hero">
        <div className="pf-hero-inner">
          <span className="pf-hero-badge">Personal Project · In Progress</span>
          <h1 className="pf-hero-title">Drobot</h1>
          <p className="pf-hero-subtitle">
            Drone + Robot 하이브리드 자율주행<br />
            시뮬레이션 플랫폼
          </p>
          <div className="pf-hero-stats">
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">3 Phase</span>
              <span className="pf-hero-stat-label">지상 → 비행 → 하이브리드</span>
            </div>
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">150+</span>
              <span className="pf-hero-stat-label">자동화 테스트</span>
            </div>
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">4 Pkg</span>
              <span className="pf-hero-stat-label">모듈형 ROS 2 구조</span>
            </div>
          </div>
        </div>
      </section>

      {/* Overview */}
      <section id="overview" className="pf-section pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">PROJECT OVERVIEW</div>
          <h2 className="pf-section-title">프로젝트 소개</h2>

          <div className="pf-overview-grid">
            <div className="pf-overview-card">
              <h3>배경</h3>
              <p>
                지상 주행과 공중 비행을 모두 수행할 수 있는 하이브리드 로봇은
                재난 현장, 물류, 탐사 등에서 높은 활용 가능성을 가집니다.
                SolidWorks로 직접 설계한 4륜 + 쿼드콥터 로봇을 ROS 2 환경에서 시뮬레이션하고,
                자율주행 시스템을 구축하는 것이 목표입니다.
              </p>
            </div>
            <div className="pf-overview-card">
              <h3>접근</h3>
              <p>
                단계적으로 접근합니다. <strong>Phase 1</strong>에서 지상 자율주행(Nav2 + SLAM)을 완성하고,
                <strong>Phase 2</strong>에서 PX4 기반 드론 비행을 연동한 뒤,
                최종적으로 <strong>Phase 3</strong>에서 주행↔비행 모드 전환이 가능한 하이브리드 시스템을 구현합니다.
              </p>
            </div>
          </div>

          {/* Roadmap */}
          <div className="pf-feature-list">
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--success)' }}>P1</div>
              <div>
                <strong>지상 주행 — 2D Navigation ✓</strong>
                <span>Nav2 + SLAM Toolbox 기반 자율주행, Frontier 탐색, YAML 규칙 엔진</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--warning)' }}>P2</div>
              <div>
                <strong>드론 비행 — 3D Control (진행중)</strong>
                <span>PX4 SITL + Micro XRCE-DDS 연동, 이륙/호버링/착륙 테스트</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num">P3</div>
              <div>
                <strong>하이브리드 — 지상+비행 전환 (예정)</strong>
                <span>모드 전환 로직, 3D SLAM (RTAB-Map), 3D 경로 계획</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="pf-section pf-section-alt pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">ARCHITECTURE</div>
          <h2 className="pf-section-title">시스템 아키텍처</h2>

          {/* Package diagram */}
          <div className="pf-arch-diagram">
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">drobot_description</span>
                <span className="pf-arch-box-sub">URDF · STL · Worlds · Generators</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↑</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">drobot_navigation</span>
                <span className="pf-arch-box-sub">Goal Navigator · Rule Engine</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↑</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">drobot_bringup</span>
                <span className="pf-arch-box-sub">Launch · Nav2 · SLAM · EKF Config</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↑</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">drobot_agent</span>
                <span className="pf-arch-box-sub">AI 실험 자동화 프레임워크</span>
              </div>
            </div>
          </div>

          {/* Frame structure */}
          <h3 className="pf-subsection-title">TF Frame 구조</h3>
          <div className="pf-pipeline">
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l1">TF</div>
              <div className="pf-pipeline-info">
                <strong>map → odom → base_footprint → base_link</strong>
                <span>SLAM이 map→odom, EKF가 odom→base_footprint TF 발행. Gazebo DiffDrive는 중복 방지를 위해 odom TF 비활성화</span>
              </div>
            </div>
          </div>

          {/* AI Agent pipeline */}
          <h3 className="pf-subsection-title">AI Agent Pipeline</h3>
          <div className="pf-pipeline">
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l2">1</div>
              <div className="pf-pipeline-info">
                <strong>WorldGen</strong>
                <span>Jinja2 SDF 템플릿 + YAML config로 월드 자동 생성, SDF 검증, 목표 지점 제안</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l2">2</div>
              <div className="pf-pipeline-info">
                <strong>ParamTuner</strong>
                <span>Nav2 파라미터 검증 + 난이도별 변형 생성 + 휴리스틱 기반 자동 튜닝</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l3">3</div>
              <div className="pf-pipeline-info">
                <strong>Simulator → Evaluator</strong>
                <span>Gazebo 실행 + 성능 메트릭 수집 (경로 길이, 소요 시간, 충돌 횟수)</span>
              </div>
            </div>
          </div>

          <div className="pf-note">
            <strong>World Generator</strong> — YAML config 하나로 사무실, 창고, 미로 등 다양한 월드를 생성합니다. Gazebo Fuel 3D 모델 17종 (책상, 의자, 선반 등)을 지원하고, matplotlib로 top-down 시각화도 가능합니다.
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section id="tech" className="pf-section pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">TECH STACK</div>
          <h2 className="pf-section-title">사용 기술</h2>

          <div className="pf-tech-categories">
            <div className="pf-tech-category">
              <h4>Robotics</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">ROS 2 Jazzy</span>
                <span className="pf-tech-tag">Nav2</span>
                <span className="pf-tech-tag">SLAM Toolbox</span>
                <span className="pf-tech-tag">PX4</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Simulation</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">Gazebo Harmonic</span>
                <span className="pf-tech-tag">URDF / Xacro</span>
                <span className="pf-tech-tag">SDF</span>
                <span className="pf-tech-tag">Isaac Sim (예정)</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Design / Tools</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">SolidWorks</span>
                <span className="pf-tech-tag">Jinja2</span>
                <span className="pf-tech-tag">matplotlib</span>
                <span className="pf-tech-tag">pytest</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Programming</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">Python 3</span>
                <span className="pf-tech-tag">C++</span>
                <span className="pf-tech-tag">YAML</span>
                <span className="pf-tech-tag">XML</span>
              </div>
            </div>
          </div>

          <h3 className="pf-subsection-title">설계 결정</h3>
          <div className="pf-decisions">
            <div className="pf-decision">
              <div className="pf-decision-q">왜 Phase별 점진적 개발?</div>
              <div className="pf-decision-a">
                하이브리드 로봇은 지상 주행과 비행의 제어 체계가 완전히 다릅니다.
                각 Phase를 독립적으로 완성한 뒤 통합하는 방식으로 복잡도를 관리합니다.
              </div>
            </div>
            <div className="pf-decision">
              <div className="pf-decision-q">왜 YAML 기반 월드 생성?</div>
              <div className="pf-decision-a">
                SDF를 직접 작성하면 수백 줄이 필요하지만, YAML config + Jinja2 템플릿 조합으로
                10줄 내외의 설정만으로 복잡한 환경을 재현 가능하게 만들었습니다.
              </div>
            </div>
            <div className="pf-decision">
              <div className="pf-decision-q">왜 AI Agent 프레임워크?</div>
              <div className="pf-decision-a">
                Nav2 파라미터 튜닝은 시행착오가 많습니다. 월드 생성 → 파라미터 변형 → 시뮬레이션 → 평가를
                자동화하는 에이전트를 만들어 실험 효율을 높였습니다.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Results */}
      <section id="results" className="pf-section pf-section-alt pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">RESULTS</div>
          <h2 className="pf-section-title">성과</h2>

          <div className="pf-results-grid">
            <div className="pf-result-card">
              <div className="pf-result-num">150+</div>
              <div className="pf-result-desc">자동화 테스트</div>
              <div className="pf-result-detail">Rule Engine 18 + World Gen 44 + Agent 88</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">4</div>
              <div className="pf-result-desc">ROS 2 패키지</div>
              <div className="pf-result-detail">Description · Navigation · Bringup · Agent</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">3</div>
              <div className="pf-result-desc">프리셋 월드</div>
              <div className="pf-result-detail">Empty · Office · Warehouse</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">17</div>
              <div className="pf-result-desc">Fuel 3D 모델</div>
              <div className="pf-result-detail">책상, 선반, 차량 등 카탈로그</div>
            </div>
          </div>

          <h3 className="pf-subsection-title">구현 현황</h3>
          <table className="pf-compare-table">
            <thead>
              <tr><th>Phase</th><th>항목</th><th>상태</th></tr>
            </thead>
            <tbody>
              <tr>
                <td rowSpan={4}>Phase 1<br />지상 주행</td>
                <td>Nav2 + SLAM 자율주행</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>Frontier-based 자동 탐색</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>Jinja2 월드 생성기 + 시각화</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>YAML 규칙 엔진</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td rowSpan={2}>Phase 2<br />드론 비행</td>
                <td>PX4 SITL + ROS 2 연동</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>호버링 / 이륙 / 착륙 제어</td>
                <td className="pf-before">진행중</td>
              </tr>
              <tr>
                <td rowSpan={2}>Phase 3<br />하이브리드</td>
                <td>주행 ↔ 비행 모드 전환</td>
                <td className="pf-before">예정</td>
              </tr>
              <tr>
                <td>3D SLAM + 3D 경로 계획</td>
                <td className="pf-before">예정</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Footer */}
      <footer className="pf-footer">
        <div className="pf-footer-inner">
          <div className="pf-footer-name">Kangjun</div>
          <div className="pf-footer-project">Drobot · 2026</div>
          <Link to="/portfolio" className="pf-footer-link">← All Projects</Link>
        </div>
      </footer>
    </div>
  )
}
