import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_fasting = {
  getUserHealthFastingWithPagination(pageNumber, numRecords, paginationFilter, intervalFilter) {
    const params = new URLSearchParams()
    if (paginationFilter !== 'disabled') {
      params.append('page_number', pageNumber)
      params.append('num_records', numRecords)
    }
    params.append('interval', intervalFilter)

    const queryString = params.toString()
    const url = queryString ? `health/fasting?${queryString}` : 'health/fasting'
    return fetchGetRequest(url)
  },
  getActiveFasting() {
    return fetchGetRequest('health/fasting/active')
  },
  getFastingStats() {
    return fetchGetRequest('health/fasting/stats')
  },
  createHealthFasting(data) {
    return fetchPostRequest('health/fasting', data)
  },
  completeHealthFasting(fastingId, data) {
    return fetchPostRequest(`health/fasting/${fastingId}/complete`, data)
  },
  editHealthFasting(data) {
    return fetchPutRequest('health/fasting', data)
  },
  deleteHealthFasting(healthFastingId) {
    return fetchDeleteRequest(`health/fasting/${healthFastingId}`)
  }
}
