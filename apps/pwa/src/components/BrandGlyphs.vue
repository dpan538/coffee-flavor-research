<script setup lang="ts">
// Five brand glyphs — leaf, circle, fan, drop, ring — in the palette. A quiet signature for the home page and About
// (owner: our own icons, not the product pasted on every page).
withDefaults(defineProps<{ size?: number; colors?: string[] }>(), { size: 22, colors: () => ["#7268C9", "#E4724B", "#C9DB6E", "#F2C24E", "#1F3B5C"] });
</script>

<template>
  <svg viewBox="0 0 150 30" :width="size * 5" :height="size" aria-hidden="true" data-component="BrandGlyphs">
    <path d="M2 28 C2 12 14 2 28 2 C28 18 16 28 2 28 Z" :fill="colors[0]" />
    <circle cx="45" cy="15" r="13" :fill="colors[1]" />
    <path d="M62 2 H88 A26 26 0 0 1 62 28 Z" :fill="colors[2]" />
    <path d="M105 2 C112 10 118 16 118 21 A13 13 0 0 1 92 21 C92 16 98 10 105 2 Z" :fill="colors[3]" />
    <circle cx="135" cy="15" r="13" fill="none" :stroke="colors[4]" stroke-width="5" />
  </svg>
</template>
