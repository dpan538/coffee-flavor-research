<script setup lang="ts">
// Three bilingual sections + the four citations with locator, licence note and declaration state.
import { X } from "lucide-vue-next";
import { about, aboutOpen, locale } from "../store";
</script>

<template>
  <aside class="fixed inset-0 overflow-y-auto bg-white p-6" role="dialog" aria-modal="true" data-component="AboutDrawer">
    <button type="button" class="border px-2 py-1" aria-label="close" @click="aboutOpen = false"><X :size="18" /></button>
    <article v-for="section in about.sections" :key="section.id" class="space-y-2 mt-6" :data-section="section.id">
      <h2>{{ section.title }}</h2>
      <p v-for="(p, i) in section.paragraphs" :key="i">{{ p }}</p>
      <ul v-if="section.bullets">
        <li v-for="(b, i) in section.bullets" :key="i">{{ b }}</li>
      </ul>
    </article>
    <article class="space-y-2 mt-6" data-section="citations">
      <h2>{{ locale === 'zh-CN' ? '文献引用与许可' : 'Citations and licences' }}</h2>
      <ul>
        <li v-for="c in about.citations" :key="c.id" :data-evidence-state="c.evidenceState">
          <strong>{{ c.title }}</strong> — {{ c.role }}<br />
          <span>{{ c.locator }}</span> · <span>{{ c.licenceNote }}</span> · <span>{{ c.evidenceState }}</span>
        </li>
      </ul>
    </article>
  </aside>
</template>
