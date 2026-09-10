<template>
  <section class="prompt-manager">
    <header class="manager-hero">
      <div>
        <p class="eyebrow">Prompt Registry</p>
        <h1>Prompt 管理</h1>
        <span>维护大模型调用的 Prompt 模板、输入参数和输出参数；Python 会按 prompt_key 从 MySQL 读取启用模板。</span>
      </div>
      <el-button type="primary" size="large" @click="openCreateDialog">新增 Prompt</el-button>
    </header>

    <el-card class="manager-card" shadow="never">
      <div class="filter-row">
        <el-input
          v-model.trim="filters.keyword"
          clearable
          placeholder="搜索 prompt_key 或名称"
          @keyup.enter="loadPrompts"
          @clear="loadPrompts"
        />
        <el-select v-model="filters.category" clearable placeholder="分类" @change="loadPrompts">
          <el-option v-for="category in categoryOptions" :key="category" :label="category" :value="category" />
        </el-select>
        <el-select v-model="filters.enabled" clearable placeholder="启用状态" @change="loadPrompts">
          <el-option label="启用" :value="true" />
          <el-option label="停用" :value="false" />
        </el-select>
        <el-button :loading="promptStore.isLoading" @click="loadPrompts">刷新</el-button>
      </div>

      <el-table
        v-loading="promptStore.isLoading"
        :data="promptTree"
        class="prompt-table"
        row-key="id"
        default-expand-all
      >
        <el-table-column prop="promptKey" label="Prompt Key" min-width="220" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <el-tag :type="row.promptScope === 'SPECIFIC' ? 'warning' : 'success'" effect="light">
              {{ row.promptScope === 'SPECIFIC' ? '特定' : '默认' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="basePromptKey" label="基础 Key" min-width="200" />
        <el-table-column prop="promptName" label="名称" min-width="160" />
        <el-table-column prop="category" label="分类" width="150" />
        <el-table-column label="匹配条件" min-width="220">
          <template #default="{ row }">
            <span v-if="row.promptScope === 'SPECIFIC'">
              {{ formatMatchCondition(row) }}
            </span>
            <span v-else class="muted-text">默认兜底</span>
          </template>
        </el-table-column>
        <el-table-column label="参数" width="110">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.parameters?.length || 0 }} 个</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="110">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              :loading="savingSwitchId === row.id"
              @change="toggleEnabled(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" min-width="180" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.promptScope !== 'SPECIFIC'"
              link
              type="success"
              @click="openCreateSpecificDialog(row)"
            >
              新增特定
            </el-button>
            <el-button link type="primary" @click="openEditDialog(row.id)">编辑</el-button>
            <el-button link type="danger" @click="deletePrompt(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="1040px" top="4vh">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid">
          <el-form-item label="Prompt Key" prop="promptKey">
            <el-input v-model.trim="form.promptKey" maxlength="100" show-word-limit placeholder="generate_story_outline" />
          </el-form-item>
          <el-form-item label="Prompt 类型">
            <el-select v-model="form.promptScope" placeholder="请选择类型" @change="handlePromptScopeChange">
              <el-option label="默认 Prompt" value="DEFAULT" />
              <el-option label="特定 Prompt" value="SPECIFIC" />
            </el-select>
          </el-form-item>
          <el-form-item label="基础 Prompt Key">
            <el-select
              v-model.trim="form.basePromptKey"
              :disabled="form.promptScope === 'DEFAULT'"
              placeholder="generate_story_outline"
              filterable
            >
              <el-option
                v-for="prompt in defaultPromptOptions"
                :key="prompt.promptKey"
                :label="`${prompt.promptName}（${prompt.promptKey}）`"
                :value="prompt.promptKey"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="名称" prop="promptName">
            <el-input v-model.trim="form.promptName" maxlength="100" show-word-limit placeholder="生成剧情大纲" />
          </el-form-item>
          <el-form-item label="分类">
            <el-input v-model.trim="form.category" maxlength="50" show-word-limit placeholder="story_outline" />
          </el-form-item>
          <el-form-item label="匹配题材">
            <el-select
              v-model.trim="form.matchGenre"
              :disabled="form.promptScope === 'DEFAULT'"
              clearable
              filterable
              placeholder="科幻"
              :loading="outlineOptionStore.isLoading"
            >
              <el-option
                v-for="option in outlineOptionStore.genreOptions"
                :key="option.id"
                :label="option.name"
                :value="option.name"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="匹配风格">
            <el-select
              v-model.trim="form.matchStyle"
              :disabled="form.promptScope === 'DEFAULT'"
              clearable
              filterable
              placeholder="国漫电影感"
              :loading="outlineOptionStore.isLoading"
            >
              <el-option
                v-for="option in outlineOptionStore.styleOptions"
                :key="option.id"
                :label="option.name"
                :value="option.name"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-input-number v-model="form.priority" :min="0" :max="9999" controls-position="right" />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" />
          </el-form-item>
        </div>

        <el-form-item label="说明" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="Prompt 模板正文" prop="templateContent">
          <el-input
            v-model="form.templateContent"
            class="prompt-editor"
            type="textarea"
            :autosize="{ minRows: 14, maxRows: 24 }"
            placeholder="请使用 {VariableName} 作为 LangChain PromptTemplate 占位符"
          />
        </el-form-item>

        <el-tabs model-value="INPUT" class="param-tabs">
          <el-tab-pane label="输入参数" name="INPUT">
            <ParameterEditor
              :items="inputParameters"
              direction="INPUT"
              @add="addParameter('INPUT')"
              @remove="removeParameter"
            />
          </el-tab-pane>
          <el-tab-pane label="输出参数" name="OUTPUT">
            <ParameterEditor
              :items="outputParameters"
              direction="OUTPUT"
              @add="addParameter('OUTPUT')"
              @remove="removeParameter"
            />
          </el-tab-pane>
        </el-tabs>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="promptStore.isSaving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue';
