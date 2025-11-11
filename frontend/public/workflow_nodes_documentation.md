# Workflow 节点使用方法介绍

本文档介绍了 `app/workflow/nodes` 目录下所有可用的工作流节点，包括它们的功能、输入输出参数和使用方法。这些节点可以组合使用来构建复杂的工作流程。

## 节点分类

本系统包含以下9个主要类别的节点，共计47个节点：

1. **基础类型节点 (basic_types)**: 6个节点 - 处理基本数据类型和数学运算
2. **文本处理节点 (text_process)**: 10个节点 - 文本操作、转换和处理
3. **列表处理节点 (list_process)**: 6个节点 - 列表数据结构操作
4. **字典处理节点 (dict_process)**: 10个节点 - 字典数据结构操作
5. **JSON处理节点 (json_process)**: 2个节点 - JSON数据解析和提取
6. **模型请求节点 (model-request)**: 6个节点 - 模型请求数据准备和配置
7. **模型服务节点 (digen_services)**: 2个节点 - 模型服务API调用
8. **自定义节点 (custom_nodes)**: 2个节点 - Qwen系列AI模型调用
9. **控制流节点 (control)**: 5个节点 - 工作流控制逻辑

### 1. 基础类型节点 (basic_types)

#### TextInputNode - 文本输入节点
**功能**: 传递文本输入，不做任何修改
- **输入端口**:
  - `text` (string, 必需): 要传递的文本内容
- **输出端口**:
  - `text` (string): 与输入相同的文本

#### IntInputNode - 整数输入节点
**功能**: 处理和验证整数输入
- **输入端口**:
  - `value` (number, 必需, 默认值: 0): 整数值
- **输出端口**:
  - `value` (number): 验证后的整数值

#### FloatInputNode - 浮点数输入节点
**功能**: 处理和验证浮点数输入
- **输入端口**:
  - `value` (number, 必需, 默认值: 0.0): 浮点数值
- **输出端口**:
  - `value` (number): 验证后的浮点数值

#### BoolInputNode - 布尔输入节点
**功能**: 处理和验证布尔值输入
- **输入端口**:
  - `value` (boolean, 必需, 默认值: false): 布尔值
- **输出端口**:
  - `value` (boolean): 验证后的布尔值

#### MathOperationNode - 数学运算节点
**功能**: 对两个数字执行基本数学运算
- **输入端口**:
  - `a` (number, 必需, 默认值: 0): 第一个操作数
  - `b` (number, 必需, 默认值: 0): 第二个操作数
  - `operation` (string, 必需, 默认值: "add"): 运算类型 (add, subtract, multiply, divide)
- **输出端口**:
  - `result` (number): 运算结果

#### TypeConvertNode - 类型转换节点
**功能**: 在不同数据类型之间进行转换
- **输入端口**:
  - `value` (any, 必需): 要转换的值
  - `from_type` (string, 必需, 默认值: "text"): 源类型 (float, int, text)
  - `to_type` (string, 必需, 默认值: "text"): 目标类型 (float, int, text)
- **输出端口**:
  - `value` (any): 转换后的值

### 2. 文本处理节点 (text_process)

#### TextRepeatNode - 文本重复节点
**功能**: 将文本转换为列表并可选择重复
- **输入端口**:
  - `text` (string, 必需): 要转换的文本
  - `repeat_count` (number, 可选, 默认值: 1): 重复次数
- **输出端口**:
  - `list` (array): 包含重复文本的数组

#### TextCombinerNode - 文本组合节点
**功能**: 使用模板和变量组合文本
- **输入端口**:
  - `prompt` (string, 必需): 包含变量的模板 (如 {text_a}, {text_b})
  - `text_a` (string, 可选): 变量 {text_a} 的值
  - `text_b` (string, 可选): 变量 {text_b} 的值
  - `text_c` (string, 可选): 变量 {text_c} 的值
- **输出端口**:
  - `combined_text` (string): 替换变量后的文本
  - `used_variables` (object): 显示哪些变量被使用

#### LoadTextFromFileNode - 文件加载节点
**功能**: 从文件加载文本内容
- **输入端口**:
  - `file_path` (string, 必需): 文件的相对路径
- **输出端口**:
  - `text` (string): 文件内容

#### TextStripNode - 文本去空格节点
**功能**: 去除文本两端的空白字符
- **输入端口**:
  - `text` (string, 必需): 要处理的文本
- **输出端口**:
  - `text` (string): 去除空白后的文本

#### TextRemoveEmptyLinesNode - 删除空行节点
**功能**: 删除文本中的空行和仅包含空白的行
- **输入端口**:
  - `text` (string, 必需): 要清理的文本
- **输出端口**:
  - `text` (string): 删除空行后的文本

#### TextSplitNode - 文本分割节点
**功能**: 使用指定分隔符分割文本
- **输入端口**:
  - `text` (string, 必需): 要分割的文本
  - `delimiter` (string, 可选, 默认值: "\n"): 分隔符
  - `max_splits` (number, 可选): 最大分割数量
