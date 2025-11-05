import axios from 'axios'

// Create Axios instance with default settings
export const api = axios.create({
  baseURL: '/api', // Works in both dev (proxy) and production (served via FastAPI)
  timeout: 10000,
})

// Helper: handle API errors globally
function handleError(error) {
  console.error('[API ERROR]', error.response?.status, error.message)
  // Return structured error info (UI can react accordingly)
  return { error: true, status: error.response?.status || 500, message: error.message }
}

// --- API Calls ---

// Fetch all registered nodes and their statuses
export async function getNodes() {
  try {
    const res = await api.get('/nodes')
    return res.data
  } catch (err) {
    return handleError(err)
  }
}

// Force an update of node statuses (triggers /update_status)
export async function updateStatus() {
  try {
    const res = await api.post('/update_status')
    return res.data
  } catch (err) {
    return handleError(err)
  }
}

// Start irrigation on a given zone (with water amount)
export async function startIrrigation(zoneId, liters) {
  try {
    const res = await api.post('/start_irrigation', { zone_id: zoneId, liter_amount: liters })
    return res.data
  } catch (err) {
    return handleError(err)
  }
}

// Stop all irrigation processes
export async function stopIrrigation() {
  try {
    const res = await api.post('/stop_irrigation')
    return res.data
  } catch (err) {
    return handleError(err)
  }
}

// Ping the server to check API availability
export async function ping() {
  try {
    const res = await api.get('/ping')
    return res.data
  } catch (err) {
    return handleError(err)
  }
}
