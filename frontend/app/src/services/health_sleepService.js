import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_sleep = {
  getUserHealthSleepWithPagination(pageNumber, numRecords, paginationFilter, intervalFilter) {
    const params = new URLSearchParams()
    if (paginationFilter !== 'disabled') {
      params.append('page_number', pageNumber)
      params.append('num_records', numRecords)
    }
    params.append('interval', intervalFilter)

    const queryString = params.toString()
    const url = queryString ? `health/sleep?${queryString}` : 'health/sleep'
    return fetchGetRequest(url)
  },
  createHealthSleep(data) {
    return fetchPostRequest('health/sleep', data)
  },
  editHealthSleep(data) {
    return fetchPutRequest('health/sleep', data)
  },
  deleteHealthSleep(healthSleepId) {
    return fetchDeleteRequest(`health/sleep/${healthSleepId}`)
  }
}
