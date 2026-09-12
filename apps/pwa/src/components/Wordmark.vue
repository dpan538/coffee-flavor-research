<script setup lang="ts">
// The wordmark as one SVG: FLAVOR in Stack Sans, WORDS in Fraunces, both fitted to the same width (textLength adjusts
// the letter-spacing), so the two lines always align whatever the fonts' natural widths.
withDefaults(defineProps<{ width?: number; ink?: string; accent?: string }>(), { width: 96, ink: "#1E1C1A", accent: "#7268C9" });
</script>

<template>
  <svg viewBox="0 0 100 52" :width="width" :height="width * 0.52" role="img" aria-label="flavorwords" data-component="Wordmark">
    <text x="0" y="24" font-size="26" font-weight="700" textLength="100" lengthAdjust="spacing" :fill="ink" style="font-family: 'Stack Sans', 'MiSans', 'Helvetica Neue', system-ui, sans-serif; letter-spacing: -0.01em">FLAVOR</text>
    <text x="0" y="50" font-size="27" font-weight="600" textLength="100" lengthAdjust="spacing" :fill="accent" style="font-family: 'Fraunces', Georgia, serif; font-variation-settings: 'opsz' 144, 'SOFT' 60, 'WONK' 1">WORDS</text>
  </svg>
</template>
