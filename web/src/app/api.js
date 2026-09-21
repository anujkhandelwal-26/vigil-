import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

const baseQuery = fetchBaseQuery({
  baseUrl: '/api/v1',
  prepareHeaders: (headers, { getState }) => {
    const token = getState().auth.token
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return headers
  },
})

export const api = createApi({
  reducerPath: 'api',
  baseQuery,
  tagTypes: ['Applications', 'Kpis', 'Models'],
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (body) => ({ url: '/auth/login', method: 'POST', body }),
    }),
    submitApplication: builder.mutation({
      query: (body) => ({ url: '/applications', method: 'POST', body }),
      invalidatesTags: ['Applications', 'Kpis'],
    }),
    listApplications: builder.query({
      query: ({ action = 'ALL', limit = 100 } = {}) =>
        `/applications?action=${action}&limit=${limit}`,
      providesTags: ['Applications'],
    }),
    getKpis: builder.query({
      query: () => '/applications/kpis',
      providesTags: ['Kpis'],
    }),
    getApplicationDetail: builder.query({
      query: (id) => `/applications/${id}`,
    }),
    getRing: builder.query({
      query: (id) => `/applications/${id}/ring`,
    }),
    getNarrative: builder.query({
      query: (id) => ({ url: `/applications/${id}/narrative`, method: 'POST' }),
    }),
    submitFeedback: builder.mutation({
      query: ({ id, verdict, note }) => ({
        url: `/applications/${id}/feedback`,
        method: 'POST',
        body: { verdict, note },
      }),
      invalidatesTags: ['Applications', 'Kpis'],
    }),
    copilotQuery: builder.mutation({
      query: (body) => ({ url: '/copilot/query', method: 'POST', body }),
    }),
    listModels: builder.query({
      query: () => '/models',
      providesTags: ['Models'],
    }),
    getCostCurve: builder.query({
      query: () => '/models/cost-curve',
      providesTags: ['Models'],
    }),
    retrainModel: builder.mutation({
      query: () => ({ url: '/models/retrain', method: 'POST' }),
      invalidatesTags: ['Models'],
    }),
  }),
})

export const {
  useLoginMutation,
  useSubmitApplicationMutation,
  useListApplicationsQuery,
  useGetKpisQuery,
  useGetApplicationDetailQuery,
  useGetRingQuery,
  useLazyGetNarrativeQuery,
  useSubmitFeedbackMutation,
  useCopilotQueryMutation,
  useListModelsQuery,
  useGetCostCurveQuery,
  useRetrainModelMutation,
} = api
