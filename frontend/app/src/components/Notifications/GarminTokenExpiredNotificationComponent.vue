<template>
  <router-link
    class="dropdown-item link-body-emphasis text-wrap"
    :to="{ name: 'settings', query: { tab: 'integrations' } }"
  >
    <span
      ><b>{{ $t('garminTokenExpiredNotificationComponent.title') }}</b></span
    >
    <br />
    <span class="fw-lighter">
      {{ $t('garminTokenExpiredNotificationComponent.subTitle') }}
    </span>
  </router-link>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { notifications } from '@/services/notificationsService'

const { t } = useI18n()
const emit = defineEmits(['notificationRead'])
const props = defineProps({
  notification: {
    type: Object,
    required: true
  },
  showDropdown: {
    type: Boolean,
    required: true
  }
})

const dropdownState = computed(() => {
  return props.showDropdown
})

function markNotificationAsRead() {
  if (props.notification.read === false && props.showDropdown === true) {
    notifications.markNotificationAsRead(props.notification.id)
    emit('notificationRead', props.notification.id)
  }
}

watch(dropdownState, markNotificationAsRead, { immediate: false })
</script>