import { ElButton, ElInput, ElInputNumber, ElMessage, ElMessageBox, ElSwitch, ElTable, ElTableColumn, type FormInstance, type FormRules } from 'element-plus';
import { useOutlineOptionStore } from '../stores/outlineOptionStore';
import { usePromptStore } from '../stores/promptStore';
import type { AiPrompt, AiPromptParameter, AiPromptRequest, PromptParameterDirection } from '../types/prompt';

const promptStore = usePromptStore();
const outlineOptionStore = useOutlineOptionStore();
const formRef = ref<FormInstance>();
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const savingSwitchId = ref<number | null>(null);
const filters = reactive<{
  keyword: string;
  category: string;
  enabled: boolean | undefined;
}>({
  keyword: '',
  category: '',
  enabled: undefined,
});
const form = reactive<AiPromptRequest>({
  promptKey: '',
  promptScope: 'DEFAULT',
  basePromptKey: '',
  matchGenre: '',
  matchStyle: '',
  priority: 0,
  promptName: '',
  category: '',
  description: '',
  templateContent: '',
  enabled: true,
  parameters: [],
});
const rules: FormRules<typeof form> = {
  promptKey: [
    { required: true, message: '请输入 Prompt Key', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_.-]+$/, message: '只能包含字母、数字、下划线、点和短横线', trigger: 'blur' },
  ],
  promptName: [
    { required: true, message: '请输入名称', trigger: 'blur' },
  ],
  templateContent: [
    { required: true, message: '请输入 Prompt 模板正文', trigger: 'blur' },
  ],
};

