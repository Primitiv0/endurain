import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_sleep = {
  getUserHealthSleepWithPagination(pageNumber, numRecords, filter) {
    return fetchGetRequest(
      `health/sleep/page_number/${pageNumber}/num_records/${numRecords}?interval=${filter}`
    )
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
