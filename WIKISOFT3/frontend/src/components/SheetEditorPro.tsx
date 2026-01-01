import { useState, useRef, useEffect, useCallback } from 'react'
import './SheetEditorPro.css'

// 에러/경고 항목
interface ValidationItem {
  severity: 'error' | 'warning'
  message: string
  row?: number
  field?: string
  emp_info?: string
}

interface SheetEditorProProps {
  isOpen: boolean
  onClose: () => void
  data: string[][]
  targetRow?: number
  targetField?: string
  errorMessage?: string
  allErrors?: ValidationItem[]
  onSave?: (data: string[][]) => void
  onRevalidate?: (data: string[][]) => Promise<ValidationItem[]>
  filename?: string  // 원본 파일명
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  cellRef?: string
}

export default function SheetEditorPro({
  isOpen,
  onClose,
  data: initialData,
  targetRow,
  targetField,
  errorMessage,
  allErrors = [],
  onSave,
  onRevalidate,
  filename = 'export.xlsx'
}: SheetEditorProProps) {
  // Sheet data
  const [sheetData, setSheetData] = useState<string[][]>([])
  const [pendingEdits, setPendingEdits] = useState<Array<{row: number, col: number, value: string, field: string}>>([])
  const [currentErrors, setCurrentErrors] = useState<ValidationItem[]>([])
  const [isRevalidating, setIsRevalidating] = useState(false)
  
  // Selection state
  const [selection, setSelection] = useState<{
    start: { row: number; col: number } | null
    end: { row: number; col: number } | null
    isSelecting: boolean
  }>({ start: null, end: null, isSelecting: false })
  const [activeCell, setActiveCell] = useState<{ row: number; col: number } | null>(null)
  const [editValue, setEditValue] = useState('')
  
  // AI Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const tableRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Resizer state
  const [sidebarWidth, setSidebarWidth] = useState(400)
  const [isResizing, setIsResizing] = useState(false)
  const minSidebarWidth = 320
  const maxSidebarWidth = 550

  // 초기화
  useEffect(() => {
    if (initialData && initialData.length > 0) {
      // 컬럼 수 계산
      const colCount = initialData[0].length + 1  // +1 for row number column
      
      // 컬럼 레터 생성 함수 (인라인)
      const toColLetter = (col: number): string => {
        let result = ''
        let n = col
        while (n > 0) {
          n--
          result = String.fromCharCode(65 + (n % 26)) + result
          n = Math.floor(n / 26)
        }
        return result
      }
      
      // 0행: 컬럼 레이블 (빈칸, A, B, C, D...)
      const columnLabels = ['', ...Array.from({ length: colCount - 1 }, (_, i) => toColLetter(i + 1))]
      
      // 1행: 헤더 (행번호 칸, 사원번호, 성명...)
      const headers = ['', ...initialData[0]]
      
      // 2행~: 데이터 (행번호, 데이터...)
      const dataWithRowNumbers = initialData.slice(1).map((row, idx) => [String(idx + 2), ...row])
      
      setSheetData([columnLabels, headers, ...dataWithRowNumbers])
    }
  }, [initialData])

  // 모달 열릴 때 초기 메시지
  useEffect(() => {
    if (isOpen) {
      setPendingEdits([])
      
      // 개별 수정 모드 (특정 에러 하나)
      if (targetRow !== undefined && targetField && errorMessage) {
        setMessages([{
          role: 'assistant',
          content: `📍 **${targetField}** 필드 (${targetRow}행) 수정을 도와드릴게요.\n\n📌 문제: ${errorMessage}\n\n수정할 값을 말씀해 주세요! 예: "2024년 1월 1일로 변경해줘"`,
          timestamp: new Date()
        }])
        
        // 해당 셀 선택
        const headers = sheetData[0] || []
        const colIdx = headers.indexOf(targetField)
        if (colIdx !== -1) {
          setSelection({
            start: { row: targetRow, col: colIdx },
            end: { row: targetRow, col: colIdx },
            isSelecting: false
          })
        }
      }
      // 전체 수정 모드 (에러 목록)
      else if (allErrors && allErrors.length > 0) {
        const errorList = allErrors.map((e, i) => 
          `${i + 1}. ${e.severity === 'error' ? '🔴' : '🟠'} ${e.emp_info || `행${e.row}`}: ${e.field}`
        ).join('\n')
        
        setMessages([{
          role: 'assistant',
          content: `📋 **수정이 필요한 ${allErrors.length}건**\n\n${errorList}\n\n---\n💡 왼쪽에서 셀을 선택하거나, "N번 OOO으로 수정해줘"라고 말해보세요!`,
          timestamp: new Date()
        }])
      }
      else {
        setMessages([{
          role: 'assistant',
          content: '안녕하세요! 데이터 수정을 도와드리겠습니다.\n\n셀을 선택하고 수정할 내용을 말씀해 주세요.',
          timestamp: new Date()
        }])
      }
    }
  }, [isOpen, targetRow, targetField, errorMessage, allErrors])

  // 메시지 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 리사이저 핸들러
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
  }, [])

  const handleResizeMove = useCallback((e: MouseEvent) => {
    if (!isResizing || !containerRef.current) return
    const containerRect = containerRef.current.getBoundingClientRect()
    const newWidth = containerRect.right - e.clientX
    if (newWidth >= minSidebarWidth && newWidth <= maxSidebarWidth) {
      setSidebarWidth(newWidth)
    }
  }, [isResizing])

  const handleResizeEnd = useCallback(() => {
    setIsResizing(false)
  }, [])

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove)
      document.addEventListener('mouseup', handleResizeEnd)
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
    } else {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    return () => {
      document.removeEventListener('mousemove', handleResizeMove)
      document.removeEventListener('mouseup', handleResizeEnd)
    }
  }, [isResizing, handleResizeMove, handleResizeEnd])

  if (!isOpen) return null

  const headers = sheetData[0] || []

  // 열 문자 변환
  const getColumnLetter = (colIdx: number): string => {
    let letter = ''
    let num = colIdx
    while (num > 0) {
      const remainder = (num - 1) % 26
      letter = String.fromCharCode(65 + remainder) + letter
      num = Math.floor((num - 1) / 26)
    }
    return letter || ''
  }

  // 셀 주소
  const getCellAddress = (row: number, col: number): string => {
    return `${getColumnLetter(col)}${row}`
  }

  // 선택 범위 문자열
  const getSelectionRangeString = (): string => {
    if (!selection.start) return ''
    const end = selection.end || selection.start
    const minRow = Math.min(selection.start.row, end.row)
    const maxRow = Math.max(selection.start.row, end.row)
    const minCol = Math.min(selection.start.col, end.col)
    const maxCol = Math.max(selection.start.col, end.col)
    
    if (minRow === maxRow && minCol === maxCol) {
      return getCellAddress(minRow, minCol)
    }
    return `${getCellAddress(minRow, minCol)}:${getCellAddress(maxRow, maxCol)}`
  }

  // 셀 선택 여부
  const isCellSelected = (row: number, col: number): boolean => {
    if (!selection.start) return false
    const end = selection.end || selection.start
    const minRow = Math.min(selection.start.row, end.row)
    const maxRow = Math.max(selection.start.row, end.row)
    const minCol = Math.min(selection.start.col, end.col)
    const maxCol = Math.max(selection.start.col, end.col)
    return row >= minRow && row <= maxRow && col >= minCol && col <= maxCol
  }

  // 에러/경고 셀인지 확인 (currentErrors가 있으면 그것 사용, 없으면 allErrors)
  const getCellErrorType = (rowIdx: number, colIdx: number): 'error' | 'warning' | null => {
    if (rowIdx === 0 || colIdx === 0) return null
    const fieldName = headers[colIdx]
    const errorsToCheck = currentErrors.length > 0 ? currentErrors : allErrors
    
    for (const err of errorsToCheck) {
      const excelRow = rowIdx + 1
      if (err.row === excelRow && err.field === fieldName) {
        return err.severity
      }
    }
    return null
  }

  // 마우스 핸들러
  const handleMouseDown = (rowIdx: number, colIdx: number, e: React.MouseEvent) => {
    if (rowIdx === 0 || colIdx === 0) return
    if (e.shiftKey && selection.start) {
      setSelection(prev => ({ ...prev, end: { row: rowIdx, col: colIdx }, isSelecting: false }))
    } else {
      setSelection({ start: { row: rowIdx, col: colIdx }, end: { row: rowIdx, col: colIdx }, isSelecting: true })
    }
  }

  const handleMouseEnter = (rowIdx: number, colIdx: number) => {
    if (!selection.isSelecting || rowIdx === 0 || colIdx === 0) return
    setSelection(prev => ({ ...prev, end: { row: rowIdx, col: colIdx } }))
  }

  const handleMouseUp = () => {
    if (selection.isSelecting) {
      setSelection(prev => ({ ...prev, isSelecting: false }))
    }
  }

  // 더블클릭 편집
  const handleCellDoubleClick = (rowIdx: number, colIdx: number) => {
    if (rowIdx === 0 || colIdx === 0) return
    setActiveCell({ row: rowIdx, col: colIdx })
    setEditValue(sheetData[rowIdx]?.[colIdx] || '')
  }

  const handleCellChange = (value: string) => {
    setEditValue(value)
    if (activeCell) {
      const newData = [...sheetData]
      newData[activeCell.row] = [...newData[activeCell.row]]
      newData[activeCell.row][activeCell.col] = value
      setSheetData(newData)
    }
  }

  const handleCellBlur = () => {
    setActiveCell(null)
  }

  // 저장
  const handleSave = () => {
    if (onSave) {
      // 행 번호 열 제거
      const dataWithoutRowNumbers = sheetData.slice(1).map(row => row.slice(1))
      const saveData = [sheetData[0].slice(1), ...dataWithoutRowNumbers]
      console.log('💾 저장 데이터:', saveData)
      onSave(saveData)
    }
    onClose()
  }

  // 다운로드 (다른 이름으로 저장)
  const handleDownload = async () => {
    try {
      // 행 번호 열 제거
      const headers = sheetData[0].slice(1)
      const dataRows = sheetData.slice(1).map(row => row.slice(1))
      
      // 헤더를 키로 하는 객체 배열로 변환
      const exportData = dataRows.map(row => {
        const obj: Record<string, any> = {}
        headers.forEach((header, idx) => {
          obj[header] = row[idx] || ''
        })
        return obj
      })
      
      const response = await fetch('http://127.0.0.1:8004/api/export/xlsx', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: filename,
          headers: headers,
          data: exportData
        })
      })
      
      if (!response.ok) {
        throw new Error('파일 다운로드 실패')
      }
      
      // Blob으로 변환하여 다운로드
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      // 파일명 추출 (Content-Disposition 헤더에서)
      const contentDisposition = response.headers.get('Content-Disposition')
      let downloadFilename = filename.replace('.xlsx', '_수정본.xlsx')
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']*)['"]?/i)
        if (filenameMatch && filenameMatch[1]) {
          downloadFilename = decodeURIComponent(filenameMatch[1])
        }
      }
      
      a.download = downloadFilename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      // 성공 메시지
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `✅ **다운로드 완료!** "${downloadFilename}" 파일이 저장되었습니다.`,
        timestamp: new Date()
      }])
      
    } catch (error) {
      console.error('다운로드 에러:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ 다운로드 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`,
        timestamp: new Date()
      }])
    }
  }

  // 날짜 형식 감지 및 변환
  const detectAndFormatDate = (originalValue: string, newDateYYYYMMDD: string): string => {
    if (!originalValue || !newDateYYYYMMDD) return newDateYYYYMMDD
    
    // 원본 형식 감지
    const original = String(originalValue).trim()
    const year = newDateYYYYMMDD.slice(0, 4)
    const month = newDateYYYYMMDD.slice(4, 6)
    const day = newDateYYYYMMDD.slice(6, 8)
    
    // YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(original)) {
      return `${year}-${month}-${day}`
    }
    // YYYY/MM/DD
    if (/^\d{4}\/\d{2}\/\d{2}$/.test(original)) {
      return `${year}/${month}/${day}`
    }
    // YYYY.MM.DD
    if (/^\d{4}\.\d{2}\.\d{2}$/.test(original)) {
      return `${year}.${month}.${day}`
    }
    // YY-MM-DD (2자리 년도)
    if (/^\d{2}-\d{2}-\d{2}$/.test(original)) {
      return `${year.slice(2)}-${month}-${day}`
    }
    // YYYYMMDD (구분자 없음)
    if (/^\d{8}$/.test(original)) {
      return newDateYYYYMMDD
    }
    // 그 외: 그대로 반환
    return newDateYYYYMMDD
  }

  // 금액 형식 감지 및 변환
  const detectAndFormatAmount = (originalValue: string, newAmount: string): string => {
    if (!originalValue || !newAmount) return newAmount
    
    const original = String(originalValue).trim()
    const numOnly = newAmount.replace(/[^0-9.-]/g, '')
    
    // 원본이 천 단위 콤마 형식이면 (예: 1,000,000)
    if (/^[\d,]+$/.test(original) && original.includes(',')) {
      const num = parseInt(numOnly)
      if (!isNaN(num)) {
        return num.toLocaleString('ko-KR')
      }
    }
    
    // 원본이 "원" 단위 포함 (예: 1,000,000원)
    if (original.endsWith('원')) {
      const num = parseInt(numOnly)
      if (!isNaN(num)) {
        return num.toLocaleString('ko-KR') + '원'
      }
    }
    
    // 원본이 소수점 포함 (예: 7736629.75)
    if (original.includes('.') && /^\d+\.\d+$/.test(original)) {
      const num = parseFloat(numOnly)
      if (!isNaN(num)) {
        // 원본 소수점 자릿수 유지
        const decimalPlaces = original.split('.')[1]?.length || 2
        return num.toFixed(decimalPlaces)
      }
    }
    
    // 그 외: 숫자만 반환
    return numOnly
  }

  // AI 수정 명령 적용
  const applyEditCommands = (response: string) => {
    console.log('🔍 AI 응답 분석:', response)
    const editPattern = /\[(?:EDIT|수정):(\d+):([^:]+):([^\]]+)\]/gi
    const edits: Array<{row: number, col: number, value: string, field: string, cellAddress: string}> = []
    let match
    
    while ((match = editPattern.exec(response)) !== null) {
      const rowNum = parseInt(match[1])
      const fieldName = match[2].trim()
      let newValue = match[3].trim()
      const colIdx = headers.indexOf(fieldName)
      
      console.log(`📝 수정 명령 발견: row=${rowNum}, field=${fieldName}, value=${newValue}, colIdx=${colIdx}`)
      
      if (colIdx !== -1 && rowNum > 0 && rowNum <= sheetData.length) {
        const originalValue = sheetData[rowNum]?.[colIdx] || ''
        
        // 날짜 필드인 경우 원본 형식에 맞게 변환
        const isDateField = /날짜|일자|생년월일|입사|퇴직/.test(fieldName)
        if (isDateField && /^\d{8}$/.test(newValue)) {
          newValue = detectAndFormatDate(originalValue, newValue)
        }
        
        // 금액 필드인 경우 원본 형식에 맞게 변환
        const isAmountField = /급여|금액|임금|퇴직금|추계액/.test(fieldName)
        if (isAmountField && /^\d+$/.test(newValue)) {
          newValue = detectAndFormatAmount(originalValue, newValue)
        }
        
        edits.push({ row: rowNum, col: colIdx, value: newValue, field: fieldName, cellAddress: getCellAddress(rowNum, colIdx) })
      }
    }
    
    if (edits.length > 0) {
      console.log('✅ 적용할 수정 사항:', edits)
      const newData = [...sheetData]
      edits.forEach(edit => {
        // 행이 배열인지 객체인지 확인
        if (Array.isArray(newData[edit.row])) {
          newData[edit.row] = [...newData[edit.row]]
          newData[edit.row][edit.col] = edit.value
        } else if (newData[edit.row] && typeof newData[edit.row] === 'object') {
          // 객체인 경우 배열로 변환하여 유지
          const headers = sheetData[0] as string[]
          const rowArray = headers.map(h => (newData[edit.row] as Record<string, unknown>)[h] ?? '')
          rowArray[edit.col] = edit.value
          newData[edit.row] = rowArray as typeof newData[number]
        }
      })
      setSheetData(newData)
      setPendingEdits(prev => {
        const updated = [...prev, ...edits]
        console.log('📌 pendingEdits 업데이트:', updated)
        return updated
      })
      
      // 첫 번째 수정 셀 선택
      setSelection({
        start: { row: edits[0].row, col: edits[0].col },
        end: { row: edits[0].row, col: edits[0].col },
        isSelecting: false
      })
    } else {
      console.log('⚠️ 수정 명령을 찾을 수 없음')
    }
    return edits
  }

  // AI 채팅
  const handleSend = async () => {
    if (!input.trim() || isThinking) return
    
    const userMessage = input.trim()
    const cellRef = getSelectionRangeString()
    
    setMessages(prev => [...prev, { role: 'user', content: userMessage, timestamp: new Date(), cellRef }])
    setInput('')
    setIsThinking(true)

    try {
      // 개별 수정 모드: 이미 row/field가 있음
      let context = ''
      if (targetRow !== undefined && targetField) {
        context = `
[개별 수정 모드]
수정 대상: 행번호=${targetRow}, 필드명="${targetField}"
문제: ${errorMessage || '없음'}
현재 선택: ${cellRef || '없음'}

사용자가 값을 말하면 바로 수정 명령을 생성하세요.
예: "2024년 1월 1일로 변경해줘" → [수정:${targetRow}:${targetField}:20240101]
`
      }
      // 전체 수정 모드
      else if (allErrors.length > 0) {
        context = `
[전체 수정 모드]
에러 목록:
${allErrors.map((e, i) => `${i + 1}번: 행번호=${e.row}, 필드명="${e.field}", 내용="${e.message}"`).join('\n')}
현재 선택: ${cellRef || '없음'}

"N번"이라고 하면 위 목록의 N번째 항목입니다.
`
      }
      
      context += `
[필수 규칙]
수정 요청 시 반드시: [수정:행번호:필드명:새값]
- 날짜: YYYY-MM-DD (2024년 5월 20일 → 2024-05-20)
- 금액: 숫자만 (206만원 → 2060000)

[수정:행:필드:값] 없이 응답하면 수정이 적용되지 않습니다!
`

      // 30초 타임아웃 설정
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)
      
      const response = await fetch('http://127.0.0.1:8004/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, context }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        const data = await response.json()
        const aiResponse = data.response || '죄송합니다, 응답을 생성하지 못했습니다.'
        
        const edits = applyEditCommands(aiResponse)
        let displayResponse = aiResponse.replace(/\[(?:EDIT|수정):[^\]]+\]/gi, '').trim()
        
        if (edits.length > 0) {
          displayResponse += `\n\n✅ **${edits.length}건 수정 완료:**\n${edits.map(e => 
            `• 📍 **${e.cellAddress}** (${e.field}) → "${e.value}"`
          ).join('\n')}`
        }
        
        setMessages(prev => [...prev, { role: 'assistant', content: displayResponse, timestamp: new Date() }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `서버 오류가 발생했습니다. (상태: ${response.status})`, timestamp: new Date() }])
      }
    } catch (error) {
      console.error('❌ 네트워크 오류:', error)
      const errorMessage = error instanceof Error 
        ? (error.name === 'AbortError' ? '요청 시간이 초과되었습니다. (30초)' : error.message)
        : '알 수 없는 오류'
      setMessages(prev => [...prev, { role: 'assistant', content: `네트워크 오류: ${errorMessage}`, timestamp: new Date() }])
    } finally {
      setIsThinking(false)
    }
  }

  // Quick Actions
  const quickActions = targetRow !== undefined && targetField
    ? [
        { label: '수정 적용', emoji: '✅', prompt: `이 값으로 수정해줘` },
        { label: '왜 오류?', emoji: '❓', prompt: '왜 이 값이 오류인가요?' },
      ]
    : [
        { label: '전체 수정', emoji: '🔧', prompt: '모든 에러를 올바른 값으로 수정해줘' },
        { label: '1번 수정', emoji: '1️⃣', prompt: '1번 항목을 올바른 값으로 수정해줘' },
        { label: '규칙 설명', emoji: '📖', prompt: '입력 규칙을 알려줘' },
      ]

  return (
    <div className="sheet-pro-overlay" onClick={onClose}>
      <div ref={containerRef} className="sheet-pro-container" onClick={e => e.stopPropagation()}>
        {/* 왼쪽: 스프레드시트 */}
        <div className="sheet-pro-main">
          {/* 툴바 */}
          <div className="sheet-pro-toolbar">
            <div className="toolbar-left">
              <div className="toolbar-logo">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <line x1="3" y1="9" x2="21" y2="9"/>
                  <line x1="9" y1="21" x2="9" y2="9"/>
                </svg>
              </div>
              <div className="toolbar-title">
                <h1>데이터 수정</h1>
                <p>AI 어시스턴트와 함께</p>
              </div>
            </div>
            
            <div className="toolbar-divider" />
            
            {/* 선택 범위 표시 */}
            {selection.start && (
              <div className="selection-indicator">
                📍 {getSelectionRangeString()}
              </div>
            )}
            
            {pendingEdits.length > 0 && (
              <div className="edit-count">✏️ {pendingEdits.length}건 수정됨</div>
            )}
            
            <div className="toolbar-spacer" />
            
            {/* 재검증 버튼 */}
            {pendingEdits.length > 0 && onRevalidate && (
              <button 
                className="btn-revalidate" 
                onClick={async () => {
                  setIsRevalidating(true)
                  try {
                    const dataWithoutRowNumbers = sheetData.slice(1).map(row => row.slice(1))
                    const newErrors = await onRevalidate([sheetData[0].slice(1), ...dataWithoutRowNumbers])
                    setCurrentErrors(newErrors)
                    
                    if (newErrors.length === 0) {
                      setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: '✅ **재검증 완료!** 모든 오류가 해결되었습니다. 저장 버튼을 눌러주세요!',
                        timestamp: new Date()
                      }])
                    } else {
                      setMessages(prev => [...prev, {
                        role: 'assistant',
                        content: `⚠️ **재검증 결과:** 아직 ${newErrors.length}건의 문제가 남아있습니다.\n\n${newErrors.map((e, i) => `${i+1}. ${e.message}`).join('\n')}`,
                        timestamp: new Date()
                      }])
                    }
                  } catch (err) {
                    setMessages(prev => [...prev, {
                      role: 'assistant',
                      content: '❌ 재검증 중 오류가 발생했습니다.',
                      timestamp: new Date()
                    }])
                  } finally {
                    setIsRevalidating(false)
                  }
                }}
                disabled={isRevalidating}
              >
                {isRevalidating ? '🔄 검증 중...' : '🔍 재검증'}
              </button>
            )}
            
            <button className="btn-cancel" onClick={onClose}>취소</button>
            <button className="btn-download" onClick={handleDownload}>💾 다른 이름으로 저장</button>
            <button className="btn-save" onClick={handleSave}>✅ 적용</button>
          </div>

          {/* 스프레드시트 */}
          <div className="sheet-pro-grid" ref={tableRef} onMouseUp={handleMouseUp}>
            <table className="sheet-table">
              <tbody>
                {sheetData.slice(0, 50).map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {row.map((cell, colIdx) => {
                      const isHeader = rowIdx <= 1 || colIdx === 0  // 0행(컬럼레이블), 1행(헤더), 0열(행번호)
                      const isSelected = isCellSelected(rowIdx, colIdx)
                      const isEditing = activeCell?.row === rowIdx && activeCell?.col === colIdx
                      const isEdited = pendingEdits.some(e => e.row === rowIdx && e.col === colIdx)
                      const isStart = selection.start?.row === rowIdx && selection.start?.col === colIdx
                      const errorType = getCellErrorType(rowIdx, colIdx)
                      
                      return (
                        <td
                          key={`${rowIdx}-${colIdx}`}
                          className={`
                            sheet-cell
                            ${isHeader ? 'header-cell' : ''}
                            ${isSelected ? 'selected-cell' : ''}
                            ${isStart ? 'start-cell' : ''}
                            ${isEdited ? 'edited-cell' : ''}
                            ${errorType === 'error' ? 'error-cell' : ''}
                            ${errorType === 'warning' ? 'warning-cell' : ''}
                          `}
                          onMouseDown={(e) => handleMouseDown(rowIdx, colIdx, e)}
                          onMouseEnter={() => handleMouseEnter(rowIdx, colIdx)}
                          onDoubleClick={() => handleCellDoubleClick(rowIdx, colIdx)}
                          title={!isHeader && colIdx > 0 && rowIdx > 1 ? `셀 ${getCellAddress(rowIdx, colIdx)}` : undefined}
                        >
                          {isHeader ? (
                            <div className="cell-header">
                              {cell}
                            </div>
                          ) : isEditing ? (
                            <input
                              type="text"
                              className="cell-input"
                              value={editValue}
                              onChange={(e) => handleCellChange(e.target.value)}
                              onBlur={handleCellBlur}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleCellBlur()
                                if (e.key === 'Escape') { setActiveCell(null) }
                              }}
                              autoFocus
                            />
                          ) : (
                            <div className="cell-content">
                              {isEdited && <span className="edit-mark">✓</span>}
                              {cell}
                            </div>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 팁 */}
          <div className="sheet-tips">
            <strong>Tips:</strong> 클릭하여 선택 • 드래그로 범위 선택 • 더블클릭으로 편집 • Shift+클릭으로 범위 확장
          </div>
        </div>

        {/* 리사이저 */}
        <div 
          className={`sheet-resizer ${isResizing ? 'active' : ''}`}
          onMouseDown={handleResizeStart}
        >
          <div className="resizer-handle" />
        </div>

        {/* 오른쪽: AI 사이드바 */}
        <div className="sheet-pro-sidebar" style={{ width: sidebarWidth }}>
          {/* 사이드바 헤더 */}
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
            </div>
            <div className="sidebar-title">
              <h2>AI Assistant <span className="beta-tag">Beta</span></h2>
              <p>스마트 데이터 수정</p>
            </div>
          </div>

          {/* 메시지 영역 */}
          <div className="sidebar-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  {msg.cellRef && (
                    <span className="message-cell-ref">📍 {msg.cellRef}</span>
                  )}
                  <div className="message-bubble">
                    {msg.content.split('\n').map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                  </div>
                  <span className="message-time">
                    {msg.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
            
            {isThinking && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content">
                  <div className="message-bubble thinking">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="sidebar-quick-actions">
            <p className="quick-label">Quick Actions</p>
            <div className="quick-buttons">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  className="quick-btn"
                  onClick={() => setInput(action.prompt)}
                >
                  <span>{action.emoji}</span> {action.label}
                </button>
              ))}
            </div>
          </div>

          {/* 입력 영역 */}
          <div className="sidebar-input-area">
            {selection.start && (
              <div className="input-selection-hint">
                📍 선택됨: <strong>{getSelectionRangeString()}</strong>
              </div>
            )}
            <div className="input-row">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="수정할 내용을 입력하세요..."
                className="chat-input"
              />
              <button
                className="send-btn"
                onClick={handleSend}
                disabled={!input.trim() || isThinking}
              >
                {isThinking ? '⏳' : '➤'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