const dialogTitle = computed(() => (editingId.value ? '编辑 Prompt' : '新增 Prompt'));
const inputParameters = computed(() => form.parameters.filter((item) => item.direction === 'INPUT'));
const outputParameters = computed(() => form.parameters.filter((item) => item.direction === 'OUTPUT'));
const categoryOptions = computed(() => Array.from(new Set(promptStore.prompts.map((item) => item.category).filter(Boolean))) as string[]);
const defaultPromptOptions = computed(() => promptStore.prompts.filter((prompt) => prompt.promptScope !== 'SPECIFIC'));
const promptTree = computed(() => {
  const defaultPrompts = defaultPromptOptions.value.map((prompt) => ({
    ...prompt,
    children: [] as AiPrompt[],
  }));
  const defaultByKey = new Map(defaultPrompts.map((prompt) => [prompt.promptKey, prompt]));
  const orphanSpecificPrompts: AiPrompt[] = [];

  for (const prompt of promptStore.prompts) {
    if (prompt.promptScope !== 'SPECIFIC') {
      continue;
    }
    const parent = defaultByKey.get(prompt.basePromptKey);
    if (parent) {
      parent.children?.push(prompt);
    } else {
      orphanSpecificPrompts.push(prompt);
    }
  }

  return [...defaultPrompts, ...orphanSpecificPrompts];
});

const ParameterEditor = defineComponent({
  props: {
    items: {
      type: Array<AiPromptParameter>,
      required: true,
    },
    direction: {
      type: String,
      required: true,
    },
  },
  emits: ['add', 'remove'],
  setup(props, { emit }) {
    return () => h('div', { class: 'parameter-editor' }, [
      h('div', { class: 'parameter-toolbar' }, [
        h(ElButton, { type: 'primary', plain: true, onClick: () => emit('add') }, () => `新增${props.direction === 'INPUT' ? '输入' : '输出'}参数`),
      ]),
      h(ElTable, { data: props.items, border: true, rowKey: 'sortOrder' }, () => [
        h(ElTableColumn, { label: '参数标识', minWidth: 150 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElInput, { modelValue: row.paramKey, 'onUpdate:modelValue': (value: string) => { row.paramKey = value; }, placeholder: 'Theme / novel_name' }),
        }),
        h(ElTableColumn, { label: '参数名称', minWidth: 140 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElInput, { modelValue: row.paramName, 'onUpdate:modelValue': (value: string) => { row.paramName = value; }, placeholder: '题材 / 小说名字' }),
        }),
        h(ElTableColumn, { label: '类型', width: 150 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElInput, { modelValue: row.dataType, 'onUpdate:modelValue': (value: string) => { row.dataType = value; }, placeholder: 'string' }),
        }),
        h(ElTableColumn, { label: '必填', width: 90 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElSwitch, { modelValue: row.requiredFlag, 'onUpdate:modelValue': (value: string | number | boolean) => { row.requiredFlag = Boolean(value); } }),
        }),
        h(ElTableColumn, { label: '排序', width: 110 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElInputNumber, { modelValue: row.sortOrder, min: 0, controlsPosition: 'right', 'onUpdate:modelValue': (value: number | undefined) => { row.sortOrder = value || 0; } }),
        }),
        h(ElTableColumn, { label: '说明', minWidth: 260 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElInput, { modelValue: row.description, type: 'textarea', autosize: { minRows: 1, maxRows: 3 }, 'onUpdate:modelValue': (value: string) => { row.description = value; }, placeholder: '参数含义、来源、约束' }),
        }),
        h(ElTableColumn, { label: '示例', minWidth: 180 }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElInput, { modelValue: row.exampleValue, 'onUpdate:modelValue': (value: string) => { row.exampleValue = value; }, placeholder: '示例值' }),
        }),
        h(ElTableColumn, { label: '操作', width: 80, fixed: 'right' }, {
          default: ({ row }: { row: AiPromptParameter }) => h(ElButton, { link: true, type: 'danger', onClick: () => emit('remove', row) }, () => '删除'),
        }),
      ]),
    ]);
  },
});

onMounted(async () => {
  await Promise.all([
    loadPrompts(),
    outlineOptionStore.fetchEnabledOptions(),
  ]);
});

