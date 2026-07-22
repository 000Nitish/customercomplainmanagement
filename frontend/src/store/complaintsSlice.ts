import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api, Complaint } from '../api/client';

export const fetchComplaints = createAsyncThunk('complaints/fetchAll', async () => {
  return (await api.getComplaints()) as Complaint[];
});

interface ComplaintsState {
  items: Complaint[];
  loading: boolean;
  error: string | null;
  filters: { status?: string; severity?: string; product?: string };
}

const initialState: ComplaintsState = {
  items: [],
  loading: false,
  error: null,
  filters: {},
};

const complaintsSlice = createSlice({
  name: 'complaints',
  initialState,
  reducers: {
    setFilters(state, action) {
      state.filters = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchComplaints.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComplaints.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchComplaints.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to load complaints';
      });
  },
});

export const { setFilters } = complaintsSlice.actions;
export default complaintsSlice.reducer;
