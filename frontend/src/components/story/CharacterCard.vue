<template>
  <article class="character-card">
    <div class="avatar">{{ initial }}</div>
    <div class="content">
      <div class="title-row">
        <h3>{{ character.name }}</h3>
        <el-tag v-if="character.role" size="small" effect="plain">{{ character.role }}</el-tag>
      </div>
      <p v-if="character.description">{{ character.description }}</p>
      <p v-if="character.personality" class="personality">性格：{{ character.personality }}</p>
      <dl v-if="appearanceEntries.length > 0">
        <template v-for="[key, value] in appearanceEntries" :key="key">
          <dt>{{ key }}</dt>
          <dd>{{ value }}</dd>
        </template>
      </dl>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { StoryCharacter } from '../../types/story';

const props = defineProps<{
  character: StoryCharacter;
}>();

const initial = computed(() => props.character.name?.slice(0, 1) || '角');

const appearanceEntries = computed(() =>
  Object.entries(props.character.appearance || {}).map(([key, value]) => [key, String(value)]),
);
</script>

<style scoped lang="scss">
.character-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  padding: 18px;
  border: 1px solid rgba(15, 118, 110, 0.14);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 46px rgba(15, 23, 42, 0.08);
}

.avatar {
  display: grid;
  width: 56px;
  height: 56px;
  place-items: center;
  border-radius: 20px;
  color: #fff;
  font-size: 22px;
  font-weight: 900;
  background: linear-gradient(135deg, #1d4ed8, #0f766e);
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

h3 {
  margin: 0;
  color: #172554;
  font-size: 20px;
}

p {
  margin: 10px 0 0;
  color: #475569;
  line-height: 1.7;
}

.personality {
  color: #0f766e;
  font-weight: 700;
}

dl {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px 10px;
  margin: 14px 0 0;
  color: #475569;
  font-size: 13px;
}

dt {
  color: #94a3b8;
  font-weight: 800;
}

dd {
  margin: 0;
}
</style>
