import { configureStore } from '@reduxjs/toolkit';
import complaintsReducer from './complaintsSlice';
import currentComplaintReducer from './currentComplaintSlice';
import dashboardReducer from './dashboardSlice';

export const store = configureStore({
  reducer: {
    complaints: complaintsReducer,
    currentComplaint: currentComplaintReducer,
    dashboard: dashboardReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