- **输出端口**:
  - `segments` (array): 分割后的文本段
  - `count` (number): 分割段数

#### TextReplaceNode - 文本替换节点
**功能**: 替换文本中的指定内容
- **输入端口**:
  - `text` (string, 必需): 原始文本
  - `old_text` (string, 必需): 要替换的文本
  - `new_text` (string, 可选): 替换后的文本
  - `count` (number, 可选): 最大替换次数
  - `direction` (string, 可选): 替换方向 (all, start, end)
- **输出端口**:
  - `replaced_text` (string): 替换后的文本
  - `replacement_count` (number): 实际替换次数

#### TextToDictNode - 文本转字典节点
**功能**: 将文本转换为字典
- **输入端口**:
  - `text` (string, 必需): 要转换的文本
  - `format` (string, 可选, 默认值: "json"): 格式 (json, key_value)
  - `separator` (string, 可选, 默认值: "\n"): 键值对分隔符
  - `key_value_delimiter` (string, 可选, 默认值: ":"): 键值分隔符
- **输出端口**:
  - `dict` (any): 解析后的字典

#### TextToListNode - 文本转列表节点
**功能**: 将文本转换为列表
- **输入端口**:
  - `text` (string, 必需): 要转换的文本
  - `format` (string, 可选, 默认值: "json"): 格式 (json, delimited)
  - `delimiter` (string, 可选, 默认值: ","): 分隔符
  - `trim_items` (boolean, 可选, 默认值: true): 是否去除项目空白
  - `skip_empty` (boolean, 可选, 默认值: true): 是否跳过空项目
- **输出端口**:
  - `list` (any): 解析后的列表

### 3. 列表处理节点 (list_process)

#### ListRangeNode - 列表范围节点
**功能**: 提取列表的指定范围元素
- **输入端口**:
  - `list` (array, 必需): 输入列表
  - `start` (number, 可选, 默认值: 0): 开始索引
  - `end` (number, 可选): 结束索引
- **输出端口**:
  - `result` (array): 提取的元素列表
  - `length` (number): 结果列表长度

#### ListIndexNode - 列表索引节点
**功能**: 获取列表指定索引的值
- **输入端口**:
  - `list` (array, 必需): 输入列表
  - `index` (number, 必需, 默认值: 0): 索引位置
- **输出端口**:
  - `value` (any): 指定索引的值
  - `exists` (boolean): 索引是否存在

#### ListConcatNode - 列表连接节点
**功能**: 连接两个列表
- **输入端口**:
  - `list_a` (array, 必需): 第一个列表
  - `list_b` (array, 必需): 第二个列表
- **输出端口**:
  - `result` (array): 连接后的列表
  - `length` (number): 结果列表长度

#### ListAppendNode - 列表追加节点
**功能**: 向列表末尾添加元素
- **输入端口**:
  - `list` (array, 必需): 输入列表
  - `value` (any, 必需): 要添加的值
- **输出端口**:
  - `result` (array): 添加元素后的列表
  - `length` (number): 结果列表长度

#### ListCreateNode - 列表创建节点
**功能**: 从单独的值创建列表
- **输入端口**:
  - `value_1` (any, 可选): 第一个值
  - `value_2` (any, 可选): 第二个值
  - `value_3` (any, 可选): 第三个值
  - `value_4` (any, 可选): 第四个值
  - `value_5` (any, 可选): 第五个值
- **输出端口**:
  - `result` (array): 创建的列表
  - `length` (number): 列表长度

#### ListLengthNode - 列表长度节点
**功能**: 获取列表长度
- **输入端口**:
  - `list` (array, 必需): 输入列表
- **输出端口**:
  - `length` (number): 列表长度
  - `is_empty` (boolean): 列表是否为空

### 4. 字典处理节点 (dict_process)

#### DictCreateNode - 字典创建节点
**功能**: 创建新的字典对象
- **输入端口**:
  - `initial_data` (object, 可选): 初始数据
- **输出端口**:
  - `dict` (object): 创建的字典

#### DictAddNode - 字典添加节点
**功能**: 向字典添加键值对
- **输入端口**:
  - `dict` (object, 必需): 目标字典
  - `key` (string, 必需): 要添加的键
  - `value` (any, 必需): 要添加的值
- **输出端口**:
  - `updated_dict` (object): 更新后的字典

#### DictGetNode - 字典获取节点
**功能**: 从字典获取指定键的值
- **输入端口**:
  - `dict` (object, 必需): 源字典
  - `key` (string, 必需): 要获取的键
  - `default_value` (any, 可选): 默认值
- **输出端口**:
  - `value` (any): 获取的值
  - `exists` (boolean): 键是否存在