async function loadPrompts() {
  await promptStore.fetchPrompts({
    keyword: filters.keyword || undefined,
    category: filters.category || undefined,
    enabled: filters.enabled,
  });
}

function openCreateDialog() {
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openCreateSpecificDialog(parent: AiPrompt) {
  editingId.value = null;
  form.promptKey = `${parent.promptKey}_specific`;
  form.promptScope = 'SPECIFIC';
  form.basePromptKey = parent.promptKey;
  form.matchGenre = '';
  form.matchStyle = '';
  form.priority = 100;
  form.promptName = `${parent.promptName} 特定 Prompt`;
  form.category = parent.category || '';
  form.description = parent.description || '';
  form.templateContent = parent.templateContent;
  form.enabled = true;
  form.parameters = parent.parameters.map((parameter) => ({
    ...parameter,
    id: undefined,
  }));
  formRef.value?.clearValidate();
  dialogVisible.value = true;
}

async function openEditDialog(id: number) {
  const prompt = await promptStore.fetchPrompt(id);
  editingId.value = prompt.id;
  form.promptKey = prompt.promptKey;
  form.promptScope = prompt.promptScope || 'DEFAULT';
  form.basePromptKey = prompt.basePromptKey || prompt.promptKey;
  form.matchGenre = prompt.matchGenre || '';
  form.matchStyle = prompt.matchStyle || '';
  form.priority = prompt.priority || 0;
  form.promptName = prompt.promptName;
  form.category = prompt.category || '';
  form.description = prompt.description || '';
  form.templateContent = prompt.templateContent;
  form.enabled = prompt.enabled;
  form.parameters = prompt.parameters.map((parameter) => ({ ...parameter }));
  dialogVisible.value = true;
}

async function submitForm() {
  if (!formRef.value) {
    return;
  }

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid || !validateParameters()) {
    return;
  }

  const payload = normalizePayload();
  try {
    if (editingId.value) {
      await promptStore.updatePrompt(editingId.value, payload);
      ElMessage.success('Prompt 已更新');
    } else {
      await promptStore.createPrompt(payload);
      ElMessage.success('Prompt 已创建');
    }

    dialogVisible.value = false;
  } catch {
    return;
  }

  try {
    await loadPrompts();
  } catch {
    ElMessage.warning('Prompt 已保存，但刷新列表超时，请稍后点击刷新确认。');
  }
}

async function toggleEnabled(prompt: AiPrompt) {
  savingSwitchId.value = prompt.id;
  try {
    await promptStore.updatePrompt(prompt.id, {
      promptKey: prompt.promptKey,
      promptScope: prompt.promptScope,
      basePromptKey: prompt.basePromptKey,
      matchGenre: prompt.matchGenre || undefined,
      matchStyle: prompt.matchStyle || undefined,
      priority: prompt.priority || 0,
      promptName: prompt.promptName,
      category: prompt.category || undefined,
      description: prompt.description || undefined,
      templateContent: prompt.templateContent,
      enabled: prompt.enabled,
      parameters: prompt.parameters || [],
    });
    ElMessage.success(prompt.enabled ? 'Prompt 已启用' : 'Prompt 已停用');
  } catch (error) {
    prompt.enabled = !prompt.enabled;
    throw error;
  } finally {
    savingSwitchId.value = null;
  }
}

async function deletePrompt(prompt: AiPrompt) {
  try {
    await ElMessageBox.confirm(`确定删除 Prompt“${prompt.promptName}”吗？Python 将无法再从数据库读取该 prompt_key。`, '删除 Prompt', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });
  } catch {
    return;
  }

  await promptStore.deletePrompt(prompt.id);
  ElMessage.success('Prompt 已删除');
}

function addParameter(direction: PromptParameterDirection) {
  form.parameters.push({
    direction,
    paramKey: '',
    paramName: '',
    dataType: 'string',
    requiredFlag: true,
    description: '',
    exampleValue: '',
    sortOrder: form.parameters.filter((item) => item.direction === direction).length * 10 + 10,
  });
}

