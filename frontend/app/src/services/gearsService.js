import {
  fetchGetRequest,
  fetchPostRequest,
  fetchPutRequest,
  fetchDeleteRequest
} from '@/utils/serviceUtils'

export const gears = {
  getUserGearsWithPagination(pageNumber = null, numRecords = null, filters = {}) {
    let queryString = `gears?`

    Object.keys(filters).forEach((key) => {
      if (filters[key] !== null && filters[key] !== undefined) {
        // Convert camelCase to snake_case
        const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
        queryString += `${snakeKey}=${encodeURIComponent(filters[key])}&`
      }
    })

    // Add pagination parameters only if they are provided
    if (pageNumber !== null && numRecords !== null) {
      queryString += `page_number=${pageNumber}&num_records=${numRecords}&`
    }

    // Remove trailing '&' or '?' if no filters were added
    queryString = queryString.slice(0, -1)

    return fetchGetRequest(queryString)
  },
  getGearById(gearId) {
    return fetchGetRequest(`gears/id/${gearId}`)
  },
  getGearFromType(gearType) {
    return fetchGetRequest(`gears/type/${gearType}`)
  },
  getGearContainsNickname(nickname) {
    return fetchGetRequest(`gears/nickname/contains/${nickname}`)
  },
  getGearByNickname(nickname) {
    return fetchGetRequest(`gears/nickname/${nickname}`)
  },
  createGear(data) {
    return fetchPostRequest('gears', data)
  },
  editGear(gearId, data) {
    return fetchPutRequest(`gears/${gearId}`, data)
  },
  deleteGear(gearId) {
    return fetchDeleteRequest(`gears/${gearId}`)
  }
}
