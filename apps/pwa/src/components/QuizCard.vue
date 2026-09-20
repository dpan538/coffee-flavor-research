<script setup lang="ts">
// The question at the top (owner: no blank above it), the options filling the rest as equal bands. Tap → highlight → fold.
// The progress segments are the way back (owner, 2026-09-18): an answered segment opens that question for editing and
// the other answers are kept and replayed afterwards — no dialog. Each thin bar sits inside a 44 px-tall hit box
// about 40 px wide, so a finger can hit it without the row growing. The option chosen last time is marked.
// Five things to tap at most (owner, 2026-09-20): most questions show four options, and "I can't say" ("这一项很难形容")
// is the fifth of them, an option like the others — not a sixth line under five options.
import { computed, ref } from "vue";
import type { QuizCardModel } from "flavor-data/product-vector-v1/view";
import {
  editSlot,
  keptAnswers,
  locale,
  pick,
  progressSegments,
  resumeEditing,
} from "../store";
import type { ProgressSegment } from "../store";

const props = defineProps<{ model: QuizCardModel }>();
const selected = ref<string | null>(null);

const previous = computed(() => keptAnswers.value[props.model.slot]);
const tappable = computed(() => [
  ...props.model.options,
  ...(props.model.unanswered ? [props.model.unanswered] : []),
]);
const segmentLabel = (i: number) =>
  locale.value === "zh-CN" ? `修改第 ${i} 题` : `Change question ${i}`;
const frontierLabel = (segment: ProgressSegment, n: number) =>
  locale.value === "zh-CN"
    ? segment.delivers
      ? "回到风味描述，答案不变"
      : `回到第 ${n} 题，其余答案不变`
    : segment.delivers
      ? "Back to the description, answers unchanged"
      : `Back to question ${n}, other answers unchanged`;
function tap(segment: ProgressSegment) {
  if (selected.value) return;
  if (segment.state === "frontier") resumeEditing();
  else if (segment.slot) editSlot(segment.slot);
}

async function choose(option: string, label: string) {
  if (selected.value) return;
  selected.value = option;
  await pick(props.model.slot, option, label, props.model.prompt);
}
</script>

<template>
  <section
    class="h-full flex flex-col"
    data-component="QuizCard"
    :data-slot="model.slot"
  >
    <div class="shrink-0 px-6 pt-6 flex flex-col gap-3">
      <div
        class="flex items-center justify-between text-xs tracking-widest opacity-70"
      >
        <span>{{ locale === "zh-CN" ? "这一口" : "This cup" }}</span>
        <span
          class="flex flex-1 justify-end max-w-[240px] ml-4"
          role="group"
          :aria-label="
            locale === 'zh-CN'
              ? '答题进度：点已答的题可返回修改'
              : 'Progress: tap an answered question to change it'
          "
          data-progress
        >
          <button
            v-for="(segment, i) in progressSegments"
            :key="i"
            type="button"
            class="seg"
            :disabled="
              segment.state === 'current' || segment.state === 'future'
            "
            :aria-current="segment.state === 'current' ? 'step' : undefined"
            :aria-label="
              segment.state === 'frontier'
                ? frontierLabel(segment, i + 1)
                : segmentLabel(i + 1)
            "
            :data-state="segment.state"
            @click="tap(segment)"
          >
            <!-- the way back to the description is not a seventh question: a dot, not a bar (owner, 2026-09-20) -->
            <span
              v-if="segment.state === 'frontier' && segment.delivers"
              class="mx-auto block h-[7px] w-[7px] rounded-full bg-current opacity-55 transition-transform duration-150"
              data-end
            />
            <span
              v-else
              class="block h-1 w-full rounded-full transition-transform duration-150"
              :class="
                segment.state === 'future'
                  ? 'bg-current opacity-25'
                  : segment.state === 'frontier'
                    ? 'bg-current opacity-55'
                    : 'bg-current'
              "
            />
          </button>
        </span>
      </div>
      <h2
        class="text-[32px] [@media(max-height:739px)]:text-[26px] rise"
        :class="locale === 'zh-CN' ? 'display-zh' : 'display-en'"
      >
        {{ model.prompt }}
      </h2>
    </div>
    <ul
      class="flex-1 min-h-0 px-4 pt-5 pb-4 flex flex-col gap-2.5 [@media(max-height:739px)]:pt-3 [@media(max-height:739px)]:gap-2"
    >
      <li
        v-for="option in tappable"
        :key="option.option"
        class="flex-1 min-h-[54px] max-h-[104px] flex rise"
      >
        <button
          type="button"
          class="option flex-1 flex items-center"
          :class="{
            'option-prev': previous === option.option && !selected,
          }"
          :aria-pressed="selected === option.option"
          :data-previous="previous === option.option || undefined"
          :data-unanswered="
            option.option === model.unanswered?.option || undefined
          "
          @click="choose(option.option, option.label)"
        >
          <span>{{ option.label }}</span>
          <span
            v-if="previous === option.option && !selected"
            class="ml-auto pl-3 shrink-0 text-xs opacity-60"
            >{{ locale === "zh-CN" ? "上次选的" : "your last pick" }}</span
          >
        </button>
      </li>
    </ul>
  </section>
</template>
