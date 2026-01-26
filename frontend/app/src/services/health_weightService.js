import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_weight = {
  getUserHealthWeightWithPagination(pageNumber, numRecords, paginationFilter, intervalFilter) {
    const params = new URLSearchParams()
    if (paginationFilter !== 'disabled') {
      params.append('page_number', pageNumber)
      params.append('num_records', numRecords)
    }
    params.append('interval', intervalFilter)

    const queryString = params.toString()
    const url = queryString ? `health/weight?${queryString}` : 'health/weight'
    return fetchGetRequest(url)
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