#### DictMergeNode - 字典合并节点
**功能**: 合并多个字典
- **输入端口**:
  - `dict1` (object, 必需): 第一个字典
  - `dict2` (object, 必需): 第二个字典
  - `dict3` (object, 可选): 第三个字典
  - `overwrite` (boolean, 可选): 是否覆盖重复键
- **输出端口**:
  - `merged_dict` (object): 合并后的字典

#### DictKeysNode - 字典键节点
**功能**: 获取字典的所有键
- **输入端口**:
  - `dict` (object, 必需): 源字典
- **输出端口**:
  - `keys` (array): 所有键的列表
  - `count` (number): 键的数量

#### DictValuesNode - 字典值节点
**功能**: 获取字典的所有值
- **输入端口**:
  - `dict` (object, 必需): 源字典
- **输出端口**:
  - `values` (array): 所有值的列表
  - `count` (number): 值的数量

#### DictRemoveNode - 字典删除节点
**功能**: 从字典删除指定键值对
- **输入端口**:
  - `dict` (object, 必需): 源字典
  - `key` (string, 必需): 要删除的键
  - `ignore_missing` (boolean, 可选): 忽略不存在的键
- **输出端口**:
  - `updated_dict` (object): 删除后的字典
  - `removed_value` (any): 被删除的值
  - `was_removed` (boolean): 是否成功删除

#### DictUpdateNode - 字典更新节点
**功能**: 更新字典中指定键的值
- **输入端口**:
  - `dict` (object, 必需): 源字典
  - `key` (string, 必需): 要更新的键
  - `new_value` (any, 必需): 新值
  - `create_if_missing` (boolean, 可选): 键不存在时是否创建
- **输出端口**:
  - `updated_dict` (object): 更新后的字典
  - `old_value` (any): 原来的值
  - `was_updated` (boolean): 是否成功更新

#### DictClearNode - 字典清空节点
**功能**: 清空字典的所有内容
- **输入端口**:
  - `dict` (object, 必需): 要清空的字典
- **输出端口**:
  - `empty_dict` (object): 清空后的字典
  - `original_count` (number): 原字典的键数量

#### DictCopyNode - 字典复制节点
**功能**: 创建字典的副本
- **输入端口**:
  - `dict` (object, 必需): 要复制的字典
  - `deep_copy` (boolean, 可选): 是否深度复制
- **输出端口**:
  - `copied_dict` (object): 复制的字典

#### DictHasKeyNode - 字典键检查节点
**功能**: 检查字典是否包含指定键
- **输入端口**:
  - `dict` (object, 必需): 要检查的字典
  - `key` (string, 必需): 要检查的键
- **输出端口**:
  - `has_key` (boolean): 是否包含该键
  - `value` (any): 键对应的值

### 5. JSON处理节点 (json_process)

#### JsonParseNode - JSON解析节点
**功能**: 将JSON字符串解析为JSON对象
- **输入端口**:
  - `json_string` (string, 必需): JSON字符串
- **输出端口**:
  - `json_object` (object): 解析后的JSON对象

#### JsonExtractNode - JSON提取节点
**功能**: 从JSON对象提取指定字段的值
- **输入端口**:
  - `json_object` (object, 必需): JSON对象
  - `key` (string, 必需): 要提取的字段名
- **输出端口**:
  - `value` (any): 提取的值

### 6. 模型请求节点 (model-request)

#### ModelRequestInputNode - 模型请求输入节点
**功能**: 构建和验证模型输入数据
- **输入端口**:
  - `url` (string, 可选): 单个URL
  - `urls` (array, 可选): URL列表
  - `type` (string, 必需): 输入类型 (image, audio, video)
- **输出端口**:
  - `input_list` (array): 处理后的输入列表

#### ConcatModelRequestInputNode - 模型请求输入合并节点
**功能**: 合并两个ModelRequestInputNode的输出
- **输入端口**:
  - `input_1` (array, 必需): 第一个输入列表
  - `input_2` (array, 必需): 第二个输入列表
- **输出端口**:
  - `input_list` (array): 合并后的输入列表

#### BatchModelRequestInputNode - 批量模型请求输入节点
**功能**: 将URL列表转换为批量输入格式
- **输入端口**:
  - `urls` (array, 必需): URL列表
  - `type` (string, 必需): 输入类型
- **输出端口**:
  - `input_list` (array): 批量输入列表

#### ConcatBatchModelRequestInputNode - 批量输入合并节点
**功能**: 合并两个BatchModelRequestInputNode的输出
- **输入端口**:
  - `input_list_1` (array, 必需): 第一个输入列表
  - `input_list_2` (array, 必需): 第二个输入列表
- **输出端口**:
  - `input_list` (array): 合并后的列表

