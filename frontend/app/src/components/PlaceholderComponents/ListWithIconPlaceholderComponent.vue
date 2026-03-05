<template>
  <ul class="list-group list-group-flush">
    <li
      class="list-group-item d-flex justify-content-between px-0 bg-body-tertiary border border-0"
      v-for="n in numberOfRows"
      :key="n"
    >
      <div class="d-flex align-items-center placeholder-glow w-100">
        <!-- circular avatar placeholder -->
        <span
          class="placeholder bg-secondary rounded-circle flex-shrink-0"
          style="width: 55px; height: 55px"
          aria-hidden="true"
        ></span>
        <div class="ms-3 flex-grow-1">
          <div class="placeholder-glow mb-1">
            <span class="placeholder col-4 bg-secondary rounded"></span>
          </div>
          <div class="placeholder-glow">
            <span class="placeholder col-2 bg-secondary rounded"></span>
          </div>
        </div>
      </div>
    </li>
  </ul>
</template>

<script setup lang="ts">
defineProps<{
  /** Number of rows to display in the placeholder list. */
  numberOfRows: number
}>()
</script>
