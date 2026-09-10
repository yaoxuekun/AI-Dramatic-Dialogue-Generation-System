from pydantic import BaseModel, Field
from typing import Optional, List


class PromptParameterItem(BaseModel):
    """Prompt 参数项"""
    direction: str = Field(..., description="参数方向：INPUT 或 OUTPUT", pattern="^(INPUT|OUTPUT)$")
    param_key: str = Field(..., min_length=1, max_length=100, description="参数 key")
    param_name: str = Field(..., min_length=1, max_length=100, description="参数名称")
    data_type: str = Field(..., min_length=1, max_length=50, description="数据类型")
    required_flag: bool = Field(True, description="是否必填")
    description: Optional[str] = Field(None, max_length=1000, description="参数描述")
    example_value: Optional[str] = Field(None, max_length=1000, description="示例值")
    sort_order: int = Field(0, ge=0, description="排序序号")


class PromptCreate(BaseModel):
    """新增 Prompt 的请求体"""
    prompt_key: str = Field(..., min_length=1, max_length=100, description="Prompt 唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="Prompt 名称")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    description: Optional[str] = Field(None, max_length=1000, description="描述")
    template_content: str = Field(..., min_length=1, description="模板内容")
    enabled: bool = Field(True, description="是否启用")
    parameters: List[PromptParameterItem] = Field(default_factory=list, description="参数列表")
    base_prompt_key: Optional[str] = Field(None, max_length=100, description="基础 Prompt Key")
    prompt_scope: Optional[str] = Field(None, max_length=20, description="作用域")
    match_genre: Optional[str] = Field(None, max_length=100, description="匹配题材")
    match_style: Optional[str] = Field(None, max_length=100, description="匹配风格")
    priority: int = Field(0, ge=0, description="优先级")


class PromptUpdate(BaseModel):
    """修改 Prompt 的请求体（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Prompt 名称")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    description: Optional[str] = Field(None, max_length=1000, description="描述")
    template_content: Optional[str] = Field(None, min_length=1, description="模板内容")
    enabled: Optional[bool] = Field(None, description="是否启用")
    parameters: Optional[List[PromptParameterItem]] = Field(None, description="参数列表（整体替换）")
    base_prompt_key: Optional[str] = Field(None, max_length=100, description="基础 Prompt Key")
    prompt_scope: Optional[str] = Field(None, max_length=20, description="作用域")
    match_genre: Optional[str] = Field(None, max_length=100, description="匹配题材")
    match_style: Optional[str] = Field(None, max_length=100, description="匹配风格")
    priority: Optional[int] = Field(None, ge=0, description="优先级")