#### BatchModelRequestNode - 批量模型请求节点
**功能**: 整合批量输入数据和选项配置
- **输入端口**:
  - `input_list` (array, 可选): 输入列表
  - `prompts` (array, 可选): 提示词列表
  - `audio_prompts` (array, 可选): 音频提示词列表
  - `negative_prompts` (array, 可选): 负面提示词列表
  - `width` (number, 可选, 默认值: 768): 图像宽度
  - `height` (number, 可选, 默认值: 768): 图像高度
  - `batch_size` (number, 可选, 默认值: 1): 批处理大小
  - `num_frames` (number, 可选): 帧数
  - `seed` (number, 可选): 随机种子
  - `output_format` (string, 可选): 输出格式
  - `extra_options` (object, 可选): 扩展选项
- **输出端口**:
  - `requests` (array): 请求配置列表

#### ModelRequestNode - 模型请求节点
**功能**: 整合输入数据和选项配置，生成完整的模型请求
- **输入端口**:
  - `input_list` (array, 可选): 输入列表
  - `prompt` (string, 可选): 提示词
  - `audio_prompt` (string, 可选): 音频提示词
  - `negative_prompt` (string, 可选): 负面提示词
  - `width` (number, 可选, 默认值: 768): 图像宽度
  - `height` (number, 可选, 默认值: 768): 图像高度
  - `batch_size` (number, 可选, 默认值: 1): 批处理大小
  - `num_frames` (number, 可选): 帧数
  - `seed` (number, 可选): 随机种子
  - `output_format` (string, 可选): 输出格式
  - `extra_options` (object, 可选): 扩展选项
  - `aws_urls` (array, 可选): AWS上传URL
  - `wasabi_urls` (array, 可选): Wasabi上传URL
- **输出端口**:
  - `request` (object): 完整的请求数据

### 7. 模型服务节点 (digen_services)

#### ModelServiceNode - 模型服务节点
**功能**: 处理与模型服务的API通信
- **输入端口**:
  - `model` (string, 必需): 模型名称
  - `request` (object, 必需): 请求数据
  - `timeout` (number, 可选): 超时时间
- **输出端口**:
  - `local_urls` (array): 本地输出URL列表
  - `wasabi_urls` (array): Wasabi输出URL列表
  - `aws_urls` (array): AWS输出URL列表
  - `options` (object): 生成选项
  - `status` (string): 请求状态
  - `metadata` (object): 附加元数据

#### BatchModelServiceNode - 批量模型服务节点
**功能**: 批量处理模型服务请求
- **输入端口**:
  - `model` (string, 必需): 模型名称
  - `timeout` (number, 可选): 超时时间
- **输出端口**:
  - `local_urls` (array): 本地URL列表
  - `wasabi_urls` (array): Wasabi URL列表
  - `aws_urls` (array): AWS URL列表
  - `metadata` (array): 每个结果的元数据
  - `results` (array): 成功的结果
  - `success_count` (number): 成功数量
  - `error_count` (number): 错误数量
  - `errors` (array): 错误列表

### 8. 自定义节点 (custom_nodes)

#### QwenLLMNode - Qwen大语言模型节点
**功能**: 调用Qwen大语言模型服务进行文本生成
- **输入端口**:
  - `system_prompt` (string, 可选, 默认值: "You are a helpful assistant."): 系统提示词
  - `prompt` (string, 必需): 用户提示词
  - `max_tokens` (number, 可选, 默认值: 256): 最大生成token数
  - `temperature` (number, 可选, 默认值: 0.7): 生成温度，控制随机性
  - `top_p` (number, 可选, 默认值: 0.9): 核采样参数
  - `model` (string, 可选, 默认值: "Qwen3-30B-A3B-Instruct-2507-FP4"): 模型名称
    - 可选项: "DeepSeek-R1-0528-Qwen3-8B-abliterated", "Qwen3-30B-A3B-Instruct-2507-FP4"
- **输出端口**:
  - `content` (string): 生成的文本内容（自动过滤思考过程）
  - `usage` (object): 使用情况统计
  - `status` (string): 请求状态

**特殊功能**: 
- 自动过滤思考模式内容（`</think>`标签之前的内容）
- 支持系统提示词和用户提示词的分离设置

#### QwenVLNode - Qwen视觉语言模型节点
**功能**: 调用QwenVL视觉语言模型服务进行图像理解和文本生成
- **输入端口**:
  - `image_url` (string, 可选): 图像URL地址
  - `prompt` (string, 可选): 用户提示词
  - `system_prompt` (string, 可选): 系统提示词
  - `seed` (number, 可选, 默认值: 42): 随机种子
  - `max_tokens` (number, 可选, 默认值: 1024): 最大处理token数
- **输出端口**:
  - `response` (string): 增强后的提示词或分析结果

**特殊功能**:
- 支持纯文本处理（不提供图像URL时）
- 支持图像+文本的多模态处理
- 返回增强后的提示词，可用于后续处理

### 9. 控制流节点 (control)

#### SwitchNode - 条件分支节点
**功能**: 根据条件将数据路由到不同的输出端口，类似于编程中的 switch-case 语句

