import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import './PortfolioOneCheck.css'

export default function PortfolioPage() {
  const [navOpen, setNavOpen] = useState(false)

  // Scroll-triggered animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          }
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
          <span className="pf-nav-project">OneCheck</span>
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
          <Link to="/login" className="pf-demo-btn" onClick={() => setNavOpen(false)}>
            Live Demo
          </Link>
        </div>
      </nav>

      {/* ===== Hero ===== */}
      <section className="pf-hero">
        <div className="pf-hero-inner">
          <span className="pf-hero-badge">Personal Project</span>
          <h1 className="pf-hero-title">OneCheck</h1>
          <p className="pf-hero-subtitle">
            퇴직급여채무 명부 검증을 자동화하는<br />
            AI 기반 웹 플랫폼
          </p>
          <div className="pf-hero-stats">
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">3h → 5min</span>
              <span className="pf-hero-stat-label">검증 시간 단축</span>
            </div>
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">21개</span>
              <span className="pf-hero-stat-label">자동화된 검증 규칙</span>
            </div>
            <div className="pf-hero-stat">
              <span className="pf-hero-stat-num">96%</span>
              <span className="pf-hero-stat-label">오류 자동 억제율</span>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Project Overview ===== */}
      <section id="overview" className="pf-section pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">PROJECT OVERVIEW</div>
          <h2 className="pf-section-title">프로젝트 소개</h2>

          <div className="pf-overview-grid">
            <div className="pf-overview-card">
              <h3>배경</h3>
              <p>
                퇴직급여채무 계리평가에서 사원명부 검증은 필수 업무입니다.
                기존에는 담당자가 Excel 매크로로 수동 검증하며, 파일당 <strong>3~4시간</strong>이 소요되었습니다.
                이메일로 파일을 주고받으며 개인정보(주민번호) 노출 위험도 존재했습니다.
              </p>
            </div>
            <div className="pf-overview-card">
              <h3>해결</h3>
              <p>
                웹에서 파일을 업로드하면 <strong>규칙 기반 + AI 하이브리드 검증</strong>을 자동 수행합니다.
                검증 결과를 인라인으로 수정할 수 있고, 사용자 피드백으로 시스템이 학습하여
                반복 사용할수록 정확도가 향상됩니다.
              </p>
            </div>
          </div>

          {/* 핵심 기능 요약 */}
          <div className="pf-feature-list">
            <div className="pf-feature-item">
              <div className="pf-feature-num">01</div>
              <div>
                <strong>진단 질문 위자드</strong>
                <span>7섹션 74개 질문으로 퇴직연금 제도 정보를 체계적으로 수집</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num">02</div>
              <div>
                <strong>AI 헤더 매칭</strong>
                <span>GPT-4o Few-shot 학습 기반으로 다양한 Excel 컬럼명을 표준 필드에 자동 매핑</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num">03</div>
              <div>
                <strong>3-Layer 검증 엔진</strong>
                <span>형식 검증 → 교차 검증 → AI 검증을 파이프라인으로 실행</span>
              </div>
            </div>
            <div className="pf-feature-item">
              <div className="pf-feature-num">04</div>
              <div>
                <strong>인라인 수정 + 학습</strong>
                <span>웹 에디터에서 직접 수정하고, "값 유지" 피드백으로 false positive 자동 억제</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Architecture ===== */}
      <section id="architecture" className="pf-section pf-section-alt pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">ARCHITECTURE</div>
          <h2 className="pf-section-title">시스템 아키텍처</h2>

          {/* System Diagram */}
          <div className="pf-arch-diagram">
            <div className="pf-arch-row">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">Frontend</span>
                <span className="pf-arch-box-sub">React 18 + TypeScript + Vite</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↓ <span>REST API</span></div>
            <div className="pf-arch-row">
              <div className="pf-arch-box pf-arch-highlight">
                <span className="pf-arch-box-label">Backend</span>
                <span className="pf-arch-box-sub">FastAPI + Python 3.11</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↓</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">Parser</span>
                <span className="pf-arch-box-sub">Excel 파싱 + 헤더 탐지</span>
              </div>
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">AI Matcher</span>
                <span className="pf-arch-box-sub">GPT-4o Few-shot</span>
              </div>
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">Validator</span>
                <span className="pf-arch-box-sub">3-Layer Engine</span>
              </div>
              <div className="pf-arch-box">
                <span className="pf-arch-box-label">Report</span>
                <span className="pf-arch-box-sub">Excel 생성</span>
              </div>
            </div>
            <div className="pf-arch-arrow">↓</div>
            <div className="pf-arch-row pf-arch-row-multi">
              <div className="pf-arch-box pf-arch-muted">
                <span className="pf-arch-box-label">SQLite</span>
              </div>
              <div className="pf-arch-box pf-arch-muted">
                <span className="pf-arch-box-label">OpenAI API</span>
              </div>
              <div className="pf-arch-box pf-arch-muted">
                <span className="pf-arch-box-label">Telegram</span>
              </div>
            </div>
          </div>

          {/* 3-Layer Pipeline */}
          <h3 className="pf-subsection-title">3-Layer Validation Pipeline</h3>
          <div className="pf-pipeline">
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l1">L1</div>
              <div className="pf-pipeline-info">
                <strong>Format Validation</strong>
                <span>21개 규칙 기반 형식 검증 — 날짜, 숫자 범위, 필수값, 중복 탐지 (0.1s)</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l2">L2</div>
              <div className="pf-pipeline-info">
                <strong>Cross Validation</strong>
                <span>진단 질문 답변과 명부 데이터 교차 비교 — 인원수, 급여 총액 대조 (0.5s)</span>
              </div>
            </div>
            <div className="pf-pipeline-connector" />
            <div className="pf-pipeline-step">
              <div className="pf-pipeline-badge l3">L3</div>
              <div className="pf-pipeline-info">
                <strong>AI Validation</strong>
                <span>GPT-4o 기반 컨텍스트 추론 — 규칙으로 잡기 어려운 비즈니스 로직 검증 (3~5s)</span>
              </div>
            </div>
          </div>

          {/* Graceful Degradation note */}
          <div className="pf-note">
            <strong>Graceful Degradation</strong> — OpenAI API가 없어도 L1+L2 규칙 기반으로 100% 동작합니다. AI는 "필수"가 아닌 "향상" 수단으로 설계했습니다.
          </div>
        </div>
      </section>

      {/* ===== Tech Stack ===== */}
      <section id="tech" className="pf-section pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">TECH STACK</div>
          <h2 className="pf-section-title">사용 기술</h2>

          <div className="pf-tech-categories">
            <div className="pf-tech-category">
              <h4>Frontend</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">React 18</span>
                <span className="pf-tech-tag">TypeScript</span>
                <span className="pf-tech-tag">Vite</span>
                <span className="pf-tech-tag">React Router v7</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Backend</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">FastAPI</span>
                <span className="pf-tech-tag">Python 3.11</span>
                <span className="pf-tech-tag">Pandas</span>
                <span className="pf-tech-tag">OpenPyXL</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>AI / ML</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">GPT-4o</span>
                <span className="pf-tech-tag">Few-shot Learning</span>
                <span className="pf-tech-tag">Pattern Matching</span>
              </div>
            </div>
            <div className="pf-tech-category">
              <h4>Database & Infra</h4>
              <div className="pf-tech-tags">
                <span className="pf-tech-tag">SQLite</span>
                <span className="pf-tech-tag">JWT + RBAC</span>
                <span className="pf-tech-tag">AES-256-GCM</span>
                <span className="pf-tech-tag">Telegram Bot</span>
              </div>
            </div>
          </div>

          {/* Key Design Decisions */}
          <h3 className="pf-subsection-title">설계 결정</h3>
          <div className="pf-decisions">
            <div className="pf-decision">
              <div className="pf-decision-q">왜 하이브리드 (규칙 + AI)?</div>
              <div className="pf-decision-a">
                규칙만으로는 컨텍스트 판단이 불가능하고, AI만으로는 비용이 높고 결과 예측이 어렵습니다.
                확정적 규칙으로 기본을 보장하고, AI로 복잡한 판단을 보완하는 방식을 선택했습니다.
              </div>
            </div>
            <div className="pf-decision">
              <div className="pf-decision-q">왜 PII-free 설계?</div>
              <div className="pf-decision-a">
                보안은 사후 조치가 아닌 설계 원칙입니다. 개인정보가 필요 없는 검증 플로우를 설계하여
                근본적으로 유출 위험을 제거했습니다.
              </div>
            </div>
            <div className="pf-decision">
              <div className="pf-decision-q">왜 사용자 피드백 학습?</div>
              <div className="pf-decision-a">
                도메인 특성상 동일 패턴의 false positive가 반복됩니다.
                사용자가 "값 유지"를 선택하면 해당 패턴을 학습하여 다음 검증에서 자동 억제합니다.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== Results ===== */}
      <section id="results" className="pf-section pf-section-alt pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">RESULTS</div>
          <h2 className="pf-section-title">성과</h2>

          <div className="pf-results-grid">
            <div className="pf-result-card">
              <div className="pf-result-num">40x</div>
              <div className="pf-result-desc">검증 속도 향상</div>
              <div className="pf-result-detail">3~4시간 → 5분</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">97 → 4</div>
              <div className="pf-result-desc">AI 학습 후 오류</div>
              <div className="pf-result-detail">93건 false positive 자동 억제</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">21/21</div>
              <div className="pf-result-desc">매크로 규칙 호환</div>
              <div className="pf-result-detail">기존 매크로 100% 대체</div>
            </div>
            <div className="pf-result-card">
              <div className="pf-result-num">74</div>
              <div className="pf-result-desc">진단 질문</div>
              <div className="pf-result-detail">7섹션 체계적 데이터 수집</div>
            </div>
          </div>

          {/* Before / After */}
          <h3 className="pf-subsection-title">Before / After</h3>
          <table className="pf-compare-table">
            <thead>
              <tr><th>항목</th><th>Before (수작업)</th><th>After (OneCheck)</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>검증 소요시간</td>
                <td className="pf-before">3~4시간</td>
                <td className="pf-after">5분</td>
              </tr>
              <tr>
                <td>컬럼 매핑</td>
                <td className="pf-before">수동 확인</td>
                <td className="pf-after">AI 자동 매핑</td>
              </tr>
              <tr>
                <td>오류 수정</td>
                <td className="pf-before">Excel 수동 편집 → 재전송</td>
                <td className="pf-after">웹 에디터 인라인 수정</td>
              </tr>
              <tr>
                <td>학습</td>
                <td className="pf-before">불가능</td>
                <td className="pf-after">사용자 피드백 자동 학습</td>
              </tr>
              <tr>
                <td>보안</td>
                <td className="pf-before">이메일 파일 첨부</td>
                <td className="pf-after">JWT + PII-free 설계</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ===== Development Process ===== */}
      <section className="pf-section pf-animate">
        <div className="pf-section-inner">
          <div className="pf-section-label">DEVELOPMENT</div>
          <h2 className="pf-section-title">개발 과정</h2>

          <div className="pf-timeline">
            {[
              { ver: 'v1', title: '문제 분석 + 파서 구현', desc: '기존 매크로 21개 규칙 역공학, Excel 파서 개발' },
              { ver: 'v2', title: 'AI 매칭 + 검증 엔진', desc: 'GPT-4o Few-shot 헤더 매칭, 3-Layer 검증 파이프라인 구현' },
              { ver: 'v3', title: '에이전트 + 학습 시스템', desc: 'ReACT 패턴 에이전트, 사용자 피드백 기반 false positive 학습' },
              { ver: 'v4', title: '보안 + 플랫폼 완성', desc: 'JWT/RBAC 인증, PII 탐지, SQLite 영속화, Telegram 알림 연동' },
            ].map((item) => (
              <div key={item.ver} className="pf-timeline-item">
                <div className="pf-timeline-ver">{item.ver}</div>
                <div className="pf-timeline-content">
                  <strong>{item.title}</strong>
                  <span>{item.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== Footer ===== */}
      <footer className="pf-footer">
        <div className="pf-footer-inner">
          <div className="pf-footer-name">Kangjun</div>
          <div className="pf-footer-project">OneCheck v4.1.0 · February 2026</div>
          <Link to="/login" className="pf-footer-link">Live Demo →</Link>
        </div>
      </footer>
    </div>
  )
}
