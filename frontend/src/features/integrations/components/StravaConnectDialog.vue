<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { StravaClientInput } from '@/features/integrations/types'

import { FormDialog } from '@/components/ui/form-dialog'
import { Input } from '@/components/ui/input'
import { inputFieldClass } from '@/components/ui/input/fieldClasses'
import { Label } from '@/components/ui/label'

const open = defineModel<boolean>('open', { required: true })

defineProps<{
  /** Whether the connect flow is in flight (state + client + redirect). */
  pending: boolean
}>()

const emit = defineEmits<{
  submit: [input: StravaClientInput]
}>()

const { t } = useI18n()

const clientId = ref('')
const clientSecret = ref('')

const canSubmit = computed(
  () =>
    clientId.value.trim().length > 0 &&
    Number.isFinite(Number(clientId.value)) &&
    clientSecret.value.length > 0,
)

watch(open, (isOpen) => {
  if (isOpen) {
    clientId.value = ''
    clientSecret.value = ''
  }
})

function onSubmit(): void {
  emit('submit', { clientId: Number(clientId.value), clientSecret: clientSecret.value })
}
</script>

<template>
  <FormDialog
    v-model:open="open"
    :title="t('settings.integrations.strava.connectTitle')"
    :description="t('settings.integrations.strava.connectDescription')"
    :submit-label="t('settings.integrations.strava.connect')"
    :cancel-label="t('settings.integrations.cancel')"
    :close-label="t('settings.integrations.close')"
    :submitting="pending"
    :can-submit="canSubmit"
    @submit="onSubmit"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1.5">
        <Label for="strava-client-id">{{ t('settings.integrations.strava.clientId') }}</Label>
        <input
          id="strava-client-id"
          v-model="clientId"
          type="number"
          inputmode="numeric"
          :placeholder="t('settings.integrations.strava.clientIdPlaceholder')"
          :disabled="pending"
          :class="inputFieldClass"
        />
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="strava-client-secret">
          {{ t('settings.integrations.strava.clientSecret') }}
        </Label>
        <Input
          id="strava-client-secret"
          v-model="clientSecret"
          type="password"
          autocomplete="off"
          :disabled="pending"
          class="w-full"
          :placeholder="t('settings.integrations.strava.clientSecret')"
        />
      </div>

      <p class="text-hint">{{ t('settings.integrations.strava.connectHint') }}</p>
    </div>
  </FormDialog>
</template>