- **输入端口**:
  - `data` (any, 必需): 要路由的输入数据
  - `rules` (array, 必需): 路由规则列表
  - `mode` (string, 可选, 默认值: "first_match"): 匹配模式
    - `first_match`: 仅匹配第一个满足条件的规则
    - `all_matches`: 匹配所有满足条件的规则

- **输出端口**:
  - `output_0`, `output_1`, ... : 动态输出端口（根据构造时的 output_count 参数）
  - `fallback` (any): 默认输出（当没有规则匹配时使用）

**支持的操作符**:
- **比较操作符**: `equals`, `not_equals`, `greater`, `greater_equal`, `less`, `less_equal`
- **字符串操作符**: `contains`, `not_contains`, `starts_with`, `ends_with`, `regex`
- **空值检查**: `is_empty`, `is_not_empty`

**字段路径支持**:
- `"field"`: 直接字段访问
- `"user.name"`: 嵌套对象字段访问
- `"items.0"`: 数组索引访问
- `"user.addresses.0.city"`: 复杂嵌套路径

**规则格式**:
```json
[
  {
    "field": "user.age",           // 要检查的字段路径
    "operator": "greater_equal",   // 比较操作符
    "value": 18,                   // 比较值
    "output_index": 0              // 匹配时的输出端口索引
  },
  {
    "field": "category",
    "operator": "equals",
    "value": "premium",
    "output_index": 1
  }
]
```

**使用示例**:

**示例1: 用户分类路由**
```python
# 创建3个输出端口的Switch节点
switch_node = SwitchNode(output_count=3)

# 设置输入数据
switch_node.input_values = {
    "data": {
        "user": {"age": 25, "status": "active"},
        "score": 85,
        "category": "premium"
    },
    "rules": [
        {
            "field": "user.age",
            "operator": "greater_equal", 
            "value": 18,
            "output_index": 0  # 成年用户 -> output_0
        },
        {
            "field": "score",
            "operator": "greater",
            "value": 80,
            "output_index": 1  # 高分用户 -> output_1  
        },
        {
            "field": "category",
            "operator": "equals",
            "value": "premium",
            "output_index": 2  # 高级用户 -> output_2
        }
    ],
    "mode": "first_match"
}

# 执行处理
result = await switch_node.process()

# first_match 模式结果：
# {
#     "output_0": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "output_1": None,
#     "output_2": None, 
#     "fallback": None
# }
```

**示例2: 多条件匹配**
```python
# 使用 all_matches 模式
switch_node.input_values["mode"] = "all_matches"
result = await switch_node.process()

# all_matches 模式结果（所有匹配的输出都会被激活）：
# {
#     "output_0": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "output_1": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "output_2": {"user": {"age": 25, "status": "active"}, "score": 85, "category": "premium"},
#     "fallback": None
# }
```

**示例3: 字符串和正则匹配**
```python
switch_node.input_values = {
    "data": {"email": "user@example.com", "status": "active"},
    "rules": [
        {
            "field": "email",
            "operator": "contains",
            "value": "@example.com",
            "output_index": 0  # 公司邮箱
        },
        {
            "field": "status",
            "operator": "regex",
            "value": "^act.*",
            "output_index": 1  # 活跃状态
        }
    ],
    "mode": "first_match"
}
```

#### PassThroughNode - 透传节点
**功能**: 用于数据流控制和透传
- **输入端口**:
  - `data` (any, 必需): 要透传的真实数据
  - `control` (any, 可选): 控制信号
  - `pass_on_empty` (boolean, 可选, 默认值: false): 当控制信号为空时是否仍然透传
- **输出端口**:
  - `output` (any): 透传的数据输出

#### MergeNode - 合并节点
**功能**: 选择第一个不为空的输入作为输出，主要用于SwitchNode分支的结果汇总

- **输入端口**:
  - `input_0`, `input_1`, ... : 动态输入端口（根据构造时的 input_count 参数）
  - 所有输入端口都是可选的，允许为 None

- **输出端口**:
  - `output` (any): 合并后的输出（第一个非空值）
  - `selected_index` (number): 被选中的输入端口索引（-1表示没有选中任何端口）
  - `has_result` (boolean): 是否有非空结果

**空值判断规则**:
- `None` 被认为是空值
- 空列表 `[]` 被认为是空值
- 空字典 `{}` 被认为是空值
- 空字符串或仅包含空白的字符串被认为是空值
- 其他类型的值（包括数字0、布尔值false）被认为是非空值

**典型使用场景**:
1. **SwitchNode结果汇总**: `SwitchNode的多个输出分支 -> MergeNode -> 后续节点`
2. **多数据源选择**: 从多个可选数据源中选择第一个可用的
3. **条件分支合并**: 将条件分支的结果汇总为单一输出

**使用示例**:

