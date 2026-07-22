import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api, Complaint } from '../api/client';

export const fetchComplaint = createAsyncThunk(
  'currentComplaint/fetch',
  async (id: number) => (await api.getComplaint(id)) as Complaint
);

interface AgentFlags {
  extracting: boolean;
  classifying: boolean;
  rootCause: boolean;
  capa: boolean;
  summarizing: boolean;
}

interface CurrentComplaintState {
  data: Complaint | null;
  loading: boolean;
  error: string | null;
  agentFlags: AgentFlags;
  agentSteps: string[];
  draft: Record<string, unknown>;
}

const initialState: CurrentComplaintState = {
  data: null,
  loading: false,
  error: null,
  agentFlags: {
    extracting: false,
    classifying: false,
    rootCause: false,
    capa: false,
    summarizing: false,
  },
  agentSteps: [],
  draft: {},
};

const currentComplaintSlice = createSlice({
  name: 'currentComplaint',
  initialState,
  reducers: {
    setAgentFlag(state, action: { payload: { key: keyof AgentFlags; value: boolean } }) {
      state.agentFlags[action.payload.key] = action.payload.value;
    },
    appendAgentSteps(state, action: { payload: string[] }) {
      state.agentSteps = [...state.agentSteps, ...action.payload];
    },
    clearAgentSteps(state) {
      state.agentSteps = [];
    },
    setDraft(state, action: { payload: Record<string, unknown> }) {
      state.draft = { ...state.draft, ...action.payload };
    },
    clearDraft(state) {
      state.draft = {};
    },
    updateLocalComplaint(state, action: { payload: Partial<Complaint> }) {
      if (state.data) state.data = { ...state.data, ...action.payload };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchComplaint.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComplaint.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchComplaint.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to load complaint';
      });
  },
});

export const {
  setAgentFlag,
  appendAgentSteps,
  clearAgentSteps,
  setDraft,
  clearDraft,
  updateLocalComplaint,
} = currentComplaintSlice.actions;
export default currentComplaintSlice.reducer;
