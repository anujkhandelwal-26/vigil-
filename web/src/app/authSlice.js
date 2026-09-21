import { createSlice } from '@reduxjs/toolkit'

const stored = (() => {
  try {
    const raw = localStorage.getItem('vigil_auth')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
})()

const authSlice = createSlice({
  name: 'auth',
  initialState: stored || { token: null, username: null, role: null, displayName: null },
  reducers: {
    setCredentials: (state, action) => {
      const { token, username, role, displayName } = action.payload
      state.token = token
      state.username = username
      state.role = role
      state.displayName = displayName
      try {
        localStorage.setItem('vigil_auth', JSON.stringify(state))
      } catch {
        // ignore storage failures (private window etc.) -- session still works in memory
      }
    },
    logout: (state) => {
      state.token = null
      state.username = null
      state.role = null
      state.displayName = null
      try {
        localStorage.removeItem('vigil_auth')
      } catch {
        // ignore
      }
    },
  },
})

export const { setCredentials, logout } = authSlice.actions
export default authSlice.reducer