**示例1: 与SwitchNode配合使用**
```python
# 创建Switch节点和Merge节点
switch_node = SwitchNode(output_count=3)
merge_node = MergeNode(input_count=4)  # 3个输出分支 + 1个fallback

# 设置Switch节点
switch_node.input_values = {
    "data": {"user_type": "premium", "score": 95},
    "rules": [
        {
            "field": "user_type",
            "operator": "equals",
            "value": "premium",
            "output_index": 0
        },
        {
            "field": "score",
            "operator": "greater",
            "value": 90,
            "output_index": 1
        }
    ],
    "mode": "first_match"
}

# 执行Switch节点
switch_result = await switch_node.process()
# switch_result = {
#     "output_0": {"user_type": "premium", "score": 95},  # 匹配的输出
#     "output_1": None,
#     "output_2": None,
#     "fallback": None
# }

# 设置Merge节点，接收Switch的所有输出
merge_node.input_values = {
    "input_0": switch_result["output_0"],
    "input_1": switch_result["output_1"], 
    "input_2": switch_result["output_2"],
    "input_3": switch_result["fallback"]
}

# 执行Merge节点
merge_result = await merge_node.process()
# merge_result = {
#     "output": {"user_type": "premium", "score": 95},  # 第一个非空值
#     "selected_index": 0,  # 选中了input_0
#     "has_result": True
# }
```

**示例2: 多数据源选择**
```python
merge_node = MergeNode(input_count=3)
merge_node.input_values = {
    "input_0": None,  # 第一个数据源为空
    "input_1": [],    # 第二个数据源为空列表
    "input_2": {"data": "from source 3"}  # 第三个数据源有数据
}

result = await merge_node.process()
# result = {
#     "output": {"data": "from source 3"},
#     "selected_index": 2,
#     "has_result": True
# }
```

**示例3: 所有输入都为空的情况**
```python
merge_node = MergeNode(input_count=2)
merge_node.input_values = {
    "input_0": None,
    "input_1": ""  # 空字符串
}

result = await merge_node.process()
# result = {
#     "output": None,
#     "selected_index": -1,
#     "has_result": False
# }
```

#### ForEachNode - 循环节点
**功能**: 对列表中的每个项目执行子工作流，实现动态工作流执行

- **输入端口**:
  - `items` (array, 必需): 要迭代的项目列表
  - `sub_workflow` (object, 必需): 子工作流定义（包含节点和连接）
  - `result_node_id` (string, 必需): 子工作流中用于收集结果的节点ID
  - `result_port_name` (string, 可选, 默认值: "result"): 结果节点的输出端口名
  - `parallel` (boolean, 可选, 默认值: false): 是否并行执行迭代
  - `continue_on_error` (boolean, 可选, 默认值: true): 出错时是否继续处理后续项目
  - `max_iterations` (number, 可选): 最大迭代次数限制
  - `global_vars` (object, 可选): 传递给每个ForEachItemNode的全局变量

- **输出端口**:
  - `results` (array): 每次成功迭代的结果列表
  - `sub_workflow_results` (array): 完整的子工作流执行结果（包含每次迭代的详细信息）
  - `item_value` (any): 最后处理的项目值
  - `current_index` (number): 最后处理的项目索引
  - `total_count` (number): 实际处理的项目总数
  - `success_count` (number): 成功处理的项目数量
  - `error_count` (number): 处理失败的项目数量
  - `errors` (array): 错误详情列表

**核心特性**:
1. **动态执行**: 为每个项目创建并执行独立的工作流实例
2. **结果收集**: 自动收集每次迭代的结果
3. **错误处理**: 可配置在出错时继续或停止
4. **进度跟踪**: 提供成功/失败统计信息
5. **并行执行**: 支持并行处理以提高性能
6. **上下文注入**: 自动将当前项目、索引和全局变量注入到子工作流

**子工作流定义格式**:
```json
{
  "nodes": [
    {
      "id": "item_node",
      "type": "ForEachItemNode"
    },
    {
      "id": "process_node", 
      "type": "QwenLLMNode"
    }
  ],
  "connections": [
    {
      "from_node": "item_node",
      "from_port": "item",
      "to_node": "process_node", 
      "to_port": "prompt"
    }
  ]
}
```

**使用示例**:

**示例1: 批量文本处理**
```python
# 创建ForEach节点
foreach_node = ForEachNode()

# 设置输入
foreach_node.input_values = {
    "items": ["处理这段文本", "分析这个内容", "总结这些信息"],
    "sub_workflow": {
        "nodes": [
            {
                "id": "item_input",
                "type": "ForEachItemNode"
            },
            {
                "id": "llm_processor",
                "type": "QwenLLMNode",
                "input_values": {
                    "system_prompt": "你是一个文本处理助手",
                    "max_tokens": 100
                }
            }
        ],
        "connections": [
            {
                "from_node": "item_input",
                "from_port": "item",
                "to_node": "llm_processor",
                "to_port": "prompt"
            }
        ]
    },
    "result_node_id": "llm_processor",
    "result_port_name": "content",
    "parallel": False,
    "continue_on_error": True
}

# 执行处理
result = await foreach_node.process()

# 结果示例：
# {
#     "results": ["处理结果1", "处理结果2", "处理结果3"],
#     "sub_workflow_results": [
#         {
#             "index": 0,
#             "item": "处理这段文本",
#             "result": "处理结果1",
#             "sub_workflow_results": {...}  # 完整的子工作流执行结果
#         },
#         ...
#     ],
#     "total_count": 3,
#     "success_count": 3,
#     "error_count": 0,
#     "errors": []
# }
```

