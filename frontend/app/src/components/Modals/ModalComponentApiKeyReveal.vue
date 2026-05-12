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
        </div>
        <div class="modal-body">
          <!-- Warning Alert -->
          <div class="alert alert-warning d-flex align-items-start" role="alert">
            <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="me-2 mt-1" />
            <div>
              <strong>{{ warningTitle }}</strong>
              <p class="mb-0 mt-1">{{ warningMessage }}</p>
            </div>
          </div>

          <!-- Description -->
          <p>{{ description }}</p>

          <!-- API Key Display -->
          <div class="bg-body-tertiary rounded p-3 mb-3 font-monospace text-break">
            {{ apiKey }}
          </div>

          <!-- Copy Button -->
          <div class="mb-3">
            <button
              type="button"
              class="btn btn-primary"
              @click="copyKey"
              :aria-label="copyButtonText"
            >
              <font-awesome-icon :icon="['fas', 'copy']" class="me-1" />
              {{ copyButtonText }}
            </button>
          </div>

          <!-- Copy Success Message -->
          <div v-if="copySuccess" class="alert alert-success py-2" role="alert">
            <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
            {{ copySuccessMessage }}
          </div>

          <!-- Confirmation Checkbox -->
          <div class="form-check mb-3">
            <input
              class="form-check-input"
              type="checkbox"
              :id="`${modalId}Confirmation`"
              v-model="confirmed"
            />
            <label class="form-check-label" :for="`${modalId}Confirmation`">
              {{ confirmationText }}
            </label>
          </div>

          <!-- Close Button -->
          <div class="d-flex justify-content-end">
            <button
              type="button"
              class="btn btn-primary"
              :disabled="!confirmed"
              @click="handleClose"
              :aria-label="closeButtonText"
            >
              {{ closeButtonText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
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
  description: {
    type: String,
    required: true
  },
  warningTitle: {
    type: String,
    required: true
  },
  warningMessage: {
    type: String,
    required: true
  },
  apiKey: {
    type: String,
    required: true
  },
  copyButtonText: {
    type: String,
    required: true
  },
  copySuccessMessage: {
    type: String,
    required: true
  },
  confirmationText: {
    type: String,
    required: true
  },
  closeButtonText: {
    type: String,
    required: true
  }
})

const emit = defineEmits<{
  closed: []
}>()

const { initializeModal, showModal, hideModal, disposeModal } = useBootstrapModal()

const modalRef = ref<HTMLDivElement | null>(null)
const confirmed = ref(false)
const copySuccess = ref(false)

/**
 * Copies the API key to the clipboard.
 *
 * @returns Promise that resolves when the copy operation is complete.
 */
const copyKey = async (): Promise<void> => {
  try {
    await navigator.clipboard.writeText(props.apiKey)
    copySuccess.value = true
    setTimeout(() => {
      copySuccess.value = false
    }, 3000)
  } catch (error) {
    console.error('Failed to copy API key:', error)
  }
}

/**
 * Handles modal close and emits the closed event.
 *
 * @returns void
 */
const handleClose = (): void => {
  hideModal()
  emit('closed')
}

/**
 * Resets modal state when hidden.
 *
 * @returns void
 */
const handleModalHidden = (): void => {
  confirmed.value = false
  copySuccess.value = false
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
 * Hides the modal and resets state.
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
