import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const health_steps = {
  getUserHealthStepsWithPagination(pageNumber, numRecords, paginationFilter, intervalFilter) {
    const params = new URLSearchParams()
    if (paginationFilter !== 'disabled') {
      params.append('page_number', pageNumber)
      params.append('num_records', numRecords)
    }
    params.append('interval', intervalFilter)

    const queryString = params.toString()
    const url = queryString ? `health/steps?${queryString}` : 'health/steps'
    return fetchGetRequest(url)
  },
  createHealthSteps(data) {
    return fetchPostRequest('health/steps', data)
  },
  editHealthSteps(data) {
    return fetchPutRequest('health/steps', data)
  },
  deleteHealthSteps(healthStepsId) {
    return fetchDeleteRequest(`health/steps/${healthStepsId}`)
  }
}
