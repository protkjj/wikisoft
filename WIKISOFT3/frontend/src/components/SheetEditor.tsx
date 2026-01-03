import { useState, useEffect, useRef } from 'react'
import './SheetEditor.css'
import { AGENT_CHAT_URL } from '../config/api'

// 에러/경고 항목
interface ValidationItem {
  severity: 'error' | 'warning'
  message: string
  row?: number
  field?: string
  emp_info?: string
}

interface SheetEditorProps {
  isOpen: boolean
  onClose: () => void
  data: string[][]  // 2D 배열 (헤더 + 데이터)
  targetRow?: number  // 하이라이트할 행 (0-indexed, 헤더 제외)
  targetField?: string  // 하이라이트할 필드명
  errorMessage?: string  // 에러 메시지 (AI 컨텍스트용)
  allErrors?: ValidationItem[]  // 모든 에러/경고 목록
  onSave?: (data: string[][]) => void
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function SheetEditor({ 
  isOpen, 
  onClose, 
  data: initialData, 
  targetRow,
  targetField,
  errorMessage,
  allErrors = [],
  onSave 
}: SheetEditorProps) {
  const [sheetData, setSheetData] = useState<string[][]>([])
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null)
  const [editValue, setEditValue] = useState('')
  const [highlightRow, setHighlightRow] = useState<number | undefined>(targetRow)
  const [highlightCol, setHighlightCol] = useState<number>(-1)
  const [pendingEdits, setPendingEdits] = useState<Array<{row: number, col: number, value: string}>>([])
  
