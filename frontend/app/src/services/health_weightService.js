import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_weight = {
  getUserHealthWeightWithPagination(pageNumber, numRecords, filter) {
    return fetchGetRequest(
      `health/weight/page_number/${pageNumber}/num_records/${numRecords}?interval=${filter}`
    )
  },
  createHealthWeight(data) {
    return fetchPostRequest('health/weight', data)
  },
  editHealthWeight(data) {
    return fetchPutRequest('health/weight', data)
  },
  deleteHealthWeight(healthWeightId) {
    return fetchDeleteRequest(`health/weight/${healthWeightId}`)
  }
}
