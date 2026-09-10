<template>
  <section class="option-manager">
    <header class="manager-hero">
      <div>
        <p class="eyebrow">Outline Settings</p>
        <h1>大纲配置</h1>
        <span>管理生成漫剧大纲时可选择的题材和漫剧风格，这部分只走 Java 后端业务接口。</span>
      </div>
      <el-button type="primary" size="large" @click="openCreateDialog">
        新增{{ activeTypeLabel }}
      </el-button>
    </header>

    <el-card class="manager-card" shadow="never">
      <el-tabs v-model="activeType" @tab-change="loadCurrentType">
        <el-tab-pane label="题材" name="GENRE" />
        <el-tab-pane label="漫剧风格" name="STYLE" />
      </el-tabs>

      <el-table
        v-loading="outlineOptionStore.isLoading"
        :data="outlineOptionStore.options"
        class="option-table"
        row-key="id"
      >
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip />
        <el-table-column prop="sortOrder" label="排序" width="90" />
        <el-table-column label="启用" width="120">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              :loading="savingSwitchId === row.id"
              @change="handleToggleEnabled(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" min-width="180" />
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="类型">
          <el-tag type="success">{{ form.type === 'GENRE' ? '题材' : '漫剧风格' }}</el-tag>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model.trim="form.name" maxlength="100" show-word-limit placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            maxlength="500"
            show-word-limit
            placeholder="给团队成员看的说明，可为空"
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortOrder" :min="0" :max="9999" controls-position="right" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="form.enabled" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="outlineOptionStore.isSaving" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { useOutlineOptionStore } from '../stores/outlineOptionStore';
import type { StoryOutlineOption, StoryOutlineOptionRequest, StoryOutlineOptionType } from '../types/outlineOption';

const outlineOptionStore = useOutlineOptionStore();
const activeType = ref<StoryOutlineOptionType>('GENRE');
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const savingSwitchId = ref<number | null>(null);
const formRef = ref<FormInstance>();
const form = reactive<StoryOutlineOptionRequest>({
  type: 'GENRE',
  name: '',
  description: '',
  sortOrder: 0,
  enabled: true,
});
const rules: FormRules<typeof form> = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' },
    { max: 100, message: '名称长度不能超过 100 个字符', trigger: 'blur' },
  ],
  description: [
    { max: 500, message: '说明长度不能超过 500 个字符', trigger: 'blur' },
  ],
};

const activeTypeLabel = computed(() => (activeType.value === 'GENRE' ? '题材' : '漫剧风格'));
const dialogTitle = computed(() => `${editingId.value ? '编辑' : '新增'}${activeTypeLabel.value}`);

onMounted(loadCurrentType);

async function loadCurrentType() {
  await outlineOptionStore.fetchOptions(activeType.value);
}

function openCreateDialog() {
  editingId.value = null;
  resetForm(activeType.value);
  dialogVisible.value = true;
}

function openEditDialog(option: StoryOutlineOption) {
  editingId.value = option.id;
  form.type = option.type;
  form.name = option.name;
  form.description = option.description || '';
  form.sortOrder = option.sortOrder || 0;
  form.enabled = option.enabled;
  dialogVisible.value = true;
}

async function submitForm() {
  if (!formRef.value) {
    return;
  }

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) {
    return;
  }

  const payload: StoryOutlineOptionRequest = {
    type: form.type,
    name: form.name,
    description: form.description || undefined,
    sortOrder: form.sortOrder || 0,
    enabled: form.enabled,
  };

  if (editingId.value) {
    await outlineOptionStore.updateOption(editingId.value, payload);
    ElMessage.success('配置项已更新');
  } else {
    await outlineOptionStore.createOption(payload);
    ElMessage.success('配置项已创建');
  }

  dialogVisible.value = false;
}

async function handleToggleEnabled(option: StoryOutlineOption) {
  savingSwitchId.value = option.id;
  try {
    await outlineOptionStore.updateOption(option.id, {
      type: option.type,
      name: option.name,
      description: option.description || undefined,
      sortOrder: option.sortOrder,
      enabled: option.enabled,
    });
    ElMessage.success(option.enabled ? '已启用' : '已停用');
  } catch (error) {
    option.enabled = !option.enabled;
    throw error;
  } finally {
    savingSwitchId.value = null;
  }
}

async function handleDelete(option: StoryOutlineOption) {
  try {
    await ElMessageBox.confirm(
      `确定删除“${option.name}”吗？已生成的漫剧只保存文本，不会被删除。`,
      '删除配置项',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      },
    );
  } catch {
    return;
  }

  await outlineOptionStore.deleteOption(option.id, option.type);
  ElMessage.success('配置项已删除');
}

function resetForm(type: StoryOutlineOptionType) {
  form.type = type;
  form.name = '';
  form.description = '';
  form.sortOrder = 0;
  form.enabled = true;
  formRef.value?.clearValidate();
}
</script>

<style scoped lang="scss">
.option-manager {
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
    radial-gradient(circle at top right, rgba(249, 115, 22, 0.18), transparent 24rem),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(239, 246, 255, 0.82));
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
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 18px 60px rgba(36, 56, 97, 0.1);
}

.option-table {
  margin-top: 12px;
}

@media (max-width: 720px) {
  .manager-hero {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
