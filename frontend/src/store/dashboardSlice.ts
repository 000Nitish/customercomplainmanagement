import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../api/client';

export const fetchDashboard = createAsyncThunk('dashboard/fetch', async () => {
  return api.dashboard();
});

interface DashboardState {
  summary: {
    total: number;
    by_status: Record<string, number>;
    by_severity: Record<string, number>;
    by_product: Record<string, number>;
    by_type: Record<string, number>;
    recent_trend: { period: string; count: number }[];
  } | null;
  loading: boolean;
  error: string | null;
}

const initialState: DashboardState = {
  summary: null,
  loading: false,
  error: null,
};

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboard.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.loading = false;
        state.summary = action.payload as DashboardState['summary'];
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to load dashboard';
      });
  },
});

export default dashboardSlice.reducer;
