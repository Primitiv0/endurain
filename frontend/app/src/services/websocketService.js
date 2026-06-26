import { fetchPostRequest } from '@/utils/serviceUtils'

export const websocket = {
  fetchTicket() {
    return fetchPostRequest('ws/ticket', null)
  }
}
