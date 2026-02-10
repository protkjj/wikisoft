import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import './PortfolioOneCheck.css' // 같은 pf- 스타일 재사용

export default function PortfolioCraip() {
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
          <span className="pf-nav-project">CRAIP</span>
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
          <span className="pf-hero-badge">University Course · Fall 2025</span>
          <h1 className="pf-hero-title">CRAIP</h1>
          <p className="pf-hero-subtitle">
            Creating Robot Artificial Intelligence Project<br />
            Unitree Go1 자율주행 및 임무 수행 시스템
          </p>
          <div className="pf-hero-stats">
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">6 Missions</span>
              <span className="pf-hero-stat-label">병원 환경 자율 임무</span>
            </div>
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">11 Pkg</span>
              <span className="pf-hero-stat-label">ROS 2 패키지 구성</span>
            </div>
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">NL → Action</span>
              <span className="pf-hero-stat-label">자연어 명령 제어</span>
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
                서울대학교 "Creating Robot Artificial Intelligence Project" 수업의 기말 프로젝트로,
                Unitree Go1 4족 보행 로봇에 자율주행과 AI 인지 능력을 부여합니다.
                Gazebo 시뮬레이션 병원 환경에서 자연어 명령만으로 6가지 임무를 수행해야 합니다.
              </p>
            </div>
            <div className="pf-overview-card">
              <h3>핵심 도전</h3>
              <p>
                Ground Truth 없이 센서만으로 위치를 추정하고(Particle Filter),
                카메라로 물체를 인식하며(YOLO), 충돌 없는 경로를 계획해야 합니다.
                모든 명령은 자연어로만 전달되어 LLM이 적절한 ROS 2 노드를 선택합니다.
              </p>
            </div>
          </div>

          {/* Missions */}
          <div className="pf-feature-list">
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--accent-primary)' }}>M1</div>
              <div>
                <strong>화장실로 자율주행</strong>
                <span>사전 탐색한 좌표로 경로 계획 → 도착 시 bark</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--accent-primary)' }}>M2</div>
              <div>
                <strong>먹을 수 있는 음식 탐색</strong>
                <span>YOLO로 Good/Bad food 분류 → 먹을 수 있는 음식 앞에서 bark</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--accent-primary)' }}>M3</div>
              <div>
                <strong>지정 색상 콘 찾기</strong>
                <span>빨강/초록/파랑 콘 중 지정 색상 인식 후 접근</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--accent-primary)' }}>M4</div>
              <div>
                <strong>박스 밀어서 목표 위치 이동</strong>
                <span>로봇 몸체로 배송 박스를 목표 영역까지 push</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--accent-primary)' }}>M5</div>
              <div>
                <strong>정지 표지판 없는 빈 방 진입</strong>
                <span>2개의 빈 방 중 정지 표지판이 없는 방 탐지 후 진입</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num" style={{ color: 'var(--accent-primary)' }}>M6</div>
              <div>
                <strong>간호사 주변 회전</strong>
                <span>휴게실의 간호사를 찾아 주변을 한 바퀴 회전</span>
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

          {/* Core modules pipeline */}
          <h3 className="pf-subsection-title">3대 핵심 모듈</h3>
          <div className="pf-pipeline">
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l1">L</div>
              <div className="pf-pipeline-info">
                <strong>Localization — Particle Filter</strong>
                <span>LiDAR + IMU + Map 기반 위치 추정. Ground Truth 없이 센서만으로 map→odom→base TF 발행. 가변 초기 위치 지원</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l2">P</div>
              <div className="pf-pipeline-info">
                <strong>Perception — YOLO Object Detection</strong>
                <span>RGB-D 카메라로 물체 탐지 + 깊이 추정. 음식 분류(Good/Bad), 색상 콘 식별, 정지 표지판 인식</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l3">T</div>
              <div className="pf-pipeline-info">
                <strong>Path Tracking — MPPI (C++)</strong>
                <span>Model Predictive Path Integral 알고리즘으로 실시간 경로 추종. /cmd_vel 퍼블리시로 로봇 이동 제어</span>
              </div>
            </div>
          </div>

          {/* Language command flow */}
          <h3 className="pf-subsection-title">자연어 명령 파이프라인</h3>
          <div className="pf-pipeline">
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l2">1</div>
              <div className="pf-pipeline-info">
                <strong>Language Command</strong>
                <span>"화장실로 가줘" → ROS 2 서비스 /language_command 호출</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l2">2</div>
              <div className="pf-pipeline-info">
                <strong>LLM Reasoning</strong>
                <span>OpenAI API가 프롬프트 + 실행 가능한 액션 목록을 분석하여 최적 액션 선택</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l3">3</div>
              <div className="pf-pipeline-info">
                <strong>Action Execution</strong>
                <span>선택된 ROS 2 노드/런치 파일 자동 실행. 이전 액션 자동 종료 → 새 액션 시작</span>
              </div>
            </div>
          </div>

          {/* Package overview */}
          <h3 className="pf-subsection-title">ROS 2 패키지 구성</h3>
          <div className="pf-arch-diagram">
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">go1_simulation</span>
                <span className="pf-arch-box-sub">URDF · Gazebo · 맵 생성 · 텔레오퍼레이션</span>
              </div>
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">environment</span>
                <span className="pf-arch-box-sub">Hospital World · 3D 모델</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↓</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">localization</span>
                <span className="pf-arch-box-sub">Particle Filter · TF 발행</span>
              </div>
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">perception</span>
                <span className="pf-arch-box-sub">YOLO · 깊이 추정</span>
              </div>
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">path_tracker</span>
                <span className="pf-arch-box-sub">MPPI (C++) · 경로 추종</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↓</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">language_command_handler</span>
                <span className="pf-arch-box-sub">OpenAI LLM · 액션 선택 · 노드 관리</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↓</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">unitree_guide2</span>
                <span className="pf-arch-box-sub">FSM 보행 제어 · 트로팅 · 밸런스</span>
              </div>
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">ros2_unitree_legged_controller</span>
                <span className="pf-arch-box-sub">관절 제어 · ros2_control 통합</span>
              </div>
            </div>
          </div>

          <div className="pf-note">
            <strong>센서 구성</strong> — Go1 로봇은 2D LiDAR, RGB-D 카메라(전방 + 상단), IMU를 탑재. Localization은 LiDAR + IMU, Perception은 상단 카메라 RGB + Depth를 활용합니다.
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
                <span className="pf-tech-tag">Gazebo Harmonic</span>
                <span className="pf-tech-tag">tf2</span>
                <span className="pf-tech-tag">ros2_control</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>AI / Perception</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">YOLO</span>
                <span className="pf-tech-tag">OpenAI API</span>
                <span className="pf-tech-tag">Particle Filter</span>
                <span className="pf-tech-tag">MPPI</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Programming</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">Python 3</span>
                <span className="pf-tech-tag">C++</span>
                <span className="pf-tech-tag">URDF / Xacro</span>
                <span className="pf-tech-tag">YAML</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Tools</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">colcon</span>
                <span className="pf-tech-tag">rosdep</span>
                <span className="pf-tech-tag">Docker</span>
                <span className="pf-tech-tag">Anaconda</span>
              </div>
            </div>
          </div>

          <h3 className="pf-subsection-title">설계 결정</h3>
          <div className="pf-decisions">
            <div className="pf-decision">
              <div className="pf-decision-q">왜 Particle Filter를 직접 구현?</div>
              <div className="pf-decision-a">
                Nav2의 AMCL 등 기존 패키지 사용이 금지되어 있어, LiDAR scan matching + IMU motion prediction을
                결합한 Monte Carlo Localization을 직접 구현했습니다. 가변 초기 위치도 지원합니다.
              </div>
            </div>
            <div className="pf-decision">
              <div className="pf-decision-q">왜 MPPI를 C++로?</div>
              <div className="pf-decision-a">
                실시간 경로 추종에서 수천 개의 샘플 궤적을 병렬 평가해야 하므로, Python 대비
                수십 배 빠른 C++ 구현으로 제어 주기(10Hz+)를 확보했습니다.
              </div>
            </div>
            <div className="pf-decision">
              <div className="pf-decision-q">왜 LLM 기반 명령 처리?</div>
              <div className="pf-decision-a">
                대회에서 명령어가 변형될 수 있어("화장실 가줘" → "Toilet, toilet, hurry!") 키워드 매칭으로는
                대응 불가합니다. LLM이 의도를 파악하고 적절한 ROS 2 노드를 선택하도록 설계했습니다.
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
              <div className="pf-result-num">6</div>
              <div className="pf-result-desc">자율 임무</div>
              <div className="pf-result-detail">주행 · 탐색 · 인식 · 물리 조작</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">11</div>
              <div className="pf-result-desc">ROS 2 패키지</div>
              <div className="pf-result-detail">시뮬레이션 + 인지 + 제어 + LLM</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">0</div>
              <div className="pf-result-desc">Ground Truth 의존</div>
              <div className="pf-result-detail">센서 기반 위치 추정만 사용</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">NL</div>
              <div className="pf-result-desc">자연어 제어</div>
              <div className="pf-result-detail">LLM으로 명령 → 액션 자동 매핑</div>
            </div>
          </div>

          <h3 className="pf-subsection-title">모듈별 구현 현황</h3>
          <table className="pf-compare-table">
            <thead>
              <tr><th>모듈</th><th>항목</th><th>상태</th></tr>
            </thead>
            <tbody>
              <tr>
                <td rowSpan={3}>Localization</td>
                <td>Particle Filter (LiDAR + IMU)</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>map → odom → base TF 발행</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>가변 초기 위치 지원</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td rowSpan={3}>Perception</td>
                <td>YOLO 물체 탐지 + 바운딩 박스</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>Depth 기반 거리 추정</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>Center region bark 판정</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td rowSpan={2}>Path Tracking</td>
                <td>MPPI 알고리즘 (C++)</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>실시간 /cmd_vel 제어</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td rowSpan={2}>Language Handler</td>
                <td>OpenAI LLM 연동</td>
                <td className="pf-after">완료</td>
              </tr>
              <tr>
                <td>자동 노드 관리 (시작/종료)</td>
                <td className="pf-after">완료</td>
              </tr>
            </tbody>
          </table>

          <div className="pf-note" style={{ marginTop: '2rem' }}>
            <strong>GitHub</strong> — <a href="https://github.com/jm020827/robot_ai_01" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-primary)' }}>github.com/jm020827/robot_ai_01</a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="pf-footer">
        <div className="pf-footer-inner">
          <div className="pf-footer-name">Kangjun</div>
          <div className="pf-footer-project">CRAIP · 2025</div>
          <Link to="/portfolio" className="pf-footer-link">← All Projects</Link>
        </div>
      </footer>
    </div>
  )
}
