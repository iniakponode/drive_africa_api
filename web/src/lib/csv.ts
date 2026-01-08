export type CsvRow = Record<string, string>

function normalizeKey(key: string) {
  return key.trim().toLowerCase().replace(/[^a-z0-9_]/g, '')
}

export function parseCsvRecords(text: string): {
  headers: string[]
  rows: CsvRow[]
} {
  const rows: string[][] = []
  let current = ''
  let inQuotes = false
  let row: string[] = []

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    if (char === '"') {
      const next = text[i + 1]
      if (inQuotes && next === '"') {
        current += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }
    if (char === ',' && !inQuotes) {
      row.push(current)
      current = ''
      continue
    }
    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && text[i + 1] === '\n') {
        i += 1
      }
      row.push(current)
      current = ''
      if (row.some((value) => value.trim() !== '')) {
        rows.push(row)
      }
      row = []
      continue
    }
    current += char
  }

  if (current.length || row.length) {
    row.push(current)
    if (row.some((value) => value.trim() !== '')) {
      rows.push(row)
    }
  }

  if (rows.length === 0) {
    return { headers: [], rows: [] }
  }

  const headerRow = rows[0].map((header) => header.trim())
  const normalizedHeaders = headerRow.map(normalizeKey)
  const dataRows = rows.slice(1)
  const records: CsvRow[] = dataRows.map((cells) => {
    const record: CsvRow = {}
    normalizedHeaders.forEach((header, index) => {
      record[header] = (cells[index] ?? '').trim()
    })
    return record
  })

  return { headers: headerRow, rows: records }
}

export function getRowValue(row: CsvRow, keys: string[]) {
  for (const key of keys) {
    const normalized = normalizeKey(key)
    const value = row[normalized]
    if (value !== undefined && value !== '') {
      return value
    }
  }
  return ''
}

export function downloadCsv(
  filename: string,
  headers: string[],
  rows: Array<Record<string, string | number | boolean | null | undefined>>,
) {
  const escape = (value: string) => {
    const needsQuotes = /[",\n\r]/.test(value)
    const escaped = value.replace(/"/g, '""')
    return needsQuotes ? `"${escaped}"` : escaped
  }

  const lines = [headers.map((header) => escape(header)).join(',')]
  rows.forEach((row) => {
    const line = headers.map((header) => {
      const raw = row[header]
      if (raw === null || raw === undefined) {
        return ''
      }
      return escape(String(raw))
    })
    lines.push(line.join(','))
  })

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