**示例2: 并行处理与错误处理**
```python
foreach_node.input_values = {
    "items": [1, 2, 3, 4, 5],
    "sub_workflow": {
        "nodes": [
            {
                "id": "item_input",
                "type": "ForEachItemNode"
            },
            {
                "id": "math_processor",
                "type": "MathOperationNode",
                "input_values": {
                    "operation": "multiply",
                    "b": 2
                }
            }
        ],
        "connections": [
            {
                "from_node": "item_input",
                "from_port": "item", 
                "to_node": "math_processor",
                "to_port": "a"
            }
        ]
    },
    "result_node_id": "math_processor",
    "result_port_name": "result",
    "parallel": True,  # 并行执行
    "continue_on_error": False,  # 遇到错误时停止
    "max_iterations": 3  # 最多处理3个项目
}

result = await foreach_node.process()
# 并行处理前3个项目: [2, 4, 6]
```

**示例3: 使用全局变量**
```python
foreach_node.input_values = {
    "items": ["文本1", "文本2", "文本3"],
    "global_vars": {
        "language": "中文",
        "style": "正式"
    },
    "sub_workflow": {
        "nodes": [
            {
                "id": "item_input",
                "type": "ForEachItemNode"
            },
            {
                "id": "text_combiner",
                "type": "TextCombinerNode",
                "input_values": {
                    "prompt": "请用{language}以{style}风格处理: {text_a}"
                }
            }
        ],
        "connections": [
            {
                "from_node": "item_input",
                "from_port": "item",
                "to_node": "text_combiner", 
                "to_port": "text_a"
            },
            {
                "from_node": "item_input",
                "from_port": "global_vars",
                "to_node": "text_combiner",
                "to_port": "text_b"  # 通过复杂逻辑处理全局变量
            }
        ]
    },
    "result_node_id": "text_combiner",
    "result_port_name": "combined_text"
}
```

#### ForEachItemNode - 循环项目节点
**功能**: 在ForEach子工作流中接收当前项目
- **输入端口**:
  - `foreach_item` (any, 必需): 来自ForEach循环的当前项目
  - `foreach_index` (number, 可选): 当前项目索引
  - `foreach_global_vars` (object, 可选): 全局变量
- **输出端口**:
  - `item` (any): 当前处理的项目
  - `index` (number): 项目索引
  - `global_vars` (object): 全局变量

## 使用建议

### 1. 基本工作流构建
- 使用基础类型节点作为数据输入点
- 使用文本处理节点进行数据预处理
- 使用列表和字典处理节点进行数据结构操作

### 2. 模型调用流程
1. 使用 ModelRequestInputNode 准备输入数据
2. 使用 ModelRequestNode 配置请求参数
3. 使用 ModelServiceNode 执行模型调用
4. 处理返回的结果数据

### 3. 批量处理
- 使用 BatchModelRequestInputNode 准备批量输入
- 使用 BatchModelRequestNode 配置批量请求
- 使用 BatchModelServiceNode 执行批量处理

### 4. 条件控制
- 使用 SwitchNode 实现条件分支
- 使用 PassThroughNode 控制数据流
- 使用 MergeNode 合并分支结果

### 5. 循环处理
- 使用 ForEachNode 对列表项目进行循环处理
- 在子工作流中使用 ForEachItemNode 接收循环项目
- 配置适当的错误处理和并行选项

### 6. 自定义AI模型调用
- 使用 QwenLLMNode 进行纯文本生成和对话
- 使用 QwenVLNode 进行图像理解和多模态处理
- 可以与其他节点组合构建复杂的AI工作流
- 支持提示词工程和参数调优

## 注意事项

1. **数据类型**: 确保输入端口的数据类型匹配
2. **必需参数**: 标记为必需的输入端口必须提供值
3. **错误处理**: 大多数节点在输入无效时会抛出异常
4. **性能考虑**: 批量处理节点适用于大量数据处理
5. **工作流设计**: 合理使用控制流节点可以构建复杂的条件逻辑

这些节点可以灵活组合，构建从简单的数据处理到复杂的AI模型调用工作流。

## 使用示例

### 示例1: 基本文本生成工作流
```
TextInputNode -> QwenLLMNode -> TextStripNode
```
1. 使用 TextInputNode 提供用户输入
2. 使用 QwenLLMNode 生成AI回复
3. 使用 TextStripNode 清理输出格式

