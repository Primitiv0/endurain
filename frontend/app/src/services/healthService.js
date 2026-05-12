import { fetchGetRequest } from '@/utils/serviceUtils'

export const health = {
  getUserDailyHealthStats() {
    return fetchGetRequest(`health/stats/daily`)
  }
}
