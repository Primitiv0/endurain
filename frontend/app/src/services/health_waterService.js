import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_water = {
  getUserHealthWaterWithPagination(pageNumber, numRecords, paginationFilter, intervalFilter) {
    const params = new URLSearchParams()
    if (paginationFilter !== 'disabled') {
      params.append('page_number', pageNumber)
      params.append('num_records', numRecords)
    }
    params.append('interval', intervalFilter)

    const queryString = params.toString()
    const url = queryString ? `health/water?${queryString}` : 'health/water'
    return fetchGetRequest(url)
  },
  createHealthWater(data) {
    return fetchPostRequest('health/water', data)
  },
  editHealthWater(data) {
    return fetchPutRequest('health/water', data)
  },
  deleteHealthWater(healthWaterId) {
    return fetchDeleteRequest(`health/water/${healthWaterId}`)
  }
}
