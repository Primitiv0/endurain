<template>
  <ul class="my-3 list-group list-group-flush">
    <li
      class="list-group-item mb-3 p-0 bg-body-tertiary border border-0"
      v-for="n in numberOfRows"
      :key="n"
    >
      <div class="fw-bold placeholder-glow">
        <span class="placeholder col-6 bg-secondary rounded"></span>
      </div>
      <div class="placeholder-glow">
        <span class="placeholder col-3 bg-secondary rounded"></span>
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
