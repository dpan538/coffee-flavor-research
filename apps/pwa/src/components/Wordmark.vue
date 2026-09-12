<script setup lang="ts">
// The wordmark as one SVG: FLAVOR in Stack Sans, WORDS in Fraunces, both fitted to the same width (textLength adjusts
// the letter-spacing), so the two lines always align whatever the fonts' natural widths.
withDefaults(defineProps<{ width?: number; ink?: string; accent?: string }>(), {
  width: 96,
  ink: "#1E1C1A",
  accent: "#7268C9",
});
</script>

<template>
  <svg
    viewBox="0 0 100 52"
    :width="width"
    :height="width * 0.52"
    role="img"
    aria-label="flavorwords"
    data-component="Wordmark"
  >
    <text
      x="0"
      y="24"
      font-size="26"
      font-weight="700"
      textLength="100"
      lengthAdjust="spacing"
      :fill="ink"
      style="
        font-family:
          &quot;Stack Sans&quot;, &quot;MiSans&quot;,
          &quot;Helvetica Neue&quot;, system-ui, sans-serif;
        letter-spacing: -0.01em;
      "
    >
      FLAVOR
    </text>
    <text
      x="0"
      y="50"
      font-size="27"
      font-weight="600"
      textLength="100"
      lengthAdjust="spacing"
      :fill="accent"
      style="
        font-family: &quot;Fraunces&quot;, Georgia, serif;
        font-variation-settings:
          &quot;opsz&quot; 144,
          &quot;SOFT&quot; 60,
          &quot;WONK&quot; 1;
      "
    >
      WORDS
    </text>
  </svg>
</template>
