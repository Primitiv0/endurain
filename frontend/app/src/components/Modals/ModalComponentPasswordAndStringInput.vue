<template>
  <div
    ref="modalRef"
    class="modal fade"
    :id="modalId"
    tabindex="-1"
    :aria-labelledby="`${modalId}Title`"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" :id="`${modalId}Title`">{{ title }}</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            <p v-if="description">{{ description }}</p>

            <!-- Password field -->
            <label :for="`${modalId}Password`" class="form-label">
              <b>* {{ passwordLabel }}</b>
            </label>
            <div class="position-relative">
              <input
                :id="`${modalId}Password`"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-control"
                :placeholder="passwordPlaceholder || passwordLabel"
                :autocomplete="passwordAutocomplete"
                required
              />
              <button
                type="button"
                class="btn position-absolute top-50 end-0 translate-middle-y"
                @click="togglePasswordVisibility"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
              >
                <font-awesome-icon :icon="showPassword ? ['fas', 'eye-slash'] : ['fas', 'eye']" />
              </button>
            </div>

            <!-- String field -->
            <label :for="`${modalId}String`" class="form-label mt-2">
              <b>* {{ stringLabel }}</b>
            </label>
            <input
              :id="`${modalId}String`"
              v-model="stringValue"
              type="text"
              class="form-control"
              :placeholder="stringPlaceholder || stringLabel"
              :autocomplete="stringAutocomplete"
              required
            />
            <small v-if="stringHint" class="form-text text-muted">{{ stringHint }}</small>

            <p class="mt-2">* {{ requiredFieldText }}</p>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              data-bs-dismiss="modal"
              :aria-label="cancelButtonText"
            >
              {{ cancelButtonText }}
            </button>
            <button
              type="submit"
              class="btn"
              :class="{
                'btn-success': actionButtonType === 'success',
                'btn-danger': actionButtonType === 'danger',
                'btn-warning': actionButtonType === 'warning',
                'btn-primary': actionButtonType === 'primary'
              }"
              :disabled="!password || !stringValue || isLoading"
              :aria-label="actionButtonText"
            >
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
// Vue composition API
import { ref, onMounted, onUnmounted, type PropType } from 'vue'
// Composables
import { useBootstrapModal } from '@/composables/useBootstrapModal'
// Types
import type { ActionButtonType } from '@/types'

defineProps({
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
    default: ''
  },
  passwordLabel: {
    type: String,
    required: true
  },
  passwordPlaceholder: {
    type: String,
    default: ''
  },
  passwordAutocomplete: {
    type: String,
    default: 'current-password'
  },
  stringLabel: {
    type: String,
    required: true
  },
  stringPlaceholder: {
    type: String,
    default: ''
  },
  stringHint: {
    type: String,
    default: ''
  },
  stringAutocomplete: {
    type: String,
    default: 'off'
  },
  requiredFieldText: {
    type: String,
    required: true
  },
  cancelButtonText: {
    type: String,
    required: true
  },
  actionButtonType: {
    type: String as PropType<ActionButtonType>,
    required: true,
    validator: (value: string) => ['success', 'danger', 'warning', 'primary'].includes(value)
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
  submitAction: [{ password: string; stringValue: string }]
}>()

const { initializeModal, showModal, hideModal, disposeModal } = useBootstrapModal()

const modalRef = ref<HTMLDivElement | null>(null)
const password = ref('')
const stringValue = ref('')
const showPassword = ref(false)

const togglePasswordVisibility = (): void => {
  showPassword.value = !showPassword.value
}

const resetForm = (): void => {
  password.value = ''
  stringValue.value = ''
  showPassword.value = false
}

const handleModalHidden = (): void => {
  resetForm()
}

const handleSubmit = (): void => {
  if (password.value && stringValue.value) {
    emit('submitAction', {
      password: password.value,
      stringValue: stringValue.value
    })
  }
}

const show = (): void => {
  showModal()
}

const hide = (): void => {
  hideModal()
  resetForm()
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

defineExpose({
  show,
  hide
})
</script>