### 示例2: 图像分析和文本处理工作流
```
TextInputNode (image_url) -> QwenVLNode -> TextToDictNode -> DictGetNode
```
1. 提供图像URL和分析提示
2. 使用 QwenVLNode 分析图像并生成结构化描述
3. 将结果转换为字典格式
4. 提取特定字段信息

### 示例3: 批量文本处理工作流
```
TextToListNode -> ForEachNode -> QwenLLMNode -> ListCreateNode
```
1. 将输入文本分割为列表
2. 使用 ForEachNode 对每个项目进行循环处理
3. 在子工作流中使用 QwenLLMNode 处理每个文本
4. 收集所有处理结果

### 示例4: 条件AI处理工作流
```
TextInputNode -> SwitchNode -> [QwenLLMNode | QwenVLNode] -> MergeNode
```
1. 根据输入内容类型进行条件判断
2. 文本内容路由到 QwenLLMNode
3. 包含图像URL的内容路由到 QwenVLNode
4. 使用 MergeNode 合并不同分支的结果

### 示例5: 复杂的控制流组合工作流
```
ListCreateNode -> ForEachNode -> SwitchNode -> [处理分支A | 处理分支B] -> MergeNode -> 结果收集
```

**完整示例代码**:
```python
# 步骤1: 创建数据列表
list_create_node = ListCreateNode()
list_create_node.input_values = {
    "value_1": {"type": "text", "content": "分析这段文字"},
    "value_2": {"type": "image", "content": "http://example.com/image.jpg", "prompt": "描述这张图片"},
    "value_3": {"type": "text", "content": "总结这个主题"}
}

# 步骤2: 使用ForEach处理每个项目
foreach_node = ForEachNode()
foreach_node.input_values = {
    "items": list_create_node.output["result"],
    "sub_workflow": {
        "nodes": [
            {
                "id": "item_input",
                "type": "ForEachItemNode"
            },
            {
                "id": "type_switch", 
                "type": "SwitchNode",
                "constructor_args": {"output_count": 2}
            },
            {
                "id": "text_processor",
                "type": "QwenLLMNode",
                "input_values": {
                    "system_prompt": "你是一个文本分析专家"
                }
            },
            {
                "id": "image_processor", 
                "type": "QwenVLNode"
            },
            {
                "id": "result_merger",
                "type": "MergeNode",
                "constructor_args": {"input_count": 3}
            }
        ],
        "connections": [
            # ForEachItem -> Switch
            {
                "from_node": "item_input",
                "from_port": "item",
                "to_node": "type_switch",
                "to_port": "data"
            },
            # Switch -> 不同处理器
            {
                "from_node": "type_switch",
                "from_port": "output_0",
                "to_node": "text_processor",
                "to_port": "prompt"
            },
            {
                "from_node": "type_switch", 
                "from_port": "output_1",
                "to_node": "image_processor",
                "to_port": "image_url"
            },
            # 处理器 -> Merger
            {
                "from_node": "text_processor",
                "from_port": "content", 
                "to_node": "result_merger",
                "to_port": "input_0"
            },
            {
                "from_node": "image_processor",
                "from_port": "response",
                "to_node": "result_merger", 
                "to_port": "input_1"
            },
            {
                "from_node": "type_switch",
                "from_port": "fallback",
                "to_node": "result_merger",
                "to_port": "input_2"
            }
        ]
    },
    "result_node_id": "result_merger",
    "result_port_name": "output",
    "parallel": True
}

# 在子工作流中，Switch节点的规则配置
switch_rules = [
    {
        "field": "type",
        "operator": "equals", 
        "value": "text",
        "output_index": 0  # 文本处理分支
    },
    {
        "field": "type",
        "operator": "equals",
        "value": "image", 
        "output_index": 1  # 图像处理分支
    }
]

# 执行整个工作流
result = await foreach_node.process()

# 最终结果包含每个项目的处理结果：
# {
#     "results": [
#         "文本分析结果1",
#         "图像描述结果", 
#         "文本分析结果2"
#     ],
#     "success_count": 3,
#     "error_count": 0
# }
```

**工作流执行流程**:
1. **ListCreateNode**: 创建包含不同类型数据的列表
2. **ForEachNode**: 对每个数据项执行子工作流
3. **子工作流中的SwitchNode**: 根据数据类型路由到不同处理分支
   - `type="text"` → QwenLLMNode (文本处理)
   - `type="image"` → QwenVLNode (图像处理)
   - 其他类型 → fallback分支
4. **子工作流中的MergeNode**: 合并不同分支的处理结果
5. **ForEachNode收集**: 收集所有子工作流的结果

**关键优势**:
- **灵活性**: 可以处理混合类型的数据
- **可扩展性**: 容易添加新的数据类型和处理分支
- **并行性**: 支持并行处理提高效率
- **容错性**: 单个项目失败不影响其他项目
- **可观测性**: 详细的执行统计和错误信息
