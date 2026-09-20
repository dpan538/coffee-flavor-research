<script setup lang="ts">
// The flavor card — the product object. Three layers: the cup's information (only what was entered), the confirmed
// words as one tight group, the evaluation line (body, bitterness, fermentation, spice: not pick words, owner
// 2026-09-17), the reference entry and the signature. Cream card like a printed tasting card; the motif row at the top
// is the kit's card composition painted with the words' feature colours.
import { computed } from "vue";
import GeoMotif from "./GeoMotif.vue";

const props = withDefaults(
  defineProps<{
    cup: Array<{ label: string; value: string }>;
    words: string[];
    dimensions?: string[];
    evaluation?: Array<{ label: string; text: string }>;
    locale?: "zh-CN" | "en";
    reference?: string;
    brand?: string;
    eyebrow?: string;
    compact?: boolean;
  }>(),
  {
    dimensions: () => [],
    evaluation: () => [],
    locale: "zh-CN",
    reference: "",
    brand: "flavorwords",
    eyebrow: "",
    compact: false,
  },
);

const DIM_COLORS: Record<string, string> = {
  acidity: "#F2C24E",
  sweetness: "#F5B0C6",
  body: "#9B7B5D",
  floral: "#7268C9",
  fruity: "#EE8F70",
  nutty_chocolate: "#B97C4E",
  fermented_winey: "#8C4A4C",
  bitter_roasted: "#1E1C1A",
  spice: "#DA8A80",
  herbal_green: "#6FA85A",
  woody_earthy: "#2F7A4C",
  defect: "#7F90B8",
};
const FALLBACK = ["#7268C9", "#E4724B", "#C9DB6E", "#F2C24E", "#1F3B5C"];
// English words are stored in lower case; on the card each one opens with a capital (owner, 2026-09-19)
const cap = (text: string) =>
  props.locale === "en" ? text.charAt(0).toUpperCase() + text.slice(1) : text;
const colors = computed(() =>
  props.words.map(
    (_, i) =>
      DIM_COLORS[props.dimensions[i] ?? ""] ?? FALLBACK[i % FALLBACK.length]!,
  ),
);
</script>

<template>
  <article
    class="rounded-[22px] bg-cream text-ink"
    :class="compact ? 'px-4 pt-3 pb-2.5' : 'px-5 pt-3.5 pb-3'"
    data-component="FlavorCard"
  >
    <div class="flex items-center justify-between">
      <p
        v-if="eyebrow"
        class="text-[10px] tracking-[0.2em] uppercase text-muted"
      >
        {{ eyebrow }}
      </p>
      <GeoMotif
        class="ml-auto"
        variant="card"
        :size="compact ? 20 : 24"
        :colors="colors"
      />
    </div>
    <dl class="mt-2 space-y-0.5" data-layer="cup">
      <div v-for="row in cup" :key="row.label" class="leader">
        <dt class="text-muted">{{ row.label }}</dt>
        <i />
        <dd class="font-medium normal-case tracking-normal text-[12px]">
          {{ row.value }}
        </dd>
      </div>
    </dl>
    <!-- the words flow in lines, never one per line (owner, 2026-09-19: the card stays near square); each flavor keeps
         to itself — no break inside "Brown sugar" — and opens with a capital, so neighbours never run together -->
    <p
      class="flex flex-wrap items-baseline gap-y-0 font-semibold"
      :class="[
        compact ? 'mt-3' : 'mt-4',
        locale === 'en'
          ? compact
            ? 'text-[18px] leading-[1.2] tracking-tight gap-x-4'
            : 'text-[21px] leading-[1.2] tracking-tight gap-x-5'
          : compact
            ? 'text-[22px] leading-[1.22] gap-x-5'
            : 'text-[27px] leading-[1.22] gap-x-5',
      ]"
      data-layer="words"
    >
      <span v-for="w in words" :key="w" class="whitespace-nowrap">{{
        cap(w)
      }}</span>
    </p>
    <!-- the evaluation rows read like the cup rows above — a label and its value — set as a fine-ruled table of two
         columns, so four rows take two lines (owner, 2026-09-20: the inline run of labels and words had a weak
         hierarchy; then: "not bad, but tighten it, it is too long"). English labels and values (Roast & bitter,
         Dark chocolate) do not fit half a row, so English uses one column of full rows. -->
    <dl
      v-if="evaluation.length"
      class="grid border-t border-ink/15"
      :class="[
        compact ? 'mt-2.5' : 'mt-3',
        locale === 'en' ? 'grid-cols-1' : 'grid-cols-2',
      ]"
      data-layer="evaluation"
    >
      <div
        v-for="(row, i) in evaluation"
        :key="row.label"
        class="min-w-0 flex items-baseline justify-between gap-x-2 border-b border-ink/15"
        :class="[
          locale === 'en'
            ? 'py-[2px]'
            : i % 2 === 0 && i === evaluation.length - 1
              ? 'py-[3px] col-span-2'
              : i % 2 === 0
                ? 'py-[3px] pr-3 border-r'
                : 'py-[3px] pl-3',
        ]"
      >
        <dt
          class="uppercase text-muted"
          :class="
            locale === 'en'
              ? 'text-[10px] tracking-[0.03em]'
              : 'text-[11px] tracking-[0.08em]'
          "
        >
          {{ row.label }}
        </dt>
        <dd class="ml-auto text-[12px] font-medium text-right">
          {{ cap(row.text) }}
        </dd>
      </div>
    </dl>
    <div
      class="flex items-end justify-between pt-2"
      :class="evaluation.length ? 'mt-2.5' : 'mt-5 border-t border-ink/15'"
      data-layer="reference"
    >
      <p class="text-[11px] text-muted">{{ reference }}</p>
      <p class="font-display text-[13px] tracking-tight">{{ brand }}</p>
    </div>
  </article>
</template>
