import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_poop = {
  getUserHealthPoopWithPagination(pageNumber, numRecords, paginationFilter, intervalFilter) {
    const params = new URLSearchParams()
    if (paginationFilter !== 'disabled') {
      params.append('page_number', pageNumber)
      params.append('num_records', numRecords)
    }
    params.append('interval', intervalFilter)

    const queryString = params.toString()
    const url = queryString ? `health/poop?${queryString}` : 'health/poop'
    return fetchGetRequest(url)
  },
  createHealthPoop(data) {
    return fetchPostRequest('health/poop', data)
  },
  editHealthPoop(data) {
    return fetchPutRequest('health/poop', data)
  },
  deleteHealthPoop(healthPoopId) {
    return fetchDeleteRequest(`health/poop/${healthPoopId}`)
  }
}