function removeParameter(parameter: AiPromptParameter) {
  form.parameters = form.parameters.filter((item) => item !== parameter);
}

function validateParameters() {
  if (form.promptScope === 'SPECIFIC' && !form.basePromptKey) {
    ElMessage.warning('特定 Prompt 必须填写基础 Prompt Key');
    return false;
  }
  if (form.promptScope === 'SPECIFIC' && !form.matchGenre && !form.matchStyle) {
    ElMessage.warning('特定 Prompt 至少需要填写匹配题材或匹配风格');
    return false;
  }
  const invalid = form.parameters.find((parameter) => !parameter.paramKey || !parameter.paramName || !parameter.dataType);
  if (invalid) {
    ElMessage.warning('参数标识、参数名称和类型不能为空');
    return false;
  }
  return true;
}

function handlePromptScopeChange() {
  if (form.promptScope === 'DEFAULT') {
    form.basePromptKey = form.promptKey;
    form.matchGenre = '';
    form.matchStyle = '';
    return;
  }

  if (!form.basePromptKey && defaultPromptOptions.value.length > 0) {
    form.basePromptKey = defaultPromptOptions.value[0].promptKey;
  }
}

function normalizePayload(): AiPromptRequest {
  const isDefault = form.promptScope !== 'SPECIFIC';
  return {
    promptKey: form.promptKey,
    promptScope: isDefault ? 'DEFAULT' : 'SPECIFIC',
    basePromptKey: isDefault ? form.promptKey : form.basePromptKey || form.promptKey,
    matchGenre: isDefault ? undefined : form.matchGenre || undefined,
    matchStyle: isDefault ? undefined : form.matchStyle || undefined,
    priority: form.priority || 0,
    promptName: form.promptName,
    category: form.category || undefined,
    description: form.description || undefined,
    templateContent: form.templateContent,
    enabled: form.enabled,
    parameters: form.parameters.map((parameter, index) => ({
      direction: parameter.direction,
      paramKey: parameter.paramKey,
      paramName: parameter.paramName,
      dataType: parameter.dataType,
      requiredFlag: parameter.requiredFlag,
      description: parameter.description || undefined,
      exampleValue: parameter.exampleValue || undefined,
      sortOrder: parameter.sortOrder ?? index * 10,
    })),
  };
}

function resetForm() {
  form.promptKey = '';
  form.promptScope = 'DEFAULT';
  form.basePromptKey = '';
  form.matchGenre = '';
  form.matchStyle = '';
  form.priority = 0;
  form.promptName = '';
  form.category = '';
  form.description = '';
  form.templateContent = '';
  form.enabled = true;
  form.parameters = [];
  formRef.value?.clearValidate();
}

function formatMatchCondition(prompt: AiPrompt) {
  const parts = [];
  if (prompt.matchGenre) {
    parts.push(`题材=${prompt.matchGenre}`);
  }
  if (prompt.matchStyle) {
    parts.push(`风格=${prompt.matchStyle}`);
  }
  return parts.length ? parts.join('，') : '未设置';
}
</script>

<style scoped lang="scss">
.prompt-manager {
  display: grid;
  gap: 18px;
}

.manager-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 28px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(14, 165, 233, 0.2), transparent 24rem),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(240, 253, 250, 0.82));
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.1);
}

.eyebrow {
  margin: 0 0 8px;
  color: #0f766e;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 10px;
  color: #172554;
  font-size: clamp(30px, 5vw, 52px);
}

.manager-hero span {
  color: #64748b;
}

.manager-card {
  border: 0;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 18px 60px rgba(36, 56, 97, 0.1);
}

.filter-row,
.form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.prompt-table {
  margin-top: 16px;
}

.prompt-editor :deep(textarea) {
  font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
  line-height: 1.6;
}

.muted-text {
  color: #94a3b8;
}

.param-tabs {
  margin-top: 12px;
}

.parameter-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

@media (max-width: 900px) {
  .manager-hero {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-row,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
