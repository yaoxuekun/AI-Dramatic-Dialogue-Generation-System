USE springcloud;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS ai_prompts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prompt_key VARCHAR(100) NOT NULL,
    base_prompt_key VARCHAR(100) NOT NULL DEFAULT '',
    prompt_scope VARCHAR(20) NOT NULL DEFAULT 'DEFAULT',
    match_genre VARCHAR(100),
    match_style VARCHAR(100),
    priority INT NOT NULL DEFAULT 0,
    prompt_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    description VARCHAR(1000),
    template_content LONGTEXT NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_prompts_key (prompt_key),
    KEY idx_ai_prompts_category (category),
    KEY idx_ai_prompts_enabled (enabled),
    KEY idx_ai_prompts_base_scope (base_prompt_key, prompt_scope, enabled),
    KEY idx_ai_prompts_match (base_prompt_key, match_genre, match_style)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_prompt_parameters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prompt_id BIGINT NOT NULL,
    direction VARCHAR(20) NOT NULL,
    param_key VARCHAR(100) NOT NULL,
    param_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    required_flag TINYINT(1) NOT NULL DEFAULT 1,
    description VARCHAR(1000),
    example_value VARCHAR(1000),
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_prompt_param (prompt_id, direction, param_key),
    KEY idx_ai_prompt_parameters_prompt_id (prompt_id),
    KEY idx_ai_prompt_parameters_direction (direction),
    CONSTRAINT fk_ai_prompt_parameters_prompt
        FOREIGN KEY (prompt_id) REFERENCES ai_prompts(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_story_outline', '生成剧情大纲', 'story_outline', '根据题材、漫剧风格和可选剧情生成小说名、故事摘要、完整大纲和主要角色设定。', '
你是一位资深的小说编辑与剧情架构师，拥有15年网络文学与出版小说编辑经验，擅长构建世界观、设计人物弧光、铺设悬念与伏笔。你熟悉玄幻、仙侠、科幻、都市、悬疑、历史、言情、末日、无限流等所有主流网文题材的创作规律。

根据用户提供的题材和部分剧情，生成一段结构完整、逻辑自洽、具有戏剧张力与商业潜力的长篇小说剧情大纲。

- 题材：{Theme}
- 用户设定的漫剧视觉风格：{StoryStyle}
- 部分剧情（选填）：{Plot}


一、基础设定（200-400字）
1. 世界观架构：时代背景、核心规则、力量体系/科技水平、社会结构
2. 核心冲突源：推动整部小说的根本矛盾（如资源枯竭、阶级对立、天道崩塌、外星入侵等）

二、主角设定（150-300字）
- 姓名/代号、年龄、身份起点
- 核心欲望：主角最深层的目标
- 致命弱点：性格缺陷或能力盲区
- 人物弧光：从开篇到结局的转变轨迹

三、主线剧情（800-1500字）
采用反转螺旋结构、阶梯式升级结构、多线并行交汇结构（网状引爆）、循环/莫比乌斯结构（时间陷阱）等结构中的一个或多个组合

四、分卷/分阶段大纲（每卷100-200字）
根据题材特性，规划5-20卷，每卷标明：
- 卷名与核心事件
- 本卷BOSS或主要对手
- 主角本卷的成长收获

五、关键配角群像（3-5人，每人50-100字）
例如：
- 导师型：给予主角关键帮助但可能牺牲或背叛
- 挚友/恋人型：与主角有情感羁绊，可能立场对立
- 宿敌型：与主角理念冲突，后期可能合作或彻底黑化
- 幕后黑手型：前期伪装盟友，后期揭露真实目的
- 喜剧调剂型：提供轻松氛围，关键时刻爆发高光

六、核心卖点与差异化（100-200字）
- 题材融合的创新点
- 情绪价值（爽点、虐点、燃点、泪点分布）
- 对标作品与差异化优势


创作原则
1. 反套路：避免陈词滥调，在经典框架中加入颠覆性设定
2. 强钩子：每卷结尾必须留下强悬念
3. 情感锚点：确保至少有一个让读者强烈共情的人物关系
4. 逻辑自洽：力量体系/规则设定必须前后一致，无硬伤
5. 商业性：节奏明快，200万字内保持张力，适合连载
6. 风格兼容：故事气质、核心场景和角色外观应兼容用户设定的漫剧视觉风格，便于后续图片与视频生成保持统一。

执行指令
请严格按上述格式输出。如果用户提供了"部分剧情"，请将其无缝融入大纲并补全前后逻辑；如果未提供，则基于题材自行创作最具潜力的剧情方向。确保大纲足够详细，作者可直接据此开始写作。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Theme', '题材', 'string', 1, '用户选择或输入的漫剧大纲题材，例如科幻、悬疑、都市。', '科幻', 10
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StoryStyle', '漫剧风格', 'string', 0, '用户设定的统一视觉风格，会影响后续图片和视频生成。', '国漫电影感', 20
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Plot', '大致剧情', 'string', 0, '用户可选输入的故事雏形；为空时由模型根据题材自行创作。', '主角在未来城市中意外获得读心能力。', 30
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'novel_name', '小说名字', 'string', 1, '模型生成的小说/漫剧名称，对应 novelName。', '记忆霓虹', 40
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'story_summary', '故事摘要', 'string', 1, '故事摘要，对应 storySummary。', '...', 50
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'outline', '大纲', 'string', 1, '完整剧情大纲，包含世界观、主线、阶段和关键冲突。', '一、基础设定...', 60
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'main_characters', '主要角色设定', 'array<MainCharacterSetting>', 1, '主要角色列表，每项包含 name、role、description、personality、appearance。', '[{"name":"林浩","role":"主角"}]', 70
FROM ai_prompts WHERE prompt_key = 'generate_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('revise_story_outline', '修改剧情大纲', 'story_outline', '根据原始故事信息和用户修改意见，自动重写剧情大纲、摘要和角色设定。', '
你是一位资深的小说编辑与剧情架构师，拥有15年网络文学与出版小说编辑经验，擅长诊断剧情漏洞、重构叙事节奏、优化人物弧光与悬念铺设。你熟悉玄幻、仙侠、科幻、都市、悬疑、历史、言情、末日、无限流等所有主流网文题材的创作规律。

根据用户提供的原有剧情大纲和修改意见，输出一份修改后的完整剧情大纲。你必须严格遵循"最小干预原则"：只修改用户明确要求的部分，未提及的内容保持原样。

- 原有剧情大纲：{OriginalOutline}
- 修改意见：{RevisionNotes}

输出示例：
一、基础设定（200-400字）
1. 世界观架构：时代背景、核心规则、力量体系/科技水平、社会结构
2. 核心冲突源：推动整部小说的根本矛盾（如资源枯竭、阶级对立、天道崩塌、外星入侵等）

二、主角设定（150-300字）
- 姓名/代号、年龄、身份起点
- 核心欲望：主角最深层的目标
- 致命弱点：性格缺陷或能力盲区
- 人物弧光：从开篇到结局的转变轨迹

三、主线剧情（800-1500字）
采用反转螺旋结构、阶梯式升级结构、多线并行交汇结构（网状引爆）、循环/莫比乌斯结构（时间陷阱）等结构中的一个或多个组合

四、分卷/分阶段大纲（每卷100-200字）
根据题材特性，规划5-20卷，每卷标明：
- 卷名与核心事件
- 本卷BOSS或主要对手
- 主角本卷的成长收获

五、关键配角群像（3-5人，每人50-100字）
例如：
- 导师型：给予主角关键帮助但可能牺牲或背叛
- 挚友/恋人型：与主角有情感羁绊，可能立场对立
- 宿敌型：与主角理念冲突，后期可能合作或彻底黑化
- 幕后黑手型：前期伪装盟友，后期揭露真实目的
- 喜剧调剂型：提供轻松氛围，关键时刻爆发高光

六、核心卖点与差异化（100-200字）
- 题材融合的创新点
- 情绪价值（爽点、虐点、燃点、泪点分布）
- 对标作品与差异化优势


修改原则：
1. 最小干预：未要求修改的部分一字不改，保持原有精华
2. 无缝衔接：新增或调整的情节必须与原有设定严丝合缝，不得产生新漏洞
3. 因果自洽：任何改动必须有充分的前因后果，人物动机必须充分且连贯
4. 风格统一：新增内容在叙事 tone、语言风格、信息密度上与原文完全一致
5. 商业性守恒：修改不得破坏原大纲的市场卖点与连载节奏，若用户修改意见存在风险，需在"连锁影响分析"中明确指出
6. 结构完整：输出必须是一份作者可直接据此开始写作的完整大纲，而非仅列出差异的补丁文档

执行指令
请严格按上述格式输出。如果用户的修改意见与原有设定存在冲突，优先执行修改意见，但必须在"连锁影响分析"中标注冲突点及你的解决方案。确保修改后的大纲逻辑闭环、节奏稳健、可直接投入创作。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'OriginalOutline', '原始大纲', 'string', 1, '由标题、故事摘要和现有剧情大纲拼接出的原始故事上下文。', '书名：...\n故事摘要：...\n剧情大纲：...', 10
FROM ai_prompts WHERE prompt_key = 'revise_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'RevisionNotes', '修改意见', 'string', 1, '用户对剧情大纲的修改要求。', '把主角改成女性，并增加悬疑线。', 20
FROM ai_prompts WHERE prompt_key = 'revise_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'story_summary', '故事摘要', 'string', 1, '故事摘要，对应 storySummary。', '...', 30
FROM ai_prompts WHERE prompt_key = 'revise_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'outline', '大纲', 'string', 1, '完整剧情大纲，包含世界观、主线、阶段和关键冲突。', '一、基础设定...', 40
FROM ai_prompts WHERE prompt_key = 'revise_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'main_characters', '主要角色设定', 'array<MainCharacterSetting>', 1, '主要角色列表，每项包含 name、role、description、personality、appearance。', '[{"name":"林浩","role":"主角"}]', 50
FROM ai_prompts WHERE prompt_key = 'revise_story_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_volume_count', '判断分卷数量', 'volume_outline', '使用温度为 0 的模型判断故事适合拆成多少个分卷。', '
你是一位长篇网文结构编辑，负责在生成分卷大纲前判断故事应该拆成多少个分卷。

请只根据以下信息判断总分卷数：

- 书名：{Title}
- 故事摘要：{StorySummary}
- 主线大纲：{Outline}
- 主要人物：{Characters}

判断原则：
1. 必须选择 5 到 20 之间的整数。
2. 如果故事主线跨度较小、冲突集中，选择 5-8 卷。
3. 如果故事有明显多阶段升级、多地图、多势力、多人物支线，选择 9-15 卷。
4. 如果故事存在超长线世界观、多层级力量体系、跨时代/跨世界阴谋，选择 16-20 卷。
5. 数量要服务于剧情密度，不要为了拉长而机械拆分。
6. 输出会被结构化模型约束，请确保 volume_count 是最终分卷总数。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'generate_volume_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 20
FROM ai_prompts WHERE prompt_key = 'generate_volume_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 30
FROM ai_prompts WHERE prompt_key = 'generate_volume_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 40
FROM ai_prompts WHERE prompt_key = 'generate_volume_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'volume_count', '分卷数量', 'integer', 1, '推荐分卷总数，范围 5-20。', '8', 50
FROM ai_prompts WHERE prompt_key = 'generate_volume_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_volume_outline_single', '逐卷生成分卷大纲', 'volume_outline', '参考故事总大纲和前序分卷，逐卷生成连续一致的分卷大纲。', '
你是一位资深长篇网文编辑与分卷架构师。现在不要一次性输出所有分卷，只生成当前指定的一卷。

你的目标是让每一卷既有独立完整的阶段目标，又能与前后卷严密衔接。生成当前卷时，必须同时参考故事总大纲和已经生成的前序分卷大纲，确保因果、人物成长、伏笔、战力层级、势力关系、情感关系前后一致。

一、全局输入

- 书名：{Title}
- 故事摘要：{StorySummary}
- 主线总大纲：{Outline}
- 主要人物设定：{Characters}
- 总分卷数：{TotalVolumes}
- 当前要生成的卷号：{CurrentVolumeNumber}

二、已经生成的前序分卷

{GeneratedVolumeOutlines}

如果“已经生成的前序分卷”为“暂无”，说明当前是第一卷。第一卷要负责建立世界观、主角核心欲望、初始冲突和长期伏笔；非第一卷必须承接前一卷卷末钩子，不能忽略前序卷已经发生的事件。

三、当前卷生成要求

1. 当前卷必须严格对应“第 {CurrentVolumeNumber} 卷 / 共 {TotalVolumes} 卷”的叙事位置。
2. 必须承接前序分卷中的未解决危机、伏笔、人物关系变化和代价。
3. 必须根据总大纲推进整体主线，不能偏离故事核心方向。
4. 必须为后续分卷留下明确的即时危机、中期压力或长期伏笔。
5. 禁止重复前序分卷已经完成的核心事件，除非是以反噬、误判、真相反转的方式重新激活。
6. 禁止战力跳级、人物动机突变、设定吃书、伏笔断裂。
7. 当前卷内容要尽可能详细，包含主线节拍、至少两条支线、暗线推进、势力互动、信息差、反转、情感钩子、人物成长和卷末悬念。

四、当前卷内容结构

请在 content 中写出完整详细的大纲，至少包含：

- 【卷首定位】：主题、叙事目标、核心冲突、主要对手/压力源、胜利悖论
- 【超密度情节骨架】：主线节拍 8-12 个；支线 A/B 各 4-6 个节拍；暗线推进；势力互动；信息差与误会；至少 2 个反转；至少 3 个情感钩子
- 【人物成长弧线】：主角变化、关键抉择、配角高光、关系演变、新角色引入
- 【世界观与设定展开】：新地图/新层级、力量体系颗粒化、历史纵深、关键道具或血脉源流、伏笔铺设
- 【节奏与结构控制】：张弛分布、信息释放节奏、代价与反噬累积
- 【卷末衔接与下卷预告】：即时危机、中期压力、长期伏笔、人物位移

五、输出边界

你只输出当前这一卷，不要输出其他卷。卷号必须是 {CurrentVolumeNumber}。卷名要有商业吸引力；summary 要概括本卷核心矛盾；endingHook 要能自然推动下一卷。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 20
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 30
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 40
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'TotalVolumes', '总分卷数', 'integer', 1, '第一阶段规划出的总卷数。', '8', 50
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'CurrentVolumeNumber', '当前卷号', 'integer', 1, '当前正在生成的卷号，从 1 开始。', '1', 60
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'GeneratedVolumeOutlines', '已生成分卷', 'string', 0, '前序分卷上下文，用于保证连续性。', '第1卷：...', 70
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'volumeNumber', '卷号', 'integer', 1, '当前分卷编号，从 1 开始。', '1', 80
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'title', '标题', 'string', 1, '生成结果标题，可表示卷标题或小节标题。', '暗夜启明', 90
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'summary', '摘要', 'string', 1, '生成结果摘要，可表示分卷摘要或小节摘要。', '...', 100
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'content', '详细内容', 'string', 1, '生成的详细大纲或小节故事细节。', '...', 110
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'endingHook', '结尾钩子', 'string', 1, '卷末或小节末尾的悬念钩子。', '...', 120
FROM ai_prompts WHERE prompt_key = 'generate_volume_outline_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('revise_volume_outline', '自动修改分卷大纲', 'volume_outline', '根据现有分卷大纲和用户修改意见，自动重写分卷结构。', '
你是一位资深网络小说编辑与故事架构修复专家，擅长诊断长篇连载大纲的结构性病灶，并进行外科手术式的精准修改。你的任务是根据作者提供的现有分卷大纲、修改需求及故事基础设定，输出一份修复后的详尽分卷大纲。

---

一、核心任务：诊断 → 拆解 → 重建

收到大纲后，你必须先执行【诊断扫描】，再进入【修改重建】。禁止直接重写而忽略原有骨架。

【诊断扫描】（内部思考过程，不输出，但用于指导修改）
1. 结构断层扫描：检查卷与卷之间是否存在"跳崖式"剧情跳跃、战力跳级、人设突变。
2. 支线孤立指数：检查支线是否与主线在关键节点交汇，配角是否沦为工具人。
3. 暗线剥洋葱节奏：检查悬疑揭露是否过快（一次性说透）或过慢（读者已猜中）。
4. 势力博弈复杂度：检查是否只有主角与反派两方对打，缺少第三方、第四方搅局。
5. 情感债务累积：检查主角获得帮助/击败敌人后，是否欠下跨卷延续的因果。
6. 代价延迟机制：检查主角的底牌、捷径、外力借用，是否在后续1-3卷内产生反噬。
7. 信息差与误会：检查是否有因信息不对等导致的重大决策偏差，且后果是否跨卷延续。
8. 节奏张弛分布：检查是否存在连续3个以上节拍全是高张力动作戏（疲劳）或全是铺垫（拖沓）。
9. 胜利悖论缺失：检查每卷结尾是否只解决旧问题而没有触发更大新问题。
10. 地图/层级解锁逻辑：检查新地图开启是否有足够的铺垫和"旧强者变底层"的落差感。

---

二、修改策略（根据诊断结果选择适用策略）

【结构修复】
- 跳崖修复：若卷与卷之间剧情断裂，插入"过渡卷"或在卷末增加"四重衔接点"（即时危机、中期压力、长期伏笔、人物位移）。
- 战力崩坏修复：将"顿悟跳级"拆解为"资源收集→瓶颈突破→巩固代价→实战验证"四阶段，分散到2-3卷完成。
- 人设修复：若角色行为逻辑矛盾，补充"隐藏动机"或"外部胁迫"，使其选择合理化；若角色扁平，增加"道德困境二选一"或"秘密身份"。

【支线并网】
- 孤立支线修复：为每条独立支线设计至少1个与主线"资源交换"或"立场冲突"的节点。支线人物的目标必须与主角目标产生"合作时互相猜忌，对抗时互相依赖"的张力。
- 工具人修复：给每个配角增加"独立动机+情感线+成长弧线+个人秘密"，使其在支线中有4-6个独立节拍。

【暗线重塑】
- 过快修复：将已揭露的真相拆分为"碎片化线索"，分散到不同角色的视角中；已说透的部分改为"部分真相+更深误导"。
- 过慢修复：在本卷增加1个"伪真相"误导读者，同时抛出1个与主线直接相关的暗线线索，提升紧迫感。

【势力重构】
- 两方对打修复：引入第三方势力（中立仲裁者、野心家、历史遗留势力），设计"因第三方威胁而被迫联手"或"临时合作下的背叛隐患"情节。
- 博弈深度修复：为每方势力设计"表面诉求"与"真实诉求"的差异，增加谈判、交易、双面间谍情节。

【情感与代价植入】
- 债务缺失修复：主角每获得一份重要帮助，必须签下"不平等契约"或欠下"人情债"；每击败一个敌人，必须面对其背后关系网的报复。
- 代价延迟修复：为主角本卷使用的每一个"底牌/捷径/外力"，在后续1-3卷内预设具体反噬事件（如：燃烧寿命→某卷濒死；借用邪力→心性侵蚀；假死→挚爱绝望出走）。

【节奏校准】
- 过紧修复：在高张力动作戏之间插入"信息整合"或"情感缓冲"节拍（如：疗伤时的对话揭露秘密、庆功宴上的暗流涌动）。
- 过松修复：将连续铺垫压缩，插入"突发事件"打断日常，或在铺垫中嵌入"倒计时压力"（如：敌人正在逼近，必须在X日内完成）。

【胜利悖论植入】
- 若某卷结局过于圆满：追加"解决旧问题的同时触发了更大问题"——可以是新敌人被惊醒、旧盟友因利益反目、主角获得的力量自带诅咒、真相揭露后发现自己是棋子。

---

三、修改输入信息

- 书名：{Title}
- 故事梗概：{StorySummary}
- 主线大纲：{Outline}
- 主要人物：{Characters}
- 现有分卷大纲：{ExistingVolumeOutline}
- 修改意见：{ModificationRequest}（作者明确指出的问题，如："第三卷节奏太慢"、"主角升级太快"、"支线B与主线脱节"等）

---

四、输出格式要求

对每一卷（或指定修改卷），必须按以下结构输出：

【第 X 卷：卷名】（若修改卷名，标注原卷名→新卷名）

【诊断报告】
- 原有问题（从诊断扫描10项中列出命中项）：
- 问题严重程度：致命/严重/一般/优化
- 问题根因分析：

【修改方案】
- 修改类型：结构修复 / 支线并网 / 暗线重塑 / 势力重构 / 情感与代价植入 / 节奏校准 / 胜利悖论植入 / 综合调整
- 具体修改动作（逐条列出）：
- 修改后预期效果：

【修改后卷首定位】
- 主题：（若有调整）
- 叙事目标：（若有调整）
- 核心冲突：（若有调整）
- 对手/压力源：（若有调整）
- 胜利悖论：（必须明确）

【修改后超密度情节骨架】
▶ 主线节拍（8-12个，标注修改标记）：
  [新增] 节拍X：……
  [调整] 节拍X：原……→改为……
  [保留] 节拍X：……
  （每个节拍含：场景、人物、事件、不可逆后果）

▶ 支线A/B节拍（4-6个，标注与主线交汇节点）：
  （同样使用[新增]/[调整]/[保留]标记）

▶ 暗线推进：
  本卷揭露层：……
  本卷新增疑问：……
  信息碎片化来源：……

▶ 势力互动：
  参与方及诉求：……
  合作与背叛节点：……

▶ 信息差与误会：
  偏差事件：……
  跨卷影响：……

▶ 反转设计（至少2处）：
  反转1：……
  反转2：……

▶ 情感钩子（至少3处）：
  1. …… 2. …… 3. ……

▶ 卷末强悬念：
  ……

【修改后人物成长弧线】
- 主角变化：（对比修改前后）
- 关键抉择：（延迟代价标注）
- 配角高光：
- 关系演变：
- 新角色引入：

【修改后世界观与设定展开】
- 新地图/层级：（若有调整）
- 力量阶梯颗粒化：（重点修复战力跳级问题）
- 历史纵深/过去线：
- 关键道具溯源：
- 伏笔铺设：（标注[新增伏笔]/[调整伏笔]，并注明预计回收卷数）

【修改后节奏与结构控制】
- 张弛分布：（明确标注高张力/缓冲/整合/铺垫的分布）
- 信息释放节奏：
- 代价与反噬累积：（明确列出本卷埋下的延迟代价及预计爆发卷数）

【卷末衔接与下卷预告】
- 即时危机：
- 中期压力：
- 长期伏笔：
- 人物位移：

---

五、跨卷联动修改规则（若修改范围涉及多卷）

当修改某一卷的内容时，必须检查并标注对相邻卷的影响：

1. 前卷影响：本卷修改是否需要前卷增加铺垫？若需要，明确写出"需在前卷X增加伏笔：……"
2. 后卷影响：本卷修改是否导致后卷剧情失效？若导致，写出"后卷X需同步调整：……"
3. 暗线一致性：修改后的暗线揭露是否与后续已设计好的揭露冲突？若冲突，提供调和方案。
4. 战力基准线：修改后的主角实力是否破坏后续敌人的威胁感？若破坏，提供后续敌人强化方案或延迟主角升级。
5. 关系网涟漪：修改后的角色关系变化（如某人提前死亡/反目）是否切断后续重要剧情线？若切断，提供替代剧情线。

---

六、修改原则与禁忌

【必须遵守】
- 保持人设连续性：修改后的角色行为必须符合其原始核心动机与性格底色。
- 保持逻辑自洽：任何新增设定必须与已有世界观兼容，禁止吃书。
- 保持情感真实：修改后的情感冲突必须基于真实的人性弱点，禁止为虐而虐。
- 保持长线燃料：每一次修改都必须为超长篇连载增加新的可持续推进动力，而非透支后续剧情。

【绝对禁止】
- 禁止为修复一个问题而制造更大的逻辑漏洞。
- 禁止将"复杂化"等同于"注水"，修改后每卷字数仍须保持高密度。
- 禁止删除已有伏笔而不提供替代方案。
- 禁止将配角高光修改为"全靠主角拯救"的工具人剧情。
- 禁止用"机械降神"解决原本的剧情困境。

---

七、输出示例（仅展示结构）

【第三卷：血盟裂帛】（原卷名：第三卷：新的朋友）

【诊断报告】
- 原有问题：
  1. 支线孤立指数过高：支线B（女二寻亲）与主线完全脱节，女二沦为情报工具人。
  2. 胜利悖论缺失：本卷主角成功组建联盟，但结局过于圆满，缺乏后续危机触发。
  3. 节奏过松：第4-6节拍连续铺垫，无突发事件打断。
- 严重程度：严重
- 根因分析：作者在规划时将女二支线视为"情感调剂"，未设计其与主线势力的利益交换点；联盟组建缺乏"蜜月期后的利益冲突"设计。

【修改方案】
- 修改类型：支线并网 + 胜利悖论植入 + 节奏校准
- 具体修改动作：
  1. 将女二寻亲目标与主线"寻找上古遗迹钥匙"绑定——女二要找的亲人正是钥匙守护者，主线与支线资源交换。
  2. 在联盟庆功宴（原节拍6）插入"盟约血誓"环节，主角为取信盟友不得不接受"魂印约束"，为第5卷反噬埋下代价。
  3. 在节拍4-5之间新增"第三方势力夜袭"事件，打断连续铺垫，同时揭露联盟内有叛徒。
- 预期效果：女二获得独立高光与道德困境；联盟从"圆满结局"变为"蜜月期下的暗流"；节奏张弛比调整为3:2:3:2。

【修改后卷首定位】
……（依此类推）

（继续输出完整修改后内容，直至完成所有指定修改卷）
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 20
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 30
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 40
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'ExistingVolumeOutline', '现有分卷大纲', 'string', 1, '当前数据库中已有分卷大纲格式化文本。', '第1卷：...', 50
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'ModificationRequest', '修改意见', 'string', 1, '用户输入的分卷修改要求。', '第三卷节奏太慢，需要增强反转。', 60
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'volumes', '分卷大纲列表', 'array<VolumeOutlineItem>', 1, '分卷大纲列表，每项包含 volumeNumber、title、summary、content、endingHook。', '[{"volumeNumber":1,"title":"..."}]', 70
FROM ai_prompts WHERE prompt_key = 'revise_volume_outline'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_volume_story', '生成分卷正文', 'volume_story', '根据某一卷分卷大纲生成完整详细的分卷正文。', '
你是一位擅长长篇网文正文创作的小说作者。现在请根据某一卷的分卷大纲，生成这一卷的详细完整故事正文,正文要尽可能的详细细致，正文要多。

写作目标：
1. 必须严格遵守故事总大纲、故事摘要、主要人物设定和当前分卷大纲。
2. 这一卷要形成完整的阶段性故事：开端、推进、冲突升级、关键反转、阶段高潮、卷末钩子都要完整。
3. 正文应尽可能细致，包含场景描写、人物行动、对话、心理变化、冲突过程和因果承接。
4. 不要写成提纲，不要只概括剧情，要以小说正文方式展开。
5. 保持人物动机稳定，不得违背已有设定，不得跳过当前分卷大纲中的关键事件。
6. 卷末必须自然承接 endingHook，为下一卷留下期待。

全局故事信息：
- 书名：{Title}
- 漫剧视觉风格：{StoryStyle}
- 故事摘要：{StorySummary}
- 故事总大纲：{Outline}
- 主要人物设定：{Characters}

当前分卷信息：
- 卷号：第 {VolumeNumber} 卷
- 卷名：{VolumeTitle}
- 分卷摘要：{VolumeSummary}
- 分卷详细大纲：{VolumeContent}
- 卷末钩子：{EndingHook}

输出要求：
- 只输出当前这一卷的正文内容。
- 使用自然的中文小说叙事，不要输出正文以外的解释。
- 章节可用“小标题”分段，但整体必须是一卷完整连续的故事。
- 正文长度尽量充分，重点是完整、细致、可读。
- 正文应尽可能细致，包含场景描写、人物行动、对话、心理变化、冲突过程和因果承接。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StoryStyle', '漫剧风格', 'string', 0, '用户设定的统一视觉风格，会影响后续图片和视频生成。', '国漫电影感', 20
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 30
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 40
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 50
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeNumber', '卷号', 'integer', 1, '当前分卷编号。', '1', 60
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeTitle', '卷标题', 'string', 1, '当前分卷标题。', '暗夜启明', 70
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeSummary', '分卷摘要', 'string', 0, '当前分卷摘要。', '...', 80
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeContent', '分卷详细大纲', 'string', 1, '当前分卷详细大纲。', '...', 90
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'EndingHook', '卷末钩子', 'string', 0, '当前分卷末尾钩子。', '...', 100
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'volumeStory', '分卷正文', 'string', 1, '生成的完整分卷正文纯文本。', '...', 110
FROM ai_prompts WHERE prompt_key = 'generate_volume_story'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_volume_section_count', '判断分卷小节数量', 'volume_sections', '使用温度为 0 的模型判断当前分卷适合拆成多少个小节。', '
你是一位长篇网文编辑，负责把某一卷分卷大纲拆成适合逐节创作的小节数量。

请根据以下信息判断当前分卷应该拆成多少个小节：

- 书名：{Title}
- 故事摘要：{StorySummary}
- 故事总大纲：{Outline}
- 主要人物设定：{Characters}
- 卷号：第 {VolumeNumber} 卷
- 卷名：{VolumeTitle}
- 分卷摘要：{VolumeSummary}
- 分卷详细大纲：{VolumeContent}
- 卷末钩子：{EndingHook}

要求：
1. 必须选择 4 到 12 之间的整数。
2. 如果本卷情节较集中，选择 4-6 节。
3. 如果本卷支线多、反转多、场景跨度大，选择 7-10 节。
4. 如果本卷是阶段高潮卷或多线并行卷，选择 10-12 节。
5. 小节数量要服务于剧情推进，不要机械拆分。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 20
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 30
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 40
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeNumber', '卷号', 'integer', 1, '当前分卷编号。', '1', 50
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeTitle', '卷标题', 'string', 1, '当前分卷标题。', '暗夜启明', 60
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeSummary', '分卷摘要', 'string', 0, '当前分卷摘要。', '...', 70
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeContent', '分卷详细大纲', 'string', 1, '当前分卷详细大纲。', '...', 80
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'EndingHook', '卷末钩子', 'string', 0, '当前分卷末尾钩子。', '...', 90
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'section_count', '小节数量', 'integer', 1, '推荐小节数量，范围 4-12。', '6', 100
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_count'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_volume_section_single', '逐节生成故事细节', 'volume_sections', '按节号逐个生成具体故事细节，并参考已生成前序小节保持连续。', '
你是一位擅长长篇网文正文创作的小说作者。现在不要一次性输出整卷，只生成当前指定小节的具体故事细节。

全局故事信息：
- 书名：{Title}
- 漫剧视觉风格：{StoryStyle}
- 故事摘要：{StorySummary}
- 故事总大纲：{Outline}
- 主要人物设定：{Characters}

当前分卷信息：
- 卷号：第 {VolumeNumber} 卷
- 卷名：{VolumeTitle}
- 分卷摘要：{VolumeSummary}
- 分卷详细大纲：{VolumeContent}
- 卷末钩子：{EndingHook}

小节位置：
- 本卷总小节数：{TotalSections}
- 当前小节号：{CurrentSectionNumber}

已经生成的前序小节：
{GeneratedSections}

生成要求：
1. 当前小节必须严格对应“第 {CurrentSectionNumber} 节 / 共 {TotalSections} 节”的叙事位置。
2. 必须承接前序小节已经发生的事件、人物情绪、因果代价和未解决危机。
3. 必须推进分卷大纲中的关键事件，不要偏离当前卷核心矛盾。
4. 内容要是具体故事细节，包含场景、行动、对话、心理、冲突、信息差和小节末尾钩子。
5. 禁止只写提纲，禁止用一句话概括，应写成可继续扩写为正文的高密度故事细节。
6. 最后一节必须自然落到本卷卷末钩子；非最后一节必须为下一节留下承接压力。

输出格式要求：
1. 不要输出 JSON，不要输出 Markdown 代码块，不要输出额外解释。
2. 必须严格使用下面 4 个标签包裹内容，标签名不能改：
<title>当前小节标题</title>
<summary>当前小节摘要</summary>
<content>当前小节具体故事细节，可以包含人物对白、引号、换行和场景描写</content>
<endingHook>当前小节末尾钩子</endingHook>
3. 只输出当前这一节，当前小节号是第 {CurrentSectionNumber} 节。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StoryStyle', '漫剧风格', 'string', 0, '用户设定的统一视觉风格，会影响后续图片和视频生成。', '国漫电影感', 20
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 30
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 40
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 50
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeNumber', '卷号', 'integer', 1, '当前分卷编号。', '1', 60
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeTitle', '卷标题', 'string', 1, '当前分卷标题。', '暗夜启明', 70
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeSummary', '分卷摘要', 'string', 0, '当前分卷摘要。', '...', 80
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeContent', '分卷详细大纲', 'string', 1, '当前分卷详细大纲。', '...', 90
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'EndingHook', '卷末钩子', 'string', 0, '当前分卷末尾钩子。', '...', 100
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'TotalSections', '总小节数', 'integer', 1, '当前卷总小节数。', '6', 110
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'CurrentSectionNumber', '当前小节号', 'integer', 1, '当前正在生成的小节号。', '1', 120
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'GeneratedSections', '已生成小节', 'string', 0, '前序小节上下文。', '第1节：...', 130
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'title', '标题', 'string', 1, '生成结果标题，可表示卷标题或小节标题。', '暗夜启明', 140
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'summary', '摘要', 'string', 1, '生成结果摘要，可表示分卷摘要或小节摘要。', '...', 150
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'content', '详细内容', 'string', 1, '生成的详细大纲或小节故事细节。', '...', 160
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'endingHook', '结尾钩子', 'string', 1, '卷末或小节末尾的悬念钩子。', '...', 170
FROM ai_prompts WHERE prompt_key = 'generate_volume_section_single'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('extract_section_assets', '识别小节人物和场景资产', 'section_assets', '从单个小节故事中识别出现的人物和场景，并判断是否匹配已有资产。', '
你是一位漫剧资产统筹，负责从单个小节故事细节中识别本节实际出现的人物和场景。

故事信息：
- 书名：{Title}
- 漫剧风格：{StoryStyle}
- 故事摘要：{StorySummary}
- 故事总大纲：{Outline}
- 主要人物设定：{Characters}

当前分卷：
- 卷号：第 {VolumeNumber} 卷
- 卷名：{VolumeTitle}

当前小节：
- 小节号：第 {SectionNumber} 节
- 小节标题：{SectionTitle}
- 小节摘要：{SectionSummary}
- 小节内容：
{SectionContent}

已有资产：
{ExistingAssets}

任务：
1. 提取本节实际出场或明确发生的“人物”和“场景”，不要提取只被随口提到、没有出场的人物或场景。
2. 你需要判断每个资产到底是人物还是场景：人物、怪物、拟人角色、明确有身份行动的生物放入 characters；地点、房间、街区、建筑、自然环境、交通空间、战斗场地放入 scenes。
3. 人物名称必须稳定，同一人物不要因为称谓变化产生多个名字，例如“林浩”和“林浩同学”只保留“林浩”。
4. 场景名称要能复用，例如“陈东的安全屋”“废弃地铁站月台”，不要写成一次性的长句。
5. 每个人物和场景都要给出用于生成图片的 imagePrompt。人物要描述外貌、发型、服装、配饰、年龄气质和标志性道具，便于后续生成三视图；场景要描述空间结构、光影、时代、氛围、关键道具和镜头构图。
6. imagePrompt 必须严格贴合用户设定的漫剧风格：{StoryStyle}。
7. 判断是否已有资产时，不要依赖图片文件名，也不要只看名称是否完全相同；必须综合资产类型、已有资产名称、已有描述、图片提示词、本节上下文判断是否是同一个人物或同一个场景。
8. 如果确认与已有资产是同一个对象，matchedExistingName 必须填写“已有资产”中的原始名称，name 可以使用本节里的规范称呼；如果不能确认是同一个对象，matchedExistingName 置空。
9. 只有高置信度确认同一人物/场景时才匹配已有资产；例如“林浩”“林浩同学”“少年林浩”可以匹配，但“黑衣人”“神秘追踪者”如果身份未明确，不要强行匹配。
10. 使用 with_structured_output 输出，不要输出额外解释。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StoryStyle', '漫剧风格', 'string', 0, '用户设定的统一视觉风格，会影响后续图片和视频生成。', '国漫电影感', 20
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 30
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 40
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 50
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeNumber', '卷号', 'integer', 1, '当前分卷编号。', '1', 60
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeTitle', '卷标题', 'string', 1, '当前分卷标题。', '暗夜启明', 70
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionNumber', '小节号', 'integer', 1, '当前小节编号。', '1', 80
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionTitle', '小节标题', 'string', 1, '当前小节标题。', '追踪者来袭', 90
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionSummary', '小节摘要', 'string', 0, '当前小节摘要。', '...', 100
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionContent', '小节内容', 'string', 1, '当前小节完整故事内容。', '...', 110
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'ExistingAssets', '已有资产', 'string', 0, '当前故事已有资产上下文，包含名称、描述、提示词和路径。', '- [CHARACTER] 林浩：...', 120
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'characters', '人物资产列表', 'array<SectionAssetExtractionItem>', 1, '识别出的本节人物列表。', '[{"name":"林浩"}]', 130
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'scenes', '场景资产列表', 'array<SectionAssetExtractionItem>', 1, '识别出的本节场景列表。', '[{"name":"废弃地铁站"}]', 140
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'matchedExistingName', '匹配已有资产名', 'string|null', 0, '每个资产项中用于标记匹配到的已有资产原始名称。', '林浩', 150
FROM ai_prompts WHERE prompt_key = 'extract_section_assets'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('generate_section_script', '生成小节故事脚本', 'section_script', '根据单个小节故事生成镜头级分镜脚本。', '
你是一名漫剧导演、分镜师和短剧编剧。现在请根据单个小节故事，生成可直接用于后续视频制作的故事脚本。

全局故事信息：
- 书名：{Title}
- 漫剧视觉风格：{StoryStyle}
- 故事摘要：{StorySummary}
- 故事总大纲：{Outline}
- 主要人物设定：{Characters}

当前分卷信息：
- 卷号：第 {VolumeNumber} 卷
- 卷名：{VolumeTitle}
- 分卷摘要：{VolumeSummary}
- 分卷详细大纲：{VolumeContent}
- 卷末钩子：{EndingHook}

当前小节信息：
- 小节号：第 {SectionNumber} 节
- 小节标题：{SectionTitle}
- 小节摘要：{SectionSummary}
- 小节故事正文：{SectionContent}
- 小节钩子：{SectionEndingHook}

创作要求：
1. 总时长由你根据小节内容自行决定，不需要用户指定；节奏要适合漫剧短视频观看。
2. 输出要拆成连续分镜，每个分镜必须包含：时长、分镜类型、镜头运动、动作、台词。
3. 分镜类型可以使用全景、远景、中景、近景、特写、大特写、俯拍、仰拍、空镜、过肩镜头等。
4. 镜头运动可以使用推、拉、摇、移、跟拍、环绕、定镜、手持感、快速切换等；不同镜头之间要有配合，不要机械重复。
5. 动作要写清楚画面中人物在做什么、场景发生什么变化、情绪如何推进。
6. 台词要写清楚画面哪个人物说的台词只写本镜头中实际说出口的话；没有台词时可以为空字符串，但不能把动作写进台词。
7. 必须严格贴合小节故事正文，不要新增会改变剧情走向的大事件。
8. 最后一两个分镜要自然承接小节钩子，为下一节保留期待。
9. 使用 with_structured_output 输出结构化结果，不要输出额外解释。
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StoryStyle', '漫剧风格', 'string', 0, '用户设定的统一视觉风格，会影响后续图片和视频生成。', '国漫电影感', 20
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 30
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 40
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Characters', '主要人物', 'string', 0, '由主要角色设定格式化后的文本。', '- 林浩：主角...', 50
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeNumber', '卷号', 'integer', 1, '当前分卷编号。', '1', 60
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeTitle', '卷标题', 'string', 1, '当前分卷标题。', '暗夜启明', 70
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeSummary', '分卷摘要', 'string', 0, '当前分卷摘要。', '...', 80
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'VolumeContent', '分卷详细大纲', 'string', 1, '当前分卷详细大纲。', '...', 90
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'EndingHook', '卷末钩子', 'string', 0, '当前分卷末尾钩子。', '...', 100
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionNumber', '小节号', 'integer', 1, '当前小节编号。', '1', 110
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionTitle', '小节标题', 'string', 1, '当前小节标题。', '追踪者来袭', 120
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionSummary', '小节摘要', 'string', 0, '当前小节摘要。', '...', 130
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionContent', '小节内容', 'string', 1, '当前小节完整故事内容。', '...', 140
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'SectionEndingHook', '小节钩子', 'string', 0, '当前小节末尾钩子。', '...', 150
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'sectionNumber', '小节号', 'integer', 1, '脚本对应的小节号。', '1', 160
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'totalDurationSeconds', '总时长', 'integer', 1, 'AI 自行决定的小节脚本总时长，单位秒。', '120', 170
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'shots', '分镜列表', 'array<ScriptShotItem>', 1, '镜头列表，每项包含 shotNumber、durationSeconds、shotType、cameraMovement、action、dialogue。', '[{"shotNumber":1,"durationSeconds":6}]', 180
FROM ai_prompts WHERE prompt_key = 'generate_section_script'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompts (prompt_key, prompt_name, category, description, template_content, enabled)
VALUES ('chat_agent', '对话路由 Agent', 'chat', '根据用户对话消息重写问题并决定需要调用的 Java 方法。', '
你是路由与工具调用代理（Routing & Tool-Calling Agent）。  
你运行在对话会话中，该会话已绑定到一个具体的故事项目。你的职责是：理解用户的聊天意图，将其转化为明确的指令，并决定调用哪条链路。

---

核心任务（必须完成以下两项）

1. 意图理解与指令重写 
   将用户的自然语言消息重写为一条清晰、完整、无歧义的独立指令。若用户意图模糊，按最合理的创作方向补全。

2. 路由决策  
   根据指令判断应调用哪条链路。只允许使用下方列出的方法。

---

输出格式要求

你必须返回一个标准 JSON 对象，包含以下字段：

```json
{
  "assistantMessage": "简短的中文回复，向用户说明执行了什么操作或给出友好回应",
  "javaMethod": "Java 方法名，必须是下方列表中的某一个",
  "javaMethodArgs": { ... }
}
', 1)
ON DUPLICATE KEY UPDATE
    prompt_name = VALUES(prompt_name),
    category = VALUES(category),
    description = VALUES(description),
    template_content = VALUES(template_content),
    enabled = VALUES(enabled);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Title', '书名', 'string', 1, '当前故事标题。', '记忆霓虹', 10
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'StorySummary', '故事摘要', 'string', 0, '当前故事摘要。', '未来都市中，主角卷入记忆交易阴谋。', 20
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'Outline', '故事大纲', 'string', 1, '完整剧情大纲。', '一、基础设定...', 30
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'INPUT', 'UserMessage', '用户消息', 'string', 1, '用户在聊天窗口发送的原始消息。', '帮我把主角改成女性。', 40
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'rewrittenQuestion', '重写问题', 'string', 1, '去除上下文依赖后的独立问题。', '请将故事主角改为女性并调整相关设定。', 50
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'route', '路由标签', 'string', 1, '模型判断出的处理类型。', 'update_outline', 60
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'javaMethod', 'Java 方法名', 'string', 1, '需要 Java 执行的方法名，必须在白名单内。', 'story.updateOutline', 70
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'javaMethodArgs', 'Java 方法参数', 'object', 1, '传给 Java 方法的参数 JSON。', '{"suggestion":"..."}', 80
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

INSERT INTO ai_prompt_parameters (prompt_id, direction, param_key, param_name, data_type, required_flag, description, example_value, sort_order)
SELECT id, 'OUTPUT', 'assistantMessage', '助手回复', 'string', 1, '返回给用户的简短中文说明。', '我会帮你调整主角设定。', 90
FROM ai_prompts WHERE prompt_key = 'chat_agent'
ON DUPLICATE KEY UPDATE
    param_name = VALUES(param_name),
    data_type = VALUES(data_type),
    required_flag = VALUES(required_flag),
    description = VALUES(description),
    example_value = VALUES(example_value),
    sort_order = VALUES(sort_order);

UPDATE ai_prompts
SET base_prompt_key = prompt_key,
    prompt_scope = 'DEFAULT',
    priority = 0
WHERE base_prompt_key = '';

