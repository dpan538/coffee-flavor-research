<script setup lang="ts">
// The user's own 5 words, then each science line with its evidence state and source (owner: declared at the UI level).
import { computed } from "vue";
import type { ResultCardModel } from "flavor-data/product-vector-v1/view";
import { locale, restart } from "../store";

defineProps<{ model: ResultCardModel }>();
const labels = computed(() => (locale.value === "zh-CN" ? { science: "科学归因", source: "来源", evidence: "证据级别", again: "再诊断一杯", share: "分享文本" } : { science: "Science", source: "Source", evidence: "Evidence", again: "Diagnose another cup", share: "Share text" }));
async function share(text: string) {
  if (typeof navigator === "undefined") return;
  const nav = navigator as Navigator & { share?: (d: { text: string }) => Promise<void> };
  if (typeof nav.share === "function") await nav.share({ text }).catch(() => undefined);
  else if (nav.clipboard) await nav.clipboard.writeText(text).catch(() => undefined);
}
</script>

<template>
  <section class="max-w-md w-full space-y-4" data-component="FinalAttributionCard" :data-corrected="model.corrected">
    <h2>{{ model.title }}</h2>
    <p data-words="picked">{{ model.picked.join(" | ") }}</p>
    <details>
      <summary>{{ labels.science }}</summary>
      <ul class="space-y-2">
        <li v-for="line in model.science" :key="line.citationRef + line.text" :data-evidence-state="line.evidenceState">
          <p>{{ line.text }}</p>
          <p><span>{{ labels.evidence }}：{{ line.evidenceState }}</span> · <span>{{ labels.source }}：{{ line.sourceTitle }}</span></p>
        </li>
      </ul>
    </details>
    <p>{{ model.closing }}</p>
    <div class="flex gap-2">
      <button type="button" class="border px-4 py-2" @click="share(model.shareText)">{{ labels.share }}</button>
      <button type="button" class="border px-4 py-2" @click="restart">{{ labels.again }}</button>
    </div>
  </section>
</template>
