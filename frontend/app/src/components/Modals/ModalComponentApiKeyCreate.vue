<template>
  <div
    ref="modalRef"
    class="modal fade"
    :id="modalId"
    tabindex="-1"
    :aria-labelledby="`${modalId}Title`"
    aria-hidden="true"
    data-bs-backdrop="static"
    data-bs-keyboard="false"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" :id="`${modalId}Title`">{{ title }}</h1>
          <button
            type="button"
            class="btn-close"
            aria-label="Close"
            @click="handleClose"
            :disabled="isLoading"
          ></button>
        </div>
        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            <!-- Key name -->
            <div class="mb-3">
              <label :for="`${modalId}Name`" class="form-label"
                ><b>* {{ nameLabel }}</b></label
              >
              <input
                type="text"
                class="form-control"
                :id="`${modalId}Name`"
                v-model="form.name"
                :placeholder="namePlaceholder"
                maxlength="100"
                required
              />
            </div>

            <!-- Scopes -->
            <div class="mb-3">
              <label class="form-label"
                ><b>* {{ scopesLabel }}</b></label
              >
              <div class="form-check" v-for="scope in availableScopes" :key="scope.value">
                <input
                  class="form-check-input"
                  type="checkbox"
                  :id="`${modalId}Scope${scope.value}`"
                  :value="scope.value"
                  v-model="form.scopes"
                />
                <label
                  class="form-check-label font-monospace"
                  :for="`${modalId}Scope${scope.value}`"
                >
                  {{ scope.value }}
                </label>
              </div>
            </div>

            <!-- Expiry (optional) -->
            <div class="mb-3">
              <label :for="`${modalId}ExpiresAt`" class="form-label">{{ expiryLabel }}</label>
              <input
                type="date"
                class="form-control"
                :id="`${modalId}ExpiresAt`"
                v-model="form.expires_at"
                :min="minDate"
              />
            </div>

            <p>* {{ requiredFieldText }}</p>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              @click="handleClose"
              :disabled="isLoading"
            >
              {{ cancelButtonText }}
            </button>
            <button type="submit" class="btn btn-success" :disabled="isLoading || !isFormValid">
              <span
                v-if="isLoading"
                class="spinner-border spinner-border-sm me-2"
                role="status"
                aria-hidden="true"
              ></span>
              {{ actionButtonText }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useBootstrapModal } from '@/composables/useBootstrapModal'

const props = defineProps({
  modalId: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  nameLabel: {
    type: String,
    required: true
  },
  namePlaceholder: {
    type: String,
    default: ''
  },
  scopesLabel: {
    type: String,
    required: true
  },
  expiryLabel: {
    type: String,
    required: true
  },
  requiredFieldText: {
    type: String,
    required: true
  },
  cancelButtonText: {
    type: String,
    required: true
  },
  actionButtonText: {
    type: String,
    required: true
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{
  submitAction: [{ name: string; scopes: string[]; expires_at: string | null }]
}>()

const { initializeModal, showModal, hideModal, disposeModal } = useBootstrapModal()

const modalRef = ref<HTMLDivElement | null>(null)

const availableScopes = [{ value: 'activities:upload' }]

const form = ref({
  name: '',
  scopes: [] as string[],
  expires_at: ''
})

const minDate = computed(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
})

const isFormValid = computed(() => {
  return form.value.name.trim().length > 0 && form.value.scopes.length > 0
})

/**
 * Resets the form to its initial state.
 *
 * @returns void
 */
const resetForm = (): void => {
  form.value = { name: '', scopes: [], expires_at: '' }
}

/**
 * Hides the modal when the close button is clicked.
 *
 * @returns void
 */
const handleClose = (): void => {
  hideModal()
}

/**
 * Resets form state when the modal is hidden.
 *
 * @returns void
 */
const handleModalHidden = (): void => {
  resetForm()
}

/**
 * Emits form data to the parent on submit.
 *
 * @returns void
 */
const handleSubmit = (): void => {
  if (!isFormValid.value) return
  emit('submitAction', {
    name: form.value.name.trim(),
    scopes: form.value.scopes,
    expires_at: form.value.expires_at || null
  })
}

/**
 * Shows the modal.
 *
 * @returns void
 */
const show = (): void => {
  showModal()
}

/**
 * Hides the modal and resets form state.
 *
 * @returns void
 */
const hide = (): void => {
  hideModal()
  handleModalHidden()
}

onMounted(async () => {
  await initializeModal(modalRef)

  if (modalRef.value) {
    modalRef.value.addEventListener('hidden.bs.modal', handleModalHidden)
  }
})

onUnmounted(() => {
  if (modalRef.value) {
    modalRef.value.removeEventListener('hidden.bs.modal', handleModalHidden)
  }
  disposeModal()
})

defineExpose({ show, hide })
</script>
