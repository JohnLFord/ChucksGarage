export type ApiResult = {
  status: number
  method: string
  path: string
  requestBody?: unknown
  data: unknown
}

export async function apiRequest<T>(
  path: string,
  method: string,
  token?: string,
  body?: unknown,
): Promise<ApiResult & { data: T }> {
  const headers: HeadersInit = { Accept: 'application/json' }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const contentType = response.headers.get('content-type') ?? ''
  const responseData = contentType.includes('application/json')
    ? await response.json()
    : await response.text()
  const data = response.ok || contentType.includes('application/json')
    ? responseData
    : {
        error: `Request failed with status ${response.status}`,
        details: 'The server returned an HTML error page. Check the API logs for the underlying exception.',
      }

  if (!response.ok) {
    const message =
      typeof data === 'object' && data !== null && 'error' in data
        ? String(data.error)
        : `Request failed with status ${response.status}`
    throw Object.assign(new Error(message), {
      result: { status: response.status, method, path, requestBody: body, data },
    })
  }

  return { status: response.status, method, path, requestBody: body, data }
}