  // AI 챗봇 상태
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const tableRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (initialData && initialData.length > 0) {
      // 행 번호 컬럼 추가
      const withRowNumbers = initialData.map((row, idx) => {
        if (idx === 0) return ['', ...row]  // 헤더 행
        return [String(idx), ...row]  // 데이터 행
      })
      setSheetData(withRowNumbers)
    }
  }, [initialData])

  // 모달 열릴 때 초기 메시지
  useEffect(() => {
    if (isOpen) {
      setPendingEdits([])
      setHighlightRow(targetRow)
      
      if (allErrors && allErrors.length > 0) {
        // 모든 에러/경고 목록 표시
        const errorList = allErrors.map((e, i) => 
          `${i + 1}. ${e.severity === 'error' ? '🔴' : '🟠'} ${e.message}`
        ).join('\n')
        
        setMessages([{
          role: 'assistant',
          content: `📋 **수정이 필요한 ${allErrors.length}건**\n\n${errorList}\n\n---\n💡 항목을 클릭하면 해당 셀로 이동해요.\n💬 "N번 이거로 수정해줘" 라고 말해보세요!`
        }])
      } else if (errorMessage) {
        setMessages([{
          role: 'assistant',
          content: `이 문제를 해결해 드릴게요:\n\n📌 **${errorMessage}**\n\n어떻게 수정하면 좋을지 물어보세요!`
        }])
      } else {
        setMessages([{
          role: 'assistant',
          content: '데이터 수정을 도와드릴게요. 궁금한 점이 있으면 물어보세요!'
        }])
      }
    }
  }, [isOpen, errorMessage, allErrors, targetRow])

  // 메시지 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!isOpen) return null

  const headers = sheetData[0] || []

  // 열 번호를 엑셀 열 문자로 변환 (1=A, 2=B, ... 27=AA)
  const getColumnLetter = (colIdx: number): string => {
    let letter = ''
    let num = colIdx
    while (num > 0) {
      const remainder = (num - 1) % 26
      letter = String.fromCharCode(65 + remainder) + letter
      num = Math.floor((num - 1) / 26)
    }
    return letter || 'A'
  }

  // 셀 주소 생성 (예: B5, C10)
  const getCellAddress = (rowIdx: number, colIdx: number): string => {
    return `${getColumnLetter(colIdx)}${rowIdx}`
  }

  const handleCellClick = (rowIdx: number, colIdx: number) => {
    if (rowIdx === 0 || colIdx === 0) return  // 헤더나 행번호는 편집 불가
    setSelectedCell({ row: rowIdx, col: colIdx })
    setEditValue(sheetData[rowIdx]?.[colIdx] || '')
  }

  const handleCellChange = (value: string) => {
    setEditValue(value)
    if (selectedCell) {
      const newData = [...sheetData]
      newData[selectedCell.row] = [...newData[selectedCell.row]]
      newData[selectedCell.row][selectedCell.col] = value
      setSheetData(newData)
    }
  }

  const handleSave = () => {
    if (onSave) {
      // 행 번호 컬럼 제거하고 반환
      const dataWithoutRowNumbers = sheetData.map((row) => row.slice(1))
      onSave(dataWithoutRowNumbers)
    }
    onClose()
  }

  const isTargetCell = (rowIdx: number, colIdx: number) => {
    // highlightRow는 sheetData 기준 (1부터 시작, 0은 헤더)
    return rowIdx === highlightRow && colIdx === highlightCol
  }

  // 에러 항목 클릭 시 해당 셀로 이동
  const handleErrorClick = (item: ValidationItem) => {
    if (item.row !== undefined && item.field) {
      // headers[0]은 빈 문자열(행번호 열), headers[1]부터가 실제 필드
      // item.field가 실제 필드명이므로 headers에서 찾으면 됨
      const colIdx = headers.indexOf(item.field)

      if (colIdx !== -1) {
        // API row는 1-indexed (헤더 포함)
        // sheetData도 행번호가 1부터 시작 (row 1 = sheetData[1])
        // 따라서 API row - 1 = sheetData 인덱스
        const dataRowIdx = item.row - 1

        setHighlightRow(dataRowIdx)
        setHighlightCol(colIdx)

        // 스크롤 (thead 때문에 +1이 아니라 tbody 내에서 찾아야 함)
        setTimeout(() => {
          const rowElement = tableRef.current?.querySelector(`tbody tr:nth-child(${dataRowIdx + 1})`)
          rowElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }, 100)
      }
    }
  }

  // AI 응답에서 수정 명령 파싱 및 적용
  const applyEditCommands = (response: string) => {
    // 형식: [EDIT:행번호:필드명:새값] 또는 [수정:행번호:필드명:새값]
    const editPattern = /\[(?:EDIT|수정):(\d+):([^:]+):([^\]]+)\]/gi
    const edits: Array<{row: number, col: number, value: string, field: string, cellAddress: string}> = []
    let match
    
    while ((match = editPattern.exec(response)) !== null) {
      const rowNum = parseInt(match[1])
      const fieldName = match[2].trim()
      const newValue = match[3].trim()
      
      const colIdx = headers.indexOf(fieldName)
      if (colIdx !== -1 && rowNum > 0 && rowNum < sheetData.length) {
        const cellAddress = getCellAddress(rowNum, colIdx)
        edits.push({ row: rowNum, col: colIdx, value: newValue, field: fieldName, cellAddress })
      }
    }
    
    if (edits.length > 0) {
      // 수정 적용
      const newData = [...sheetData]
      edits.forEach(edit => {
        newData[edit.row] = [...newData[edit.row]]
        newData[edit.row][edit.col] = edit.value
      })
      setSheetData(newData)
      setPendingEdits(prev => [...prev, ...edits.map(e => ({...e}))])
      
      // 첫 번째 수정된 셀로 스크롤
      if (edits.length > 0) {
        setHighlightRow(edits[0].row - 1)
        setHighlightCol(edits[0].col)
        const rowElement = tableRef.current?.querySelector(`tr:nth-child(${edits[0].row + 1})`)
        rowElement?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
      
      return edits
    }
    return []
  }

  // AI 채팅 전송
  const handleChatSend = async () => {
    if (!chatInput.trim() || isThinking) return
    
    const userMessage = chatInput.trim()
    setChatInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setIsThinking(true)

    try {
      // 현재 선택된 셀 정보
      const cellInfo = selectedCell 
        ? `현재 선택된 셀: ${headers[selectedCell.col]} 컬럼, ${selectedCell.row}행, 값: "${sheetData[selectedCell.row]?.[selectedCell.col]}"`
        : '선택된 셀 없음'
      
      // 에러 목록 컨텍스트
      // 에러 목록 컨텍스트 (행 번호와 필드명 명확하게)
      const errorListContext = allErrors.length > 0 
        ? `\n\n=== 에러/경고 목록 ("N번"은 아래 N번째 항목을 의미) ===\n${allErrors.map((e, i) => 
            `${i + 1}번: 행번호=${e.row}, 필드명="${e.field}", 에러내용="${e.message}"`
          ).join('\n')}`
        : ''
      
      const context = `
당신은 HR 데이터 검증 시스템의 AI 어시스턴트입니다.
사용자가 "N번"이라고 하면, 아래 에러 목록의 N번째 항목을 의미합니다.
${cellInfo}
${errorListContext}

[필수 규칙]
1. "수정해줘", "바꾸줘" 등 요청 시 반드시 아래 형식으로 응답:
   [수정:행번호:필드명:새값]

2. 예시:
   - "1번 2024년 1월 1일로 수정해줘" → 1번 항목의 행번호와 필드명을 찾아서 [수정:15:입사일자:20240101]
   - "2번 206만원으로 바꾸줘" → 2번 항목의 행번호와 필드명을 찾아서 [수정:3:기준급여:2060740]

3. 날짜는 YYYYMMDD 형식 (2024년 1월 1일 → 20240101)
4. 금액은 숫자만 (206만원 → 2060000)
5. 사용자가 "N번"이라고 하면 에러 목록에서 N번째 항목의 행번호와 필드명을 사용하세요!
      `.trim()

      const response = await fetch(AGENT_CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          context: context
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        const aiResponse = data.response || '답변을 생성하지 못했습니다.'
        
        // 수정 명령 파싱 및 적용
        const edits = applyEditCommands(aiResponse)
        
        // 수정 결과를 메시지에 추가 (셀 주소 포함)
        let displayResponse = aiResponse.replace(/\[(?:EDIT|수정):[^\]]+\]/gi, '').trim()
        if (edits.length > 0) {
          displayResponse += `\n\n✅ **${edits.length}건 수정 완료:**\n${edits.map(e => 
            `• 📍 **${e.cellAddress}** (${e.field}) → "${e.value}"`
          ).join('\n')}`
        }
        
        setMessages(prev => [...prev, { role: 'assistant', content: displayResponse }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: '서버 오류가 발생했습니다.' }])
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: '네트워크 오류가 발생했습니다.' }])
    } finally {
      setIsThinking(false)
    }
  }

  // 빠른 질문 버튼
  const quickQuestions = [
    { label: '📝 올바른 값은?', question: '이 필드의 올바른 값을 알려주세요. 수정해주세요.' },
    { label: '🔧 전체 수정', question: '모든 에러를 올바른 값으로 수정해주세요.' },
    { label: '❓ 왜 오류야?', question: '왜 이 값이 오류로 표시되나요?' },
  ]

  return (
    <div className="sheet-editor-overlay" onClick={onClose}>
      <div className="sheet-editor-modal with-chat" onClick={e => e.stopPropagation()}>
        {/* 왼쪽: 스프레드시트 */}
        <div className="sheet-editor-left">
          {/* 헤더 */}
          <div className="sheet-editor-header">
            <h2>📊 데이터 수정</h2>
            {pendingEdits.length > 0 && (
              <span className="edit-badge">✏️ {pendingEdits.length}건 수정됨</span>
            )}
          </div>

          {/* 에러 목록 (전체 수정 모드일 때) */}
          {allErrors.length > 0 && (
            <div className="error-list-panel">
              <div className="error-list-header">
                📋 수정 필요 항목 ({allErrors.length}건)
              </div>
              <div className="error-list-items">
                {allErrors.map((item, idx) => (
                  <div 
                    key={idx} 
                    className={`error-list-item ${item.severity} ${highlightRow === (item.row ? item.row - 1 : -1) ? 'active' : ''}`}
                    onClick={() => handleErrorClick(item)}
                  >
                    <span className="error-num">{idx + 1}</span>
                    <span className="error-icon">{item.severity === 'error' ? '🔴' : '🟠'}</span>
                    <span className="error-text">
                      {item.emp_info || `행${item.row}`}: {item.field}
                      {item.row && <span className="error-row-num">(행 {item.row - 1})</span>}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 안내 메시지 (단일 수정 모드일 때) */}
          {!allErrors.length && targetField && (
            <div className="sheet-editor-info">
              💡 <strong>{targetField}</strong> 필드를 수정하세요. 
              {targetRow !== undefined && ` (${targetRow + 1}행 하이라이트)`}
            </div>
          )}

          {/* 스프레드시트 */}
          <div className="sheet-editor-table-wrapper" ref={tableRef}>
            <table className="sheet-editor-table">
              {/* 열 문자 헤더 (A, B, C, ...) */}
              <thead>
                <tr className="column-letters-row">
                  <th className="column-letter"></th>
                  {headers.slice(1).map((_, idx) => (
                    <th key={idx} className="column-letter">{getColumnLetter(idx + 1)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sheetData.slice(0, 50).map((row, rowIdx) => (
                  <tr key={rowIdx} className={highlightRow !== undefined && rowIdx === highlightRow + 1 ? 'highlight-row' : ''}>
                    {row.map((cell, colIdx) => {
                      const isHeader = rowIdx === 0 || colIdx === 0
                      const isSelected = selectedCell?.row === rowIdx && selectedCell?.col === colIdx
                      const isTarget = isTargetCell(rowIdx, colIdx)
                      const isEdited = pendingEdits.some(e => e.row === rowIdx && e.col === colIdx)
                      const cellAddr = colIdx > 0 && rowIdx > 0 ? getCellAddress(rowIdx, colIdx) : ''
                      
                      return (
                        <td
                          key={`${rowIdx}-${colIdx}`}
                          className={`
                            sheet-cell 
                            ${isHeader ? 'header-cell' : ''} 
                            ${isSelected ? 'selected-cell' : ''} 
                            ${isTarget ? 'target-cell' : ''}
                            ${isEdited ? 'edited-cell' : ''}
                          `}
                          onClick={() => handleCellClick(rowIdx, colIdx)}
                          title={cellAddr ? `셀 ${cellAddr}` : undefined}
                          style={{ 
                            minWidth: colIdx === 0 ? '40px' : '120px',
                            maxWidth: colIdx === 0 ? '40px' : '200px',
                          }}
                        >
                          {isEdited && <span className="edit-indicator">✓</span>}
                          {isSelected && !isHeader ? (
                            <input
                              type="text"
                              value={editValue}
                              onChange={(e) => handleCellChange(e.target.value)}
                              autoFocus
                              className="cell-input"
                              onBlur={() => setSelectedCell(null)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === 'Tab') {
                                  setSelectedCell(null)
                                }
                              }}
                            />
                          ) : (
                            <div className="cell-content" title={String(cell)}>
                              {String(cell)}
                            </div>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            {sheetData.length > 50 && (
              <div className="more-rows-info">
                ... 외 {sheetData.length - 50}개 행
              </div>
            )}
          </div>

          {/* 액션 버튼 */}
          <div className="sheet-editor-actions">
            <button className="btn-secondary" onClick={onClose}>
              취소
            </button>
            <button className="btn-primary" onClick={handleSave}>
              💾 저장
            </button>
          </div>
        </div>

        {/* 오른쪽: AI 챗봇 */}
        <div className="sheet-editor-chat">
          <div className="chat-header">
            <span>✨ AI 어시스턴트</span>
            <button className="close-btn-small" onClick={onClose}>✕</button>
          </div>
          
          {/* 메시지 영역 */}
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                <div className="message-bubble">
                  {msg.content.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>
            ))}
            {isThinking && (
              <div className="chat-message assistant">
                <div className="message-bubble thinking">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 빠른 질문 */}
          <div className="quick-questions">
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                className="quick-btn"
                onClick={() => {
                  setChatInput(q.question)
                }}
              >
                {q.label}
              </button>
            ))}
          </div>

          {/* 입력 영역 */}
          <div className="chat-input-area">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleChatSend()}
              placeholder="질문을 입력하세요..."
              className="chat-input"
            />
            <button 
              className="send-btn"
              onClick={handleChatSend}
              disabled={!chatInput.trim() || isThinking}
            >
              ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
