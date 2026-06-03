import { fetchGetRequest, fetchPutRequest } from '@/utils/serviceUtils'

export const userDefaultGear = {
  getUserDefaultGear() {
    return fetchGetRequest('profile/default_gear')
  },
  editUserDefaultGear(data) {
    return fetchPutRequest('profile/default_gear', data)
  }
}
