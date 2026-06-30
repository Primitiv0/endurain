<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Eye, EyeOff, LoaderCircle } from '@lucide/vue'

import AppLogo from '@/components/AppLogo.vue'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ErrorState } from '@/components/ui/error-state'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { usePublicServerSettings } from '@/features/config/composables/usePublicServerSettings'
import { HttpError } from '@/services/http'
import { confirmPasswordReset } from '@/features/auth/services/passwordReset'
import { buildPasswordRequirements, isValidPassword } from '@/utils/validation'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { serverSettings, load } = usePublicServerSettings()

/** Reset token from the emailed link; empty when absent or malformed. */
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))

const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const alert = ref<{ kind: 'error'; message: string } | null>(null)

const passwordRequirements = computed(() =>
  buildPasswordRequirements(
    serverSettings.value.password_type,
    serverSettings.value.password_length_regular_users,
  ),
)

const isPasswordValid = computed(
  () => password.value.length === 0 || isValidPassword(password.value, passwordRequirements.value),
)
const passwordsMatch = computed(
  () => confirmPassword.value.length === 0 || password.value === confirmPassword.value,
)

const canSubmit = computed(
  () =>
    token.value.length > 0 &&
    isValidPassword(password.value, passwordRequirements.value) &&
    password.value === confirmPassword.value,
)

/**
 * Validates the form and confirms the password reset, then redirects to the
 * sign-in page with the appropriate status flag.
 */
async function submitForm(): Promise<void> {
  if (!canSubmit.value || isLoading.value) {
    return
  }

  isLoading.value = true
  alert.value = null

  try {
    await confirmPasswordReset({ token: token.value, new_password: password.value })
    await router.replace({ name: 'login', query: { passwordResetSuccess: 'true' } })
  } catch (error) {
    const message =
      error instanceof HttpError && error.status === 400
        ? t('resetPassword.errorInvalidToken')
        : t('resetPassword.errorGeneral')
    alert.value = { kind: 'error', message }
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="mx-auto w-full max-w-md">
    <div class="rounded-card border border-border bg-card p-6 sm:p-8">
      <ErrorState
        v-if="token.length === 0"
        :title="t('resetPassword.invalidLinkTitle')"
        :description="t('resetPassword.invalidLinkBody')"
      >
        <template #action>
          <Button as-child variant="outline">
            <RouterLink :to="{ name: 'login' }">{{ t('resetPassword.backToLogin') }}</RouterLink>
          </Button>
        </template>
      </ErrorState>

      <form v-else class="flex flex-col" novalidate @submit.prevent="submitForm">
        <AppLogo width="40" height="40" class="mx-auto mb-3 size-10" />
        <h1 class="text-center text-card-heading">
          {{ t('resetPassword.title') }}
        </h1>
        <p class="mt-2 text-center text-body">
          {{ t('resetPassword.subtitle') }}
        </p>

        <Alert v-if="alert" :kind="alert.kind" class="mt-5">
          {{ alert.message }}
        </Alert>

        <div class="mt-5 flex flex-col gap-1.5">
          <Label for="new-password">{{ t('resetPassword.newPassword') }}</Label>
          <div class="relative">
            <Input
              id="new-password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              class="w-full pr-10"
              :aria-invalid="!isPasswordValid"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground"
              :aria-label="
                showPassword ? t('resetPassword.hidePassword') : t('resetPassword.showPassword')
              "
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" class="size-4" aria-hidden="true" />
              <Eye v-else class="size-4" aria-hidden="true" />
            </button>
          </div>
          <p class="text-hint">
            {{ t('resetPassword.passwordHelp', { min: passwordRequirements.minLength }) }}
          </p>
          <p v-if="!isPasswordValid" class="text-field-error">
            {{ t('resetPassword.weakPassword') }}
          </p>
        </div>

        <div class="mt-4 flex flex-col gap-1.5">
          <Label for="confirm-password">{{ t('resetPassword.confirmPassword') }}</Label>
          <Input
            id="confirm-password"
            v-model="confirmPassword"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            class="w-full"
            :aria-invalid="!passwordsMatch"
          />
          <p v-if="!passwordsMatch" class="text-field-error">
            {{ t('resetPassword.mismatch') }}
          </p>
        </div>

        <Button type="submit" class="mt-6" :disabled="!canSubmit || isLoading">
          <LoaderCircle v-if="isLoading" class="size-4 animate-spin" aria-hidden="true" />
          {{ isLoading ? t('resetPassword.submitting') : t('resetPassword.submitButton') }}
        </Button>

        <RouterLink
          :to="{ name: 'login' }"
          class="mt-4 text-center text-meta text-primary hover:underline"
        >
          {{ t('resetPassword.backToLogin') }}
        </RouterLink>
      </form>
    </div>
  </section>
</template>
