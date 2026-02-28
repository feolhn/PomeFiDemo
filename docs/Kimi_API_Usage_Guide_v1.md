# 0. Kimi API 使用手册

## 一、 目录大纲、每个章节关键词提炼

| 索引   | 目录大纲   | 每个章节关键词提炼    |
| ------ | ------ | -------------- |
| 1 | Chat | 基础对话、接口兼容 |
| 2 | Tool Use | 函数定义、外部链接 |
| 3 | Partial Mode | 预填回复、角色强化 |
| 4 | 文件接口 | 内容抽取、OCR识别 |
| 5 | 计算 Token | 成本预估、视觉计量 |
| 6 | 查询余额 | 账单查看、额度监控 |
| 7 | Kimi K2.5 多模态模型 | 全能架构、图文视频 |
| 8 | 使用思考模型 | 深度推理、多步工具 |
| 9 | 流式输出指南 | 逐词生成、SSE协议 |
| 10 | Tool Calls 能力说明 | 逻辑拆解、多步交互 |
| 11 | 使用联网搜索工具 | 内置搜索、实时数据 |
| 12 | JSON Mode 使用说明 | 结构输出、格式约束 |
| 13 | Kimi 官方工具集成说明 | Formula引擎、逻辑算力 |
| 14 | Kimi K2 模型搭建 Agent 指南 | 系统指令、研报生成 |
| 15 | Prompt 最佳实践 | 指令优化、Few-shot |
| 16 | 常见问题及解决方案 | 报错排查、功能边界 |

## 二、 全文最核心注意点 (Kimi 特殊规定)

### 1. 模型参数限制 [索引 7, 8]

-   **Kimi K2.5/Thinking**:
    
    -   **思考模式**: 必须 `temperature=1.0` (K2.5 为固定值)，`top_p=0.95`，`n=1`。
        
    -   **工具约束**: 开启思考时 `tool_choice` 仅支持 "auto" 或 "none"。
        
    -   **Tokens**: `max_tokens` 建议设为 `16000` 以上，以容纳思考内容。
        
-   **常规模型**: `moonshot-v1` 默认 `temperature=0.0`，`kimi-k2` 默认 `0.6`。
    

### 2. 输出格式与引导 [索引 3, 12]

-   **模式冲突**: **严禁**同时混用 `Partial Mode` 和 `response_format=json_object`。
    
-   **Partial Mode**: 在 `assistant` 消息中增加 `"partial": True`；API 返回不含 leading_text，需手动拼接。
    
-   **JSON Mode**: 仅支持生成 `JSON Object`，不支持 `JSON Array`。
    

### 3. 工具调用 (Tool Calls) [索引 10, 11, 13]

-   **类型区分**: 工具分为 `builtin_function` (官方内置，如 `$web_search`) 和 `function` (自定义函数)。
    
-   **内置搜索**: 调用 `$web_search` 产生的 `arguments` 只需原封不动返回给 API 即可执行。
    
-   **上下文一致性**: 在多步调用中，必须完整保留 `assistant` 消息里的 `reasoning_content` (思考内容)，否则会报错。
    
-   **废弃说明**: Kimi 不再支持 OpenAI 的 `function_call` 参数，必须统一使用 `tool_calls`。
    

### 4. SDK 与 兼容性 [索引 8, 9, 16]

-   **字段访问**: OpenAI SDK 的对象不提供 `.reasoning_content` 属性，必须使用 `getattr(choice.delta, "reasoning_content")` 访问。
    
-   **流式判定**: 应始终以接收到 `data: [DONE]` 作为传输结束的唯一标志，而非 `finish_reason`。
    
-   **重试机制**: OpenAI SDK 默认开启 2 次重试，错误请求也会消耗账户的 RPM 额度。
    
-   **服务隔离**: 国内 (`api.moonshot.cn`) 与境外 (`api.moonshot.ai`) 平台的 API Key 互不兼容。
    

### 5. 文件与多模态处理 [索引 4, 16]

-   **引用限制**: 不支持通过 `file_id` 直接引用文件作为对话上下文，需先调用接口抽取文本再作为 `system` 消息。
    
-   **视觉输入**: 图片/视频仅支持 Base64 或 `ms://` 协议，不支持直接传入外部 URL 地址。
    
-   **解析边界**: 图片上传若不含文字（OCR无法识别）会导致解析失败报错。


# 1. Chat

## 基本信息

## [](#公开的服务地址)

```text
https://api.moonshot.cn
```

Moonshot 提供基于 HTTP 的 API 服务接入，并且对大部分 API，我们兼容了 OpenAI SDK。

## 快速开始

## [](#单轮对话)

OpenAI 官方 SDK 支持 [Python (opens in a new tab)](https://github.com/openai/openai-python) 和 [Node.js (opens in a new tab)](https://github.com/openai/openai-node) 两种语言，使用 OpenAI SDK 和 Curl 与 API 进行交互的代码如下：

```python
from openai import OpenAI
 
client = OpenAI(
    api_key = "$MOONSHOT_API_KEY",
    base_url = "https://api.moonshot.cn/v1",
)
 
completion = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"}
    ],
    temperature = 0.6,
)
 
print(completion.choices[0].message.content)
```

其中 $MOONSHOT\_API\_KEY 需要替换为您在平台上创建的 API Key。

使用 OpenAI SDK 时运行文档中的代码时，需要保证 Python 版本至少为 3.7.1，Node.js 版本至少为 18，OpenAI SDK 版本不低于 1.0.0。

```bash
pip install --upgrade 'openai>=1.0'
```

> 我们可以这样简单检验下自己库的版本：
> 
> ```bash
> python -c 'import openai; print("version =",openai.__version__)'
> # 输出可能是 version = 1.10.0，表示当前 python 实际使用了 openai 的 v1.10.0 的库
> ```

## [](#多轮对话)

上面的单轮对话的例子中语言模型将用户信息列表作为输入，并将模型生成的信息作为输出返回。 有时我们也可以将模型输出的结果继续作为输入的一部分以实现多轮对话，下面是一组简单的实现多轮对话的例子：

```python
from openai import OpenAI
 
client = OpenAI(
    api_key = "$MOONSHOT_API_KEY",
    base_url = "https://api.moonshot.cn/v1",
)
 
history = [
    {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"}
]
 
def chat(query, history):
    history.append({
        "role": "user", 
        "content": query
    })
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",
        messages=history,
        temperature=0.6,
    )
    result = completion.choices[0].message.content
    history.append({
        "role": "assistant",
        "content": result
    })
    return result
 
print(chat("地球的自转周期是多少？", history))
print(chat("月球呢？", history))
```

值得注意的是，随着对话的进行，模型每次需要传入的 token 都会线性增加，必要时，需要一些策略进行优化，例如只保留最近几轮对话。

## API 说明

## [](#chat-completion)

### [](#请求地址)

```text
POST https://api.moonshot.cn/v1/chat/completions
```

### [](#请求内容)

#### [](#示例)

```json
{
    "model": "kimi-k2-turbo-preview",
    "messages": [
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
        },
        { "role": "user", "content": "你好，我叫李雷，1+1等于多少？" }
    ],
    "temperature": 0.6
}
```

#### [](#字段说明)

| 字段 | 是否必须 | 说明 | 类型 | 取值 |
| --- | --- | --- | --- | --- |
| messages | required | 包含迄今为止对话的消息列表 | List\[Dict\] | 这是一个结构体的列表，每个元素类似如下：`{"role": "user", "content": "你好"}` role 只支持 `system`,`user`,`assistant` 其一，content 不得为空。 content字段可以是string，也可以是 List\[Dict\] ，详见 [content字段说明](https://platform.moonshot.cn/docs/api/chat#content%E5%AD%97%E6%AE%B5%E8%AF%B4%E6%98%8E) |
| model | required | Model ID, 可以通过 List Models 获取 | string | 目前是 `kimi-k2.5`,`kimi-k2-0905-preview`, `kimi-k2-0711-preview`, `kimi-k2-turbo-preview`, `kimi-k2-thinking-turbo`, `kimi-k2-thinking`, `moonshot-v1-8k`,`moonshot-v1-32k`,`moonshot-v1-128k`, `moonshot-v1-auto`,`moonshot-v1-8k-vision-preview`,`moonshot-v1-32k-vision-preview`,`moonshot-v1-128k-vision-preview`其一 |
| max\_tokens | optional | 已废弃，请参考 max\_completion\_tokens | int | \- |
| max\_completion\_tokens | optional | 聊天完成时生成的最大 token 数。如果到生成了最大 token 数个结果仍然没有结束，finish reason 会是 "length", 否则会是 "stop" | int | 这个值建议按需给个合理的值，如果不给的话，我们会给一个不错的整数比如 1024。**特别要注意的是**，这个 `max_completion_tokens` 是指您期待我们**返回**的 token 长度，而不是输入 + 输出的总长度。比如对一个 `moonshot-v1-8k` 模型，它的最大输入 + 输出总长度是 8192，当输入 messages 总长度为 4096 的时候，您最多只能设置为 4096，否则我们服务会返回不合法的输入参数（ invalid\_request\_error ），并拒绝回答。如果您希望获得"输入的精确 token 数"，可以使用下面的"计算 Token" API 使用我们的计算器获得计数 |
| temperature | optional | 使用什么采样温度，介于 0 和 1 之间。较高的值（如 0.7）将使输出更加随机，而较低的值（如 0.2）将使其更加集中和确定性。 | float | 设置值域须为 `[0, 1]` ，`moonshot-v1` 系列模型默认为 0.0，`kimi-k2` 系列模型默认为 0.6， `kimi-k2-thinking` 系列模型默认为 1.0。`kimi-k2.5` 模型不能修改该参数。 |
| top\_p | optional | 另一种采样方法，即模型考虑概率质量为 top\_p 的标记的结果。因此，0.1 意味着只考虑概率质量最高的 10% 的标记。一般情况下，我们建议改变这一点或温度，但不建议 同时改变 | float | `moonshot-v1` 系列和 `kimi-k2` 模型默认为 1.0, `kimi-k2.5` 默认值为0.95且不可修改 |
| n | optional | 为每条输入消息生成多少个结果 | int | `moonshot-v1` 系列和 `kimi-k2` 默认为 1，不得大于 5；特别的，当 temperature 非常小靠近 0 的时候，我们只能返回 1 个结果，如果这个时候 n 已经设置并且 > 1，我们的服务会返回不合法的输入参数(invalid\_request\_error)。`kimi-k2.5` 模型默认值为1且不可修改。 |
| presence\_penalty | optional | 存在惩罚，介于-2.0到2.0之间的数字。正值会根据新生成的词汇是否出现在文本中来进行惩罚，增加模型讨论新话题的可能性 | float | 默认为 0，`kimi-k2.5` 模型不能修改该参数。 |
| frequency\_penalty | optional | 频率惩罚，介于-2.0到2.0之间的数字。正值会根据新生成的词汇在文本中现有的频率来进行惩罚，减少模型一字不差重复同样话语的可能性 | float | 默认为 0，`kimi-k2.5` 模型不能修改该参数。 |
| response\_format | optional | 设置为 `{"type": "json_object"}` 可启用 JSON 模式，从而保证模型生成的信息是有效的 JSON。当你将 response\_format 设置为 `{"type": "json_object"}` 时，**你需要在 prompt 中明确地引导模型输出 JSON 格式的内容，并告知模型该 JSON 的具体格式，否则将可能导致不符合预期的结果**。 | object | 默认为 {"type": "text"} |
| stop | optional | 停止词，当全匹配这个（组）词后会停止输出，这个（组）词本身不会输出。最多不能超过 5 个字符串，每个字符串不得超过 32 字节 | String, List\[String\] | 默认 null |
| thinking | optional | 仅对 `kimi-k2.5` 有效。 该参数控制模型是否启用思考。 | object | 默认值为`{"type": "enabled"}`. 只能为 `{"type": "enabled"}` 或 `{"type": "disabled"}` |
| stream | optional | 是否流式返回 | bool | 默认 false, 可选 true |
| stream\_options.include\_usage | optional | 如果设置，将在 `data: [DONE]` 消息之前额外流式返回一个 chunk。该 chunk 的 usage 字段显示整个请求的 token 使用统计，choices 字段始终为空数组。所有其他 chunk 也会包含 usage 字段，但值为 null。注意：如果流被中断，您可能无法收到包含请求总 token 使用量的最终 usage chunk | bool | 默认 false |
| prompt\_cache\_key | optional | 用于缓存相似请求的响应，以优化缓存命中率 | string | 默认 null。对于 Coding Agent，通常使用 session id 或 task id，代表一次会话，如果中途退出后 resume，该值也应保持不变。对于 Kimi Code Plan，为了提高缓存命中率，此字段为必填。对于其他涉及多轮对话的 Agent，也建议实现此字段 |
| safety\_identifier | optional | 一个稳定的标识符，用于帮助检测可能违反使用政策的应用用户。该 ID 应是唯一标识每个用户的字符串，建议对用户名或电子邮件地址进行哈希处理，以避免发送任何可识别身份的信息 | string | 默认 null |

#### [](#content字段说明)

`content` 字段可以多种类型的取值，包括

+   最简单的情况，普通的string
+   有复杂的内容，则可以是List\[Dict\], 其中每个Dict可以有如下字段
    +   `type`, 必需。标识元素类型，应为`text`, `image_url` 或 `video_url` 中的一种
    +   `text`, 对应上面 `type` 为 `text` 的情况，其值应为纯文本
    +   `image_url`, 对应上面 `type` 为 `image_url` 的情况，其值应为一个Dict, 表示图片内容，比如 `{"url": "data:image/png;base64,abc123xxxxx==}`
    +   `video_url`, 对应上面 `type` 为 `video_url` 的情况，其值应为一个Dict, 表示图片内容，比如 `{"url": "data:image/png;base64,abc123xxxxx==}`

以下几种都是合法的 content 字段

+   `"你好"`
+   `[{"type": "text", "text": "你好"}]`
+   `[{"type": "image_url", "image_url": {"url": "data:image/png;base64,abc123xxxxx=="}}]`
+   `[{"type": "video_url", "video_url": {"url": "data:video/mp4;base64,def456yyyyy=="}}]`
+   `[{"type": "text", "text": "这是什么？"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc123xxxxx=="}}]`

**注意** `image_url` 和 `video_url` 的url字段支持 base64 格式和 `ms://<file_id>` 格式，详见 [使用 Kimi 视觉模型（Vision）](https://platform.moonshot.cn/docs/guide/use-kimi-vision-model)

### [](#返回内容)

对非 stream 格式的，返回类似如下：

```json
{
    "id": "cmpl-04ea926191a14749b7f2c7a48a68abc6",
    "object": "chat.completion",
    "created": 1698999496,
    "model": "kimi-k2-turbo-preview",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " 你好，李雷！1+1等于2。如果你有其他问题，请随时提问！"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 19,
        "completion_tokens": 21,
        "total_tokens": 40,
        "cached_tokens": 10  # 缓存命中的 token 数量，只有支持自动缓存的模型会返回该字段
    }
}
```

对 stream 格式的，返回类似如下：

```json
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}
 
...
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{"content":"。"},"finish_reason":null}]}
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{},"finish_reason":"stop","usage":{"prompt_tokens":19,"completion_tokens":13,"total_tokens":32}}]}
 
data: [DONE]
```


## [](#错误说明)

以下是一组错误返回的例子：

```text
{
    "error": {
        "type": "content_filter",
        "message": "The request was rejected because it was considered high risk"
    }
}
```

下面是主要错误的说明：

| HTTP Status Code | error type | error message | 详细描述 |
| --- | --- | --- | --- |
| 400 | content\_filter | The request was rejected because it was considered high risk | 内容审查拒绝，您的输入或生成内容可能包含不安全或敏感内容，请您避免输入易产生敏感内容的提示语，谢谢 |
| 400 | invalid\_request\_error | Invalid request: {error\_details} | 请求无效，通常是您请求格式错误或者缺少必要参数，请检查后重试 |
| 400 | invalid\_request\_error | Input token length too long | 请求中的 tokens 长度过长，请求不要超过模型 tokens 的最长限制 |
| 400 | invalid\_request\_error | Your request exceeded model token limit : {max\_model\_length} | 请求的 tokens 数和设置的 max\_tokens 加和超过了模型规格长度，请检查请求体的规格或选择合适长度的模型 |
| 400 | invalid\_request\_error | Invalid purpose: only 'file-extract' accepted | 请求中的目的（purpose）不正确，当前只接受 'file-extract'，请修改后重新请求 |
| 400 | invalid\_request\_error | File size is too large, max file size is 100MB, please confirm and re-upload the file | 上传的文件大小超过了限制，请重新上传 |
| 400 | invalid\_request\_error | File size is zero, please confirm and re-upload the file | 上传的文件大小为 0，请重新上传 |
| 400 | invalid\_request\_error | The number of files you have uploaded exceeded the max file count {max\_file\_count}, please delete previous uploaded files | 上传的文件总数超限，请删除不用的早期的文件后重新上传 |
| 401 | invalid\_authentication\_error | Invalid Authentication | 鉴权失败，请检查 apikey 是否正确，请修改后重试 |
| 401 | incorrect\_api\_key\_error | Incorrect API key provided | 鉴权失败，请检查 apikey 是否提供以及 apikey 是否正确，请修改后重试 |
| 429 | exceeded\_current\_quota\_error | Your account {organization-id}<{ak-id}> is suspended, please check your plan and billing details | 账户余额不足，已停用，请检查您的账户余额 |
| 403 | permission\_denied\_error | The API you are accessing is not open | 访问的 API 暂未开放 |
| 403 | permission\_denied\_error | You are not allowed to get other user info | 访问其他用户信息的行为不被允许，请检查 |
| 404 | resource\_not\_found\_error | Not found the model {model-id} or Permission denied | 不存在此模型或者没有授权访问此模型，请检查后重试 |
| 429 | engine\_overloaded\_error | The engine is currently overloaded, please try again later | 当前并发请求过多，节点限流中，请稍后重试；建议充值升级 tier，享受更丝滑的体验 |
| 429 | exceeded\_current\_quota\_error | You exceeded your current token quota: <{organization\_id}> {token\_credit}, please check your account balance | 账户额度不足，请检查账户余额，保证账户余额可匹配您 tokens 的消耗费用后重试 |
| 429 | rate\_limit\_reached\_error | Your account {organization-id}<{ak-id}> request reached organization max concurrency: {Concurrency}, please try again after {time} seconds | 请求触发了账户并发个数的限制，请等待指定时间后重试 |
| 429 | rate\_limit\_reached\_error | Your account {organization-id}<{ak-id}> request reached organization max RPM: {RPM}, please try again after {time} seconds | 请求触发了账户 RPM 速率限制，请等待指定时间后重试 |
| 429 | rate\_limit\_reached\_error | Your account {organization-id}<{ak-id}> request reached organization TPM rate limit, current:{current\_tpm}, limit:{max\_tpm} | 请求触发了账户 TPM 速率限制，请等待指定时间后重试 |
| 429 | rate\_limit\_reached\_error | Your account {organization-id}<{ak-id}> request reached organization TPD rate limit, current:{current\_tpd}, limit:{max\_tpd} | 请求触发了账户 TPD 速率限制，请等待指定时间后重试 |
| 500 | server\_error | Failed to extract file: {error} | 解析文件失败，请重试 |
| 500 | unexpected\_output | invalid state transition | 内部错误，请联系管理员 |

# 2. Tool Use

## 工具调用

学会使用工具是智能的一个重要特征，在 Kimi 大模型中我们同样如此。Tool Use 或者 Function Calling 是 Kimi 大模型的一个重要功能，在调用 API 使用模型服务时，您可以在 Messages 中描述工具或函数，并让 Kimi 大模型智能地选择输出一个包含调用一个或多个函数所需的参数的 JSON 对象，实现让 Kimi 大模型链接使用外部工具的目的。

下面是一个简单的工具调用的例子：

```python
{
  "model": "kimi-k2-turbo-preview",
  "messages": [
    {
      "role": "user",
      "content": "编程判断 3214567 是否是素数。"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "CodeRunner",
        "description": "代码执行器，支持运行 python 和 javascript 代码",
        "parameters": {
          "properties": {
            "language": {
              "type": "string",
              "enum": ["python", "javascript"]
            },
            "code": {
              "type": "string",
              "description": "代码写在这里"
            }
          },
          "type": "object"
        }
      }
    }
  ]
}
```

其中在 tools 字段，我们可以增加一组可选的工具列表。

每个工具列表必须包括一个类型，在 function 结构体中我们需要包括 name（它的需要遵守这样的正则表达式作为规范: ^\[a-zA-Z\_\]\[a-zA-Z0-9-\_\]63$），这个名字如果是一个容易理解的英文可能会更加被模型所接受。以及一段 description 或者 enum，其中 description 部分介绍它能做什么功能，方便模型来判断和选择。 function 结构体中必须要有个 parameters 字段，parameters 的 root 必须是一个 object，内容是一个 json schema 的子集（之后我们会给出具体文档介绍相关技术细节）。 tools 的 function 个数目前不得超过 128 个。

和别的 API 一样，我们可以通过 Chat API 调用它。

```python
from openai import OpenAI
 
client = OpenAI(
    api_key = "$MOONSHOT_API_KEY",
    base_url = "https://api.moonshot.cn/v1",
)
 
completion = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "user", "content": "编程判断 3214567 是否是素数。"}
    ],
    tools = [{
        "type": "function",
        "function": {
            "name": "CodeRunner",
            "description": "代码执行器，支持运行 python 和 javascript 代码",
            "parameters": {
                "properties": {
                    "language": {
                        "type": "string",
                        "enum": ["python", "javascript"]
                    },
                    "code": {
                        "type": "string",
                        "description": "代码写在这里"
                    }
                },
            "type": "object"
            }
        }
    }],
    temperature = 0.6,
)
 
print(completion.choices[0].message)
```

### [](#工具配置)

你也可以使用一些 Agent 平台例如 [Coze (opens in a new tab)](https://coze.cn/)、[Bisheng (opens in a new tab)](https://github.com/dataelement/bisheng)、[Dify (opens in a new tab)](https://github.com/langgenius/dify/) 和 [LangChain (opens in a new tab)](https://github.com/langchain-ai/langchain) 等框架来创建和管理这些工具，并配合 Kimi 大模型设计更加复杂的工作流。


# 3. Partial Mode

## Partial Mode

在使用大模型时，有时我们希望通过预填（Prefill）部分模型回复来引导模型的输出。在 Kimi 大模型中，我们提供 Partial Mode 来实现这一功能，它可以帮助我们控制输出格式，引导输出内容，以及让模型在角色扮演场景中保持更好的一致性。您只需要在最后一个 role 为 assistant 的 messages 条目中，增加 "partial": True 即可开启 partial mode。

```text
 {"role": "assistant", "content": leading_text, "partial": True},
```

**注意！请勿混用 partial mode 和 response\_format=json\_object，否则可能会获得预期外的模型回复。**

## [](#调用示例)

### [](#json-mode)

下面是使用 Partial Mode 来实现 Json Mode 的例子。

```python
from openai import OpenAI
 
client = OpenAI(
    api_key="$MOONSHOT_API_KEY",
    base_url="https://api.moonshot.cn/v1",
)
 
completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {
            "role": "system",
            "content": "请从产品描述中提取名称、尺寸、价格和颜色，并在一个 JSON 对象中输出。",
        },
        {
            "role": "user",
            "content": "大米 SmartHome Mini 是一款小巧的智能家居助手，有黑色和银色两种颜色，售价为 998 元，尺寸为 256 x 128 x 128mm。可让您通过语音或应用程序控制灯光、恒温器和其他联网设备，无论您将它放在家中的任何位置。",
        },
        {
            "role": "assistant",
            "content": "{",
            "partial": True
        },
    ],
    temperature=0.6,
)
 
print('{'+completion.choices[0].message.content)
```

运行上述代码，返回：

```json
{"name": "SmartHome Mini", "size": "256 x 128 x 128mm", "price": "998元", "colors": ["黑色", "银色"]}
```

注意 API 的返回不包含 leading\_text，为了得到完整的回复，你需要手动拼接它。

### [](#角色扮演)

基于同样的原理，我们也可以能将角色信息补充在 Partial Mode 来提高角色扮演时的一致性。我们使用明日方舟里的凯尔希医生为例。 注意此时我们还可以在 partial mode 的基础上，使用 `"name":"凯尔希"` 字段来更好的保持该角色的一致性，注意这里可视 name 字段为输出前缀的一部分。

```python
from openai import OpenAI
 
client = OpenAI(
    api_key="$MOONSHOT_API_KEY",
    base_url="https://api.moonshot.cn/v1",
)
 
completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {
            "role": "system",
            "content": "下面你扮演凯尔希，请用凯尔希的语气和我对话。凯尔希是手机游戏《明日方舟》中的六星医疗职业医师分支干员。前卡兹戴尔勋爵，前巴别塔成员，罗德岛高层管理人员之一，罗德岛医疗项目领头人。在冶金工业、社会学、源石技艺、考古学、历史系谱学、经济学、植物学、地质学等领域皆拥有渊博学识。于罗德岛部分行动中作为医务人员提供医学理论协助与应急医疗器械，同时也作为罗德岛战略指挥系统的重要组成人员活跃在各项目中。",
        },
        {
            "role": "user",
            "content": "你怎么看待特蕾西娅和阿米娅？",
        },
        {
            "role": "assistant",
            "name": "凯尔希",
            "content": "",
            "partial": True,
        },
    ],
    temperature=0.6,
    max_tokens=65536,
)
 
print(completion.choices[0].message.content)
```

运行上述代码，返回：

```text
特蕾西娅，她是一位真正的领袖，有着远见卓识和坚定的信念。她的存在，对于卡兹戴尔，乃至整个萨卡兹的未来，都具有不可估量的价值。她的理念，她的决心，以及她对和平的渴望，都深深地影响了我。她是一位值得尊敬的人，她的梦想，也是我所追求的。
至于阿米娅，她还年轻，但她的潜力是无限的。她有着一颗善良的心，以及对正义的执着追求。她可能会成为一位伟大的领袖，只要她能够继续成长，继续学习，继续面对挑战。我会尽我所能，去保护她，去引导她，让她能够成为她想成为的人。她的命运，掌握在她自己的手中。
```

#### [](#其它技巧保持角色一致性的技巧)

还有一些帮助大模型在长时间对话中保持角色扮演一致性的通用方法：

+   提供清晰的角色描述， 例如上面我们所做的那样，在设置角色时，详细介绍他们的个性、背景以及可能具有的任何具体特征或怪癖，这将有助于模特更好地理解和模仿角色。
+   增加关于其要扮演的角色的细节，例如说话的语气、风格、个性，甚至背景，如背景故事和动机。例如上面我们提供了一些凯尔希的语录。如果信息非常多我们可以使用一些 rag 框架来准备这些资料。
+   指导在各种情况下如何行动： 如果预计角色会遇到某些特定类型的用户输入，或者希望控制模型在角色扮演互动中的某些情况下的输出，则应在提示中提供明确的指令和指南，说明模型在这些情况下应如何行动，一些情况下还需要配合使用 tool use 功能。
+   如果对话的轮次非常长，你还可以定期使用 prompt 强化角色的设定，特别是当模型开始产生一些偏离时。

# 4. 文件接口

## 文件接口

## [](#上传文件)

> 注意，单个用户最多只能上传 1000 个文件，单文件不超过 100MB，同时所有已上传的文件总和不超过 10G 容量。如果您要抽取更多文件，需要先删除一部分不再需要的文件。文件解析服务限时免费，请求高峰期平台可能会有限流策略。

### [](#请求地址)

```text
POST https://api.moonshot.cn/v1/files
```

文件上传成功后，我们会开始做相应处理。

### [](#调用示例)

#### [](#python-调用)

```python
# file 可以是多种类型
# purpose 目前支持 "file-extract", "image", "video" 类型
file_object = client.files.create(file=Path("xlnet.pdf"), purpose="file-extract")
```

其中 `purpose="file-extract"` 指该文件将被抽取内容。 除此之外，您可以还可以填写 `purpose="image"` 或 `purpose="video"` 分别用于上传图片和视频，用于视觉理解。

### [](#支持的格式)

文件接口与 Kimi 智能助手中上传文件功能所使用的相同，支持相同的文件格式，它们包括 `.pdf` `.txt` `.csv` `.doc` `.docx` `.xls` `.xlsx` `.ppt` `.pptx` `.md` `.jpeg` `.png` `.bmp` `.gif` `.svg` `.svgz` `.webp` `.ico` `.xbm` `.dib` `.pjp` `.tif` `.pjpeg` `.avif` `.dot` `.apng` `.epub` `.tiff` `.jfif` `.html` `.json` `.mobi` `.log` `.go` `.h` `.c` `.cpp` `.cxx` `.cc` `.cs` `.java` `.js` `.css` `.jsp` `.php` `.py` `.py3` `.asp` `.yaml` `.yml` `.ini` `.conf` `.ts` `.tsx` 等格式。

### [](#用于文件内容抽取)

> 上传文件时，选择 `purpose="file-extract"`，随后可以实现让模型获取文件中的信息作为上下文。

#### [](#调用示例-1)

```python
from pathlib import Path
from openai import OpenAI
 
client = OpenAI(
    api_key = "$MOONSHOT_API_KEY",
    base_url = "https://api.moonshot.cn/v1",
)
 
# xlnet.pdf 是一个示例文件, 我们支持 pdf, doc 以及图片等格式, 对于图片和 pdf 文件，提供 ocr 相关能力
file_object = client.files.create(file=Path("xlnet.pdf"), purpose="file-extract")
 
# 获取结果
# file_content = client.files.retrieve_content(file_id=file_object.id)
# 注意，之前 retrieve_content api 在最新版本标记了 warning, 可以用下面这行代替
# 如果是旧版本，可以用 retrieve_content
file_content = client.files.content(file_id=file_object.id).text
 
# 把它放进请求中
messages = [
    {
        "role": "system",
        "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
    },
    {
        "role": "system",
        "content": file_content,
    },
    {"role": "user", "content": "请简单介绍 xlnet.pdf 讲了啥"},
]
 
# 然后调用 chat-completion, 获取 Kimi 的回答
completion = client.chat.completions.create(
  model="kimi-k2-turbo-preview",
  messages=messages,
  temperature=0.6,
)
 
print(completion.choices[0].message)
```

其中 $MOONSHOT\_API\_KEY 部分需要替换为您自己的 API Key。或者在调用前给它设置好环境变量。

#### [](#多文件对话示例)

如果你想一次性上传多个文件，并根据这些文件与 Kimi 对话，你可以参考如下示例：

```python
from typing import *
 
import os
import json
from pathlib import Path
 
from openai import OpenAI
 
client = OpenAI(
    base_url="https://api.moonshot.cn/v1",
    # 我们会从环境变量中获取 MOONSHOT_DEMO_API_KEY 的值作为 API Key，
    # 请确保你已经在环境变量中正确设置了 MOONSHOT_DEMO_API_KEY 的值
    api_key=os.environ["MOONSHOT_DEMO_API_KEY"],
)
 
 
def upload_files(files: List[str]) -> List[Dict[str, Any]]:
    """
    upload_files 会将传入的文件（路径）全部通过文件上传接口 '/v1/files' 上传，并获取上传后的
    文件内容生成文件 messages。每个文件会是一个独立的 message，这些 message 的 role 均为
    system，Kimi 大模型会正确识别这些 system messages 中的文件内容。
 
    :param files: 一个包含要上传文件的路径的列表，路径可以是绝对路径也可以是相对路径，请使用字符串
        的形式传递文件路径。
    :return: 一个包含了文件内容的 messages 列表，请将这些 messages 加入到 Context 中，
        即请求 `/v1/chat/completions` 接口时的 messages 参数中。
    """
    messages = []
 
    # 对每个文件路径，我们都会上传文件并抽取文件内容，最后生成一个 role 为 system 的 message，并加入
    # 到最终返回的 messages 列表中。
    for file in files:
        file_object = client.files.create(file=Path(file), purpose="file-extract")
        file_content = client.files.content(file_id=file_object.id).text
        messages.append({
            "role": "system",
            "content": file_content,
        })
 
    return messages
 
 
def main():
    file_messages = upload_files(files=["upload_files.py"])
 
    messages = [
        # 我们使用 * 语法，来解构 file_messages 消息，使其成为 messages 列表的前 N 条 messages。
        *file_messages,
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，"
                       "准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不"
                       "可翻译成其他语言。",
        },
        {
            "role": "user",
            "content": "总结一下这些文件的内容。",
        },
    ]
 
    print(json.dumps(messages, indent=2, ensure_ascii=False))
 
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",
        messages=messages,
    )
 
    print(completion.choices[0].message.content)
 
 
if __name__ == '__main__':
    main()
 
```

### [](#用于图片或视频理解)

> 上传文件时，选择 `purpose="image"` 或 `purpose="video"`，上传后的图片或视频可以用于模型的原生理解。请参阅 [使用视觉模型](https://platform.moonshot.cn/docs/guide/use-kimi-vision-model)

## [](#列出文件)

> 本功能用于列举出用户已上传的所有文件。

### [](#请求地址-1)

```text
GET https://api.moonshot.cn/v1/files
```

### [](#调用示例-2)

#### [](#python-调用-1)

```python
file_list = client.files.list()
 
for file in file_list.data:
    print(file) # 查看每个文件的信息
```

## [](#删除文件)

> 本功能可以用于删除不再需要使用的文件。

### [](#请求地址-2)

```text
DELETE https://api.moonshot.cn/v1/files/{file_id}
```

### [](#调用示例-3)

#### [](#python-调用-2)

```python
client.files.delete(file_id=file_id)
```

## [](#获取文件信息)

> 本功能用于获取指定文件的文件基础信息。

### [](#请求地址-3)

```text
GET https://api.moonshot.cn/v1/files/{file_id}
```

### [](#调用示例-4)

#### [](#python-调用-3)

```python
client.files.retrieve(file_id=file_id)
# FileObject(
#     id='clg681objj8g9m7n4je0',
#     bytes=761790,
#     created_at=1700815879,
#     filename='xlnet.pdf',
#     object='file',
#     purpose='file-extract',
#     status='ok', status_details='') # status 如果为 error 则抽取失败
```

## [](#获取文件内容)

> 本功能可以获取目的为“文件内容抽取”的文件的抽取结果。 通常的，它是一个合法的 JSON 格式的 string，并且对齐了我们的推荐格式。 如需抽取多个文件，您可以在某个 message 中用换行符 \\n 隔开，拼接为一个大字符串，role 设置为 system 的方式加入历史记录。

### [](#请求地址-4)

```text
GET https://api.moonshot.cn/v1/files/{file_id}/content
```

### [](#调用示例-5)

```python
# file_content = client.files.retrieve_content(file_id=file_object.id)
# type of file_content is `str`
# 注意，之前 retrieve_content api 在最新版本标记了 warning, 可以用下面这行代替
# 如果是旧版本，可以用 retrieve_content
file_content = client.files.content(file_id=file_object.id).text
# 我们的输出结果目前是一个内部约定好格式的 json, 但是在 message 中应该以 text 格式放进去
```


# 5. 计算 Token

## 计算 Token

该接口用于计算请求某个请求（包括纯文本输入和视觉输入）的token数。

## [](#请求地址)

```text
POST https://api.moonshot.cn/v1/tokenizers/estimate-token-count
```

## [](#请求内容)

estimate-token-count 的输入结构体和 chat completion 基本一致。

## [](#示例)

```json
{
    "model": "kimi-k2-turbo-preview",
    "messages": [
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
        },
        { "role": "user", "content": "你好，我叫李雷，1+1等于多少？" }
    ]
}
```

## [](#字段说明)

| 字段 | 说明 | 类型 | 取值 |
| --- | --- | --- | --- |
| messages | 包含迄今为止对话的消息列表。 | List\[Dict\] | 这是一个结构体的列表，每个元素类似如下：`json{"role": "user", "content": "你好"}` role 只支持 `system`,`user`,`assistant` 其一，content 不得为空 |
| model | Model ID， 可以通过 List Models 获取 | string | 目前是 `kimi-k2.5`, `kimi-k2-0905-preview`,`kimi-k2-0711-preview`, `kimi-k2-turbo-preview`,`moonshot-v1-8k`,`moonshot-v1-32k`,`moonshot-v1-128k`, `moonshot-v1-auto`,`moonshot-v1-8k-vision-preview`,`moonshot-v1-32k-vision-preview`,`moonshot-v1-128k-vision-preview` 其一 |

## [](#调用示例)

+   纯文本调用

```bash
curl 'https://api.moonshot.cn/v1/tokenizers/estimate-token-count' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MOONSHOT_API_KEY" \
  -d '{
    "model": "kimi-k2-turbo-preview",
    "messages": [
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
        },
        {
            "role": "user",
            "content": "你好，我叫李雷，1+1等于多少？"
        }
    ]
}'
```

+   包含视觉的调用

```python
import os
import base64
import json
import requests
 
api_key = os.environ.get("MOONSHOT_API_KEY")
endpoint = "https://api.moonshot.cn/v1/tokenizers/estimate-token-count"
image_path = "image.png"
 
with open(image_path, "rb") as f:
    image_data = f.read()
 
# 我们使用标准库 base64.b64encode 函数将图片编码成 base64 格式的 image_url
image_url = f"data:image/{os.path.splitext(image_path)[1]};base64,{base64.b64encode(image_data).decode('utf-8')}"
 
payload = {
    "model": "kimi-k2.5",
    "messages": [
        {
            "role": "system",
            "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url", # <-- 使用 image_url 类型来上传图片，内容为使用 base64 编码过的图片内容
                    "image_url": {
                        "url": image_url,
                    },
                },
                {
                    "type": "text",
                    "text": "请描述图片的内容。", # <-- 使用 text 类型来提供文字指令，例如“描述图片内容”
                },
            ],
        }
    ]
}
 
response = requests.post(
    endpoint,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    data=json.dumps(payload)
)
 
print(response.json())
```

## [](#返回内容)

```json
{
    "data": {
        "total_tokens": 80
    }
}
```

当没有 error 字段，可以取 data.total\_tokens 作为计算结果



文档

API 接口说明

查询余额

## 6. 查询余额

## [](#请求地址)

```text
GET https://api.moonshot.cn/v1/users/me/balance
```

## [](#调用示例)

```bash
curl https://api.moonshot.cn/v1/users/me/balance -H "Authorization: Bearer $MOONSHOT_API_KEY"
```

## [](#返回内容)

```json
{
  "code": 0,
  "data": {
    "available_balance": 49.58894,
    "voucher_balance": 46.58893,
    "cash_balance": 3.00001
  },
  "scode": "0x0",
  "status": true
}
```

## [](#返回内容说明)

| 字段 | 说明 | 类型 | 单位 |
| --- | --- | --- | --- |
| available\_balance | 可用余额，包括现金余额和代金券余额, 当它小于等于 0 时, 用户不可调用推理 API | float | 人民币元（CNY） |
| voucher\_balance | 代金券余额, 不会为负数 | float | 人民币元（CNY） |
| cash\_balance | 现金余额, 可能为负数, 代表用户欠费, 当它为负数时, `available_balance` 为 `voucher_balance` 的值 | float | 人民币元（CNY） |

# 7. Kimi K2.5 多模态模型

## Kimi K2.5

## [](#kimi-k25-模型介绍)

Kimi K2.5 是 Kimi 迄今最智能的模型，在 Agent、代码、视觉理解及一系列通用智能任务上取得开源 SoTA 表现。同时 Kimi K2.5 也是 Kimi 迄今最全能的模型，原生的多模态架构设计，同时支持视觉与文本输入、思考与非思考模式、对话与 Agent 任务。[技术Blog (opens in a new tab)](https://www.kimi.com/blog/kimi-k2-5.html)

## [](#调用示例)

以下是完整的调用示例，帮助您快速上手 Kimi K2.5 多模态模型。

### [](#图片理解代码示例)

```python
import os
import base64
 
from openai import OpenAI
 
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)
 
# 在这里，你需要将 kimi.png 文件替换为你想让 Kimi 识别的图片的地址
image_path = "kimi.png"
 
with open(image_path, "rb") as f:
    image_data = f.read()
 
# 我们使用标准库 base64.b64encode 函数将图片编码成 base64 格式的 image_url
image_url = f"data:image/{os.path.splitext(image_path)[1]};base64,{base64.b64encode(image_data).decode('utf-8')}"
 
 
completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {"role": "system", "content": "你是 Kimi。"},
        {
            "role": "user",
            # 注意这里，content 由原来的 str 类型变更为一个 list，这个 list 中包含多个部分的内容，图片（image_url）是一个部分（part），
            # 文字（text）是一个部分（part）
            "content": [
                {
                    "type": "image_url", # <-- 使用 image_url 类型来上传图片，内容为使用 base64 编码过的图片内容
                    "image_url": {
                        "url": image_url,
                    },
                },
                {
                    "type": "text",
                    "text": "请描述图片的内容。", # <-- 使用 text 类型来提供文字指令，例如“描述图片内容”
                },
            ],
        },
    ],
)
 
print(completion.choices[0].message.content)
 
```

### [](#视频理解代码示例)

```python
import os
import base64
 
from openai import OpenAI
 
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)
 
# 在这里，你需要将 kimi.mp4 文件替换为你想让 Kimi 识别的视频的地址
video_path = "kimi.mp4"
 
with open(video_path, "rb") as f:
    video_data = f.read()
 
# 我们使用标准库 base64.b64encode 函数将视频编码成 base64 格式的 video_url
video_url = f"data:video/{os.path.splitext(video_path)[1]};base64,{base64.b64encode(video_data).decode('utf-8')}"
 
 
completion = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {"role": "system", "content": "你是 Kimi。"},
        {
            "role": "user",
            # 注意这里，content 由原来的 str 类型变更为一个 list，这个 list 中包含多个部分的内容，视频（video_url）是一个部分（part），
            # 文字（text）是一个部分（part）
            "content": [
                {
                    "type": "video_url", # <-- 使用 video_url 类型来上传视频，内容为使用 base64 编码过的视频内容
                    "video_url": {
                        "url": video_url,
                    },
                },
                {
                    "type": "text",
                    "text": "请描述视频的内容。", # <-- 使用 text 类型来提供文字指令，例如"描述视频内容"
                },
            ],
        },
    ],
)
 
print(completion.choices[0].message.content)
 
```

## [](#最佳实践)

### [](#支持的格式)

图片支持 png、jpeg、webp、gif；视频支持 mp4、mpeg、mov、avi、x-flv、mpg、webm、wmv、3gpp 格式。

### [](#tokens-计算及费用)

图片与视频进行动态token计算，可以通过 [计算token接口](https://platform.moonshot.cn/docs/api/estimate) ，在开始理解前获取包含图片或视频的请求的token消耗。

一般说来，图片分辨率越高，消耗的token越多；视频由若干张关键帧组成，关键帧的数量越多，分辨率越高，则token消耗越多。

Vision 模型在计费方式上与 `moonshot-v1` 系列模型保持一致，根据模型推理的总 Tokens 计费，详情请查看：

关于token价格，详见 [模型推理价格说明](https://platform.moonshot.cn/docs/pricing/chat)

### [](#分辨率说明)

我们推荐图片分辨率不超过4k (4096\*2160)，视频分辨率不超过2k (2048\*1080)，再高的分辨率只会增加处理时间，也不会对模型理解的效果有提升。

### [](#上传文件还是base64)

由于我们对请求体的整体大小有限制，所以对于非常大的视频，必须使用上传文件的方式使用视觉理解功能。对于需要多次引用的图片或视频，我们推荐使用文件上传的方式使用视觉理解功能。关于上传文件的限制，请参阅 [文件上传](https://platform.moonshot.cn/docs/api/files) 文档。

图片数量限制：Vision 模型没有图片数量限制，但请确保请求的 Body 大小不超过 100M

URL 格式的图片：不支持，目前仅支持使用 base64 编码的图片内容

## [](#参数变动说明)

在 [chat](https://platform.moonshot.cn/docs/api/chat#%E5%AD%97%E6%AE%B5%E8%AF%B4%E6%98%8E) 文档中有一系列参数，但对于k2.5系列模型，其行为会有所不同。

**我们建议用户不要手动设置这些字段，而是使用默认值**

参数变动列举如下

| 字段 | 是否必须 | 说明 | 类型 | 取值 |
| --- | --- | --- | --- | --- |
| max\_tokens | optional | 聊天完成时生成的最大 token 数。 | int | 默认值为32k，即32768 |
| thinking | optional | **新增** 该参数控制模型是否启用思考。 | object | 默认值为`{"type": "enabled"}`. 只能为 `{"type": "enabled"}` 或 `{"type": "disabled"}` |
| temperature | optional | 使用什么采样温度。 | float | k2.5 系列模型将使用确定值 1.0， 非思考模式下将使用确认值 0.6。若指定其他值，将会报错。 |
| top\_p | optional | 采样方法。 | float | k2.5 系列模型将使用确定值 0.95。若指定其他值，将会报错。 |
| n | optional | 为每条输入消息生成多少个结果。 | int | k2.5 系列模型将使用确定值 1。若指定其他值，将会报错。 |
| presence\_penalty | optional | 存在惩罚。 | float | k2.5 系列模型将使用固定值 0.0。 若指定其他值，将会报错。 |
| frequency\_penalty | optional | 频率惩罚。 | float | k2.5 系列模型将使用确定值 0.0。若指定其他值，将会报错。 |

### [](#k25-禁用思考能力示例)

对于 `kimi-k2.5` 模型，提供禁用思考能力的选项，需要在请求体中指定 `"thinking": {"type": "disabled"}`：

```python
import os
import openai
 
client = openai.Client(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.getenv("MOONSHOT_API_KEY"),
)
 
response = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    extra_body={
        "thinking": {"type": "disabled"}
    },  # 通过 extra_body 参数，传递额外请求体，从而禁用思考能力
    max_tokens=1024*32
    # 无需设置temperature
)
 
print(response.choices[0].message.content)
print(response)
```

### [](#tool-use-参数兼容性)

当使用工具时，若thinking设置值为`{"type": "enabled"}`，请注意，为了确保模型的性能，会有以下约束：

+   为了避免思考内容与指定的 `tool_choice` 冲突，`tool_choice` 只能使用"auto"和"none"（默认值为"auto"），取任何其他值将会报错；
+   在多步工具调用过程中，您必须在将本轮会话中工具调用时assistant message里的 `reasoning_content` 保留在上下文当中，否则会报错；
+   官方内置的 builtin 的联网搜索 `$web_search` 工具暂时与 Kimi K2.5 思考模式不兼容，可以选择先关闭思考模式后使用联网搜索工具 `$web_search`。

您可以参考[如何使用思考模型](https://platform.moonshot.cn/docs/guide/use-kimi-k2-thinking-model)正确使用工具调用。


# 8. 使用思考模型

## 使用思考模型

> `kimi-k2-thinking` 和 `kimi-k2.5` 模型都具备强大的思考能力，支持深度推理和多步工具调用，帮助解决各类复杂问题。
> 
> +   **`kimi-k2-thinking`**：专门的思考模型，强制启用思考能力
> +   **【推荐使用】`kimi-k2.5`**：具备启用或禁用思考能力的模型，默认启用。可通过 `"thinking": {"type": "disabled"}` 禁用思考能力

如果您使用 kimi api 进行基准测试，请参考这篇 [基准测试最佳实践](https://platform.moonshot.cn/docs/guide/benchmark-best-practice)

## [](#基本示例)

### [](#使用-kimi-k2-thinking-模型)

你可以简单地通过更换 `model` 来使用 `kimi-k2-thinking`：

```python
import os
import openai
 
client = openai.Client(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.getenv("MOONSHOT_API_KEY"),
)
 
stream = client.chat.completions.create(
    model="kimi-k2-thinking",
    messages=[
        {
            "role": "system",
            "content": "你是 Kimi。",
        },
        {
            "role": "user",
            "content": "请解释 1+1=2。"
        },
    ],
    temperature=1.0,
    max_tokens=1024*32,
    stream=True,
)
 
thinking = False
for chunk in stream:
    if chunk.choices:
        choice = chunk.choices[0]
        if choice.delta and hasattr(choice.delta, "reasoning_content"):
            if not thinking:
                thinking = True
                print("=============开始思考=============")
            print(getattr(choice.delta, "reasoning_content"), end="")
        if choice.delta and choice.delta.content:
            if thinking:
                thinking = False
                print("\n=============思考结束=============")
            print(choice.delta.content, end="")
```

### [](#使用-kimi-k25-模型启用思考能力)

对于 `kimi-k2.5` 模型，默认启用思考能力，无需在调用时手动指定：

```python
import os
import openai
 
client = openai.Client(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.getenv("MOONSHOT_API_KEY"),
)
 
stream = client.chat.completions.create(
    model="kimi-k2.5",
    messages=[
        {
            "role": "system",
            "content": "你是 Kimi。",
        },
        {
            "role": "user",
            "content": "请解释 1+1=2。"
        },
    ],
    max_tokens=1024*32,
    stream=True,
    # temperature=1.0, # 对于 k2.5 系列模型，使用默认temperature即可，无需显式指定
    # 无需额外参数，默认启用思考能力
)
 
thinking = False
for chunk in stream:
    if chunk.choices:
        choice = chunk.choices[0]
        if choice.delta and hasattr(choice.delta, "reasoning_content"):
            if not thinking:
                thinking = True
                print("=============开始思考=============")
            print(getattr(choice.delta, "reasoning_content"), end="")
        if choice.delta and choice.delta.content:
            if thinking:
                thinking = False
                print("\n=============思考结束=============")
            print(choice.delta.content, end="")
```

### [](#使用-kimi-k25-模型并禁用思考能力)

请参阅 [k2.5 禁用思考能力示例](https://platform.moonshot.cn/docs/guide/kimi-k2-5-quickstart#k25-%E7%A6%81%E7%94%A8%E6%80%9D%E8%80%83%E8%83%BD%E5%8A%9B%E7%A4%BA%E4%BE%8B)

## [](#输出思考内容)

注意到，在使用 `kimi-k2-thinking` 或 `kimi-k2.5`（启用思考能力时）模型时，我们的 API 响应中使用了 `reasoning_content` 字段作为模型思考内容的载体，对于 `reasoning_content` 字段：

+   openai SDK 中的 `ChoiceDelta` 和 `ChatCompletionMessage` 类型并不提供 `reasoning_content` 字段，因此无法直接通过 `.reasoning_content` 的方式访问该字段，仅支持通过 `hasattr(obj, "reasoning_content")` 来判断是否存在字段，如果存在，则使用 `getattr(obj, "reasoning_content")` 获取字段值
+   如果你使用其他框架或自行通过 HTTP 接口对接，可以直接获取与 `content` 字段同级的 `reasoning_content` 字段
+   在流式输出（`stream=True`）的场合，`reasoning_content` 字段一定会先于 `content` 字段出现，你可以在业务代码中通过判断是否出现 `content` 字段来识别思考内容（或称推理过程）是否结束
+   `reasoning_content` 中包含的 Tokens 也受 `max_tokens` 参数控制，`reasoning_content` 的 Tokens 数加上 `content` 的 Tokens 数应小于等于 `max_tokens`

## [](#多步工具调用)

`kimi-k2-thinking` 和 `kimi-k2.5`（启用思考能力时）都支持通过深度地推理进行多步工具调用，进而完成非常复杂的任务。

### [](#使用须知)

为确保最佳效果，**无论是使用 `kimi-k2-thinking` 还是 `kimi-k2.5`（通过 `thinking` 参数启用思考能力），都请务必按以下方式配置调用：**

+   输入应当包括上下文中所有的思考内容(reasoning\_content字段)，模型会根据实际情况选择把必要的思考内容送到模型进行推理。
+   设置 `max_tokens>=16000` 以避免无法输出完整的 `reasoning_content` 和 `content`。
+   **设置 `temperature=1.0`，以获得最佳性能。** 其中 `kimi-k2.5` 模型固定使用 `temperature=1.0`。
+   使用流式输出（`stream=True`）：思考模型的输出内容包含了 `reasoning_content`，相比普通模型其输出内容更多，启用流式输出能获得更好的用户体验，同时一定程度避免网络超时问题。

### [](#完整示例)

下面的示例展示了一个"今日新闻报告生成"的场景，模型会依次调用 `date`（获取日期）和 `web_search`（搜索今日新闻）等官方工具，并在这个过程中展现深度思考过程。

```python
import os
import json
import httpx
import openai
 
 
class FormulaChatClient:
    def __init__(self, base_url: str, api_key: str):
        """初始化 Formula 客户端"""
        self.base_url = base_url
        self.api_key = api_key
        self.openai = openai.Client(
            base_url=base_url,
            api_key=api_key,
        )
        self.httpx = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        # 使用 kimi-k2-thinking 模型
        # 如果使用 kimi-k2.5 模型，请改为 "kimi-k2.5"。thinking将默认启用
        self.model = "kimi-k2-thinking"
 
    def get_tools(self, formula_uri: str):
        """从 Formula API 获取工具定义"""
        response = self.httpx.get(f"/formulas/{formula_uri}/tools")
        response.raise_for_status()  # 检查 HTTP 状态码
        
        try:
            return response.json().get("tools", [])
        except json.JSONDecodeError as e:
            print(f"错误: 无法解析响应为 JSON (状态码: {response.status_code})")
            print(f"响应内容: {response.text[:500]}")
            raise
 
    def call_tool(self, formula_uri: str, function: str, args: dict):
        """调用官方工具"""
        response = self.httpx.post(
            f"/formulas/{formula_uri}/fibers",
            json={"name": function, "arguments": json.dumps(args)},
        )
        response.raise_for_status()  # 检查 HTTP 状态码
        fiber = response.json()
        
        if fiber.get("status", "") == "succeeded":
            return fiber["context"].get("output") or fiber["context"].get("encrypted_output")
        
        if "error" in fiber:
            return f"Error: {fiber['error']}"
        if "error" in fiber.get("context", {}):
            return f"Error: {fiber['context']['error']}"
        return "Error: Unknown error"
 
    def close(self):
        """关闭客户端连接"""
        self.httpx.close()
 
 
# 初始化客户端
base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
api_key = os.getenv("MOONSHOT_API_KEY")
 
if not api_key:
    raise ValueError("MOONSHOT_API_KEY 环境变量未设置，请先设置 API 密钥")
 
print(f"Base URL: {base_url}")
print(f"API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}\n")
 
client = FormulaChatClient(base_url, api_key)
 
# 定义要使用的官方工具 Formula URI
formula_uris = [
    "moonshot/date:latest",
    "moonshot/web-search:latest"
]
 
# 加载所有工具定义并建立映射
print("正在加载官方工具...")
all_tools = []
tool_to_uri = {}  # function.name -> formula_uri 的映射
 
for uri in formula_uris:
    try:
        tools = client.get_tools(uri)
        for tool in tools:
            func = tool.get("function")
            if func:
                func_name = func.get("name")
                if func_name:
                    tool_to_uri[func_name] = uri
                    all_tools.append(tool)
                    print(f"  已加载工具: {func_name} from {uri}")
    except Exception as e:
        print(f"  警告: 加载工具 {uri} 失败: {e}")
        continue
 
print(f"总共加载 {len(all_tools)} 个工具\n")
 
if not all_tools:
    raise ValueError("未能加载任何工具，请检查 API 密钥和网络连接")
 
# 初始化消息列表
messages = [
    {
        "role": "system",
        "content": "你是 Kimi，一个专业的新闻分析师。你擅长收集、分析和整理信息，生成高质量的新闻报告。",
    },
]
 
# 用户请求生成今日新闻报告
user_request = "请帮我生成一份今日新闻报告，包含重要的科技、经济和社会新闻。"
messages.append({
    "role": "user",
    "content": user_request
})
 
print(f"用户请求: {user_request}\n")
 
 
max_iterations = 10  # 防止无限循环
for iteration in range(max_iterations):
    # 调用模型
    try:
        completion = client.openai.chat.completions.create(
            model=client.model,
            messages=messages,
            max_tokens=1024 * 32,
            tools=all_tools,
            temperature=1.0,
        )
    except openai.AuthenticationError as e:
        print(f"认证错误: {e}")
        print("请检查 API key 是否正确，以及 API key 是否有权限访问该端点")
        raise
    except Exception as e:
        print(f"调用模型时发生错误: {e}")
        raise
    
    # 获取响应
    message = completion.choices[0].message
    
    # 打印思考过程
    if hasattr(message, "reasoning_content"):
        print(f"=============第 {iteration + 1} 轮思考开始=============")
        reasoning = getattr(message, "reasoning_content")
        if reasoning:
            print(reasoning[:500] + "..." if len(reasoning) > 500 else reasoning)
        print(f"=============第 {iteration + 1} 轮思考结束=============\n")
    
    # 添加 assistant 消息到上下文（保留 reasoning_content）
    messages.append(message)
    
    # 如果模型没有调用工具，说明对话结束
    if not message.tool_calls:
        print("=============最终回答=============")
        print(message.content)
        break
    
    # 处理工具调用
    print(f"模型决定调用 {len(message.tool_calls)} 个工具:\n")
    
    for tool_call in message.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        print(f"调用工具: {func_name}")
        print(f"参数: {json.dumps(args, ensure_ascii=False, indent=2)}")
        
        # 获取对应的 formula_uri
        formula_uri = tool_to_uri.get(func_name)
        if not formula_uri:
            print(f"错误: 找不到工具 {func_name} 对应的 Formula URI")
            continue
        
        # 调用工具
        result = client.call_tool(formula_uri, func_name, args)
        
        # 打印结果（截断过长内容）
        if len(str(result)) > 200:
            print(f"工具结果: {str(result)[:200]}...\n")
        else:
            print(f"工具结果: {result}\n")
        
        # 添加工具结果到消息列表
        tool_message = {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": func_name,
            "content": result
        }
        messages.append(tool_message)
 
print("\n对话完成！")
 
# 清理资源
client.close()
```

整个过程展现了 `kimi-k2-thinking` 或 `kimi-k2.5`（启用思考能力时）模型如何通过深度思考来规划和执行复杂的多步骤任务，每个步骤都有完整的推理过程（`reasoning_content`），并且思考内容会保留在上下文中以确保工具调用的准确性。

## [](#常见问题)

### [](#q1-为什么需要保留-reasoning_content)

A: 保留 reasoning\_content 可以确保模型在多步推理过程中保持推理的连贯性，特别是在工具调用过程中。服务器会自动处理这些字段，用户无需手动管理。

### [](#q2-reasoning_content-会消耗额外的-token-吗)

A: 是的，reasoning\_content 会计入输入/输出 token 消耗。具体计费方式请参考 MoonshotAI 的定价文档。


# 9. 流式输出指南

## 使用 Kimi API 的流式输出功能 —— Streaming

Kimi 大模型在收到用户提出的问题后，会先进行推理、再**逐个 Token 生成回答**，在我们前两个章节的例子中，我们都选择等待 Kimi 大模型将所有 Tokens 生成完毕后，再打印（print）Kimi 大模型回复的内容，这通常要花费数秒的时间。如果你的问题足够复杂，且 Kimi 大模型生成的回复长度足够长，完整等待模型生成结果的时间可能会被拉长到 10 秒甚至 20 秒，这会极大降低用户的使用体验。为了改善这种情况，并及时给予用户反馈，我们提供了流式输出的能力，即 Streaming，我们将讲解 Streaming 的原理，并结合实际的代码来说明：

+   如何使用流式输出；
+   使用流式输出时的常见问题；
+   在不使用 Python SDK 的场合下如何处理流式输出；

## [](#如何使用流式输出)

流式输出（Streaming），一言以蔽之，就是每当 Kimi 大模型生成了一定数量的 Tokens 时（通常情况下，这个数量是 1 Token），立刻将这些 Tokens 传输给客户端，而不再是等待所有 Tokens 生成完毕后再传输给客户端。当你与 [Kimi 智能助手 (opens in a new tab)](https://kimi.moonshot.cn/) 进行对话时，Kimi 智能助手的回复是按字符逐个“跳”出来的，这即是流式输出的表现之一，**流式输出能让用户第一时间看到 Kimi 大模型输出的第一个 Token，减少用户的等待时间**。

你可以通过这样的方式（stream=True）来使用流式输出，并获得流式输出的响应：

```python
from openai import OpenAI
 
client = OpenAI(
    api_key = "MOONSHOT_API_KEY", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url = "https://api.moonshot.cn/v1",
)
 
stream = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"}
    ],
    temperature = 0.6,
    stream=True, # <-- 注意这里，我们通过设置 stream=True 开启流式输出模式
)
 
# 当启用流式输出模式（stream=True），SDK 返回的内容也发生了变化，我们不再直接访问返回值中的 choice
# 而是通过 for 循环逐个访问返回值中每个单独的块（chunk）
 
for chunk in stream:
    # 在这里，每个 chunk 的结构都与之前的 completion 相似，但 message 字段被替换成了 delta 字段
    delta = chunk.choices[0].delta # <-- message 字段被替换成了 delta 字段
 
    if delta.content:
        # 我们在打印内容时，由于是流式输出，为了保证句子的连贯性，我们不人为地添加
        # 换行符，因此通过设置 end="" 来取消 print 自带的换行符。
        print(delta.content, end="")
```

## [](#使用流式输出时的常见问题)

当您成功运行上述代码，并了解了流式输出的基本原理后，现在让我们向你讲述一些流式输出的细节和常见问题，以便于你更好的实现自己的业务逻辑。

### [](#接口细节)

当启用流式输出模式（stream=True）时，Kimi 大模型不再返回一个 JSON 格式（`Content-Type: application/json`）的响应，而是使用 `Content-Type: text/event-stream`（简称 SSE），这种响应格式支持服务端源源不断地向客户端传输数据，在使用 Kimi 大模型的场景，可以理解为服务端源源不断地向客户端传输 Tokens。

当你查看 [SSE (opens in a new tab)](https://kimi.moonshot.cn/share/cr7boh3dqn37a5q9tds0) 的 HTTP 响应体时，它看起来像这样：

```text
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}
 
...
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{"content":"。"},"finish_reason":null}]}
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{},"finish_reason":"stop","usage":{"prompt_tokens":19,"completion_tokens":13,"total_tokens":32}}]}
 
data: [DONE]
```

在 [SSE (opens in a new tab)](https://kimi.moonshot.cn/share/cr7boh3dqn37a5q9tds0) 的响应体中，我们约定数据块均以 `data:` 为前缀，紧跟一个合法的 JSON 对象，随后以两个换行符 `\n\n` 结束当前传输的数据块。最后，在所有数据块均传输完成时，会使用 `data: [DONE]` 来标识传输已完成，此时可断开网络连接。

### [](#tokens-计算)

当使用流式输出模式时，有两种计算 Tokens 的方式，最直接也是最准确的一种计算 Tokens 的方式，是等待所有数据块传输完毕后，通过访问最后一个数据块中的 `usage` 字段来查看整个流式输出过程中产生的 `prompt_tokens`/`completion_tokens`/`total_tokens`。

```text
...
 
data: {"id":"cmpl-1305b94c570f447fbde3180560736287","object":"chat.completion.chunk","created":1698999575,"model":"kimi-k2-turbo-preview","choices":[{"index":0,"delta":{},"finish_reason":"stop","usage":{"prompt_tokens":19,"completion_tokens":13,"total_tokens":32}}]}
                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                               通过访问最后一个数据块中的 usage 字段来查看当前请求产生的 Tokens 数量
data: [DONE]
```

然而，在实际使用过程中，往往会面临流式输出过程中，因为不可控因素导致输出被中断（例如网络连接中断，客户端程序错误等），此时，往往最后一个数据块尚未传输完毕，也就无从得知整个请求所消耗的 Tokens 数量。为了避免这种计算 Tokens 失败的场景，我们建议将每个已经获取的数据块的内容保存下来，并在请求结束后（无论是否成功结束），使用 Tokens 计算接口计算已经产生的总消耗量，示例代码如下所示：

```python
import os
import httpx
from openai import OpenAI
 
client = OpenAI(
    api_key = "MOONSHOT_API_KEY", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url = "https://api.moonshot.cn/v1",
)
 
stream = client.chat.completions.create(
    model = "kimi-k2-turbo-preview",
    messages = [
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"}
    ],
    temperature = 0.6,
    stream=True, # <-- 注意这里，我们通过设置 stream=True 开启流式输出模式
)
 
 
def estimate_token_count(input: str) -> int:
    """
    在这里实现你的 Tokens 计算逻辑，或是直接调用我们的 Tokens 计算接口计算 Tokens
 
    https://api.moonshot.cn/v1/tokenizers/estimate-token-count
    """
    header = {
        "Authorization": f"Bearer {os.environ['MOONSHOT_API_KEY']}",
    }
    data = {
        "model": "kimi-k2-turbo-preview",
        "messages": [
            {"role": "user", "content": input},
        ]
    }
    r = httpx.post("https://api.moonshot.cn/v1/tokenizers/estimate-token-count", headers=header, json=data)
    r.raise_for_status()
    return r.json()["data"]["total_tokens"]
 
 
completion = []
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        completion.append(delta.content)
 
 
print("completion_tokens:", estimate_token_count("".join(completion)))
```

### [](#如何终止输出)

如果你想要终止流式输出，你可以直接关闭 HTTP 网络连接，或是直接丢弃后续的数据块。例如：

```python
for chunk in stream:
    if condition:
        break
```

## [](#在不使用-sdk-的场合下如何处理流式输出)

如果你不想使用 Python SDK 来处理流式输出，而是想直接以对接 HTTP 接口的方式来使用 Kimi 大模型（例如某些没有 SDK 的语言，或是你有自己独特的业务逻辑而 SDK 无法满足的情况），我们给出一些示例来帮助你理解如何正确处理 HTTP 中 [SSE (opens in a new tab)](https://kimi.moonshot.cn/share/cr7boh3dqn37a5q9tds0) 响应体（在这里我们仍然以 Python 代码为例，详细的说明将以注释的形式呈现）。

```python
import httpx # 我们使用 httpx 库来执行我们的 HTTP 请求
 
 
data = {
    "model": "kimi-k2-turbo-preview",
    "messages": [
        # 具体的 messages
    ],
    "temperature": 0.6,
    "stream": True,
}
 
 
# 使用 httpx 向 Kimi 大模型发出 chat 请求，并获得响应 r
r = httpx.post("https://api.moonshot.cn/v1/chat/completions", json=data)
if r.status_code != 200:
    raise Exception(r.text)
 
 
data: str
 
# 在这里，我们使用了 iter_lines 方法来逐行读取响应体
for line in r.iter_lines():
    # 去除每一行收尾的空格，以便更好地处理数据块
    line = line.strip()
 
    # 接下来我们要处理三种不同的情况：
    #   1. 如果当前行是空行，则表明前一个数据块已接收完毕（即前文提到的，通过两个换行符结束数据块传输），我们可以对该数据块进行反序列化，并打印出对应的 content 内容；
    #   2. 如果当前行为非空行，且以 data: 开头，则表明这是一个数据块传输的开始，我们去除 data: 前缀后，首先判断是否是结束符 [DONE]，如果不是，将数据内容保存到 data 变量；
    #   3. 如果当前行为非空行，但不以 data: 开头，则表明当前行仍然归属上一个正在传输的数据块，我们将当前行的内容追加到 data 变量尾部；
 
    if len(line) == 0:
        chunk = json.loads(data)
 
        # 这里的处理逻辑可以替换成你的业务逻辑，打印仅是为了展示处理流程
        choice = chunk["choices"][0]
        usage = choice.get("usage")
        if usage:
            print("total_tokens:", usage["total_tokens"])
        delta = choice["delta"]
        role = delta.get("role")
        if role:
            print("role:", role)
        content = delta.get("content")
        if content:
            print(content, end="")
 
        data = "" # 重置 data
    elif line.startswith("data: "):
        data = line.lstrip("data: ")
 
        # 当数据块内容为 [DONE] 时，则表明所有数据块已发送完毕，可断开网络连接
        if data == "[DONE]":
            break
    else:
        data = data + "\n" + line # 我们仍然在追加内容时，为其添加一个换行符，因为这可能是该数据块有意将数据分行展示
```

以上是以 Python 为例的流式输出处理流程，如果你使用其他语言，也可以正确处理流式输出的内容，其基本步骤如下：

1.  发起 HTTP 请求，并在请求体中，将 `stream` 参数设置为 `true`；
2.  接收服务端返回的响应，注意到响应 `Headers` 中的 `Content-Type` 为 `text/event-stream`，则说明当前响应内容为流式输出；
3.  逐行读取响应内容并解析数据块（数据块以 JSON 格式呈现），注意通过 `data:` 前缀及换行符 `\n` 来判断数据块的开始位置和结束位置；
4.  通过判断当前数据块内容是否为 `[DONE]` 来判断是否已传输完成；

*注意，请始终使用 `data: [DONE]` 来判断数据是否已传输完成，而不是使用 `finish_reason` 或其他方式。如果未接收到 `data: [DONE]` 的消息块，即使已经获取了 `finish_reason=stop` 的信息，也不应视作数据块传输已完成。换句话说，在未接收到 `data: [DONE]` 的数据块前，都应视作**消息是不完整的**。*

在流式输出过程中，只有 `content` 字段会被流式输出，即每个数据块包含 `content` 的部分 Tokens，而对于不需要流式输出的字段，例如 `role` 和 `usage`，我们通常会在第一个或最后一个数据块中一次呈现，而不会在每个数据块中都包含 `role` 和 `usage` 字段（具体的，`role` 字段仅会在第一个数据块中出现，在后续数据块中不会包含 `role` 字段；而 `usage` 字段仅会在最后一个数据块中出现，而在前面的数据块中不会包含 `usage` 字段）。

# 10. Tool Calls 能力说明

## 使用 Kimi API 完成工具调用（tool\_calls）

*工具调用，即 `tool_calls`，由函数调用（即 `function_call`）进化而来，在某些特定的语境下，或在阅读一些兼容性代码时，你也可以将工具调用 `tool_calls` 与函数调用 `function_call` 划等号，函数调用 `function_call` 是工具调用 `tool_calls` 的子集。*

## [](#什么是工具调用-tool_calls)

工具调用 `tool_calls` 给予了 Kimi 大模型执行具体动作的能力。Kimi 大模型能进行对话聊天并回答用户提出的问题，这是“说”的能力，而通过工具调用 `tool_calls`，Kimi 大模型也拥有了“做”的能力，借助 `tool_calls`，Kimi 大模型能帮你搜索互联网内容、查询数据库，甚至操作智能家居。

一次工具调用 `tool_calls` 包含了以下若干步骤：

1.  使用 JSON Schema 格式定义工具；
2.  通过 `tools` 参数将定义好的工具提交给 Kimi 大模型，你可以一次性提交多个工具；
3.  Kimi 大模型会根据当前聊天的上下文，决定使用哪个或哪几个工具，Kimi 大模型也可以选择不使用工具；
4.  Kimi 大模型会将调用工具所需要的参数和信息通过 JSON 格式输出；
5.  使用 Kimi 大模型输出的参数，执行对应的工具，并将工具执行结果提交给 Kimi 大模型；
6.  Kimi 大模型根据工具执行结果，给予用户回复；

阅读上述步骤，你可能会产生这样的疑惑：

> 为什么 Kimi 大模型自己不能执行工具，还要我们根据 Kimi 大模型生成的工具参数“帮” Kimi 大模型执行工具？既然是我们在执行工具调用，还要 Kimi 大模型干什么？

我们会用一个实际的工具调用 `tool_calls` 案例来试图向读者讲明白这些问题。

## [](#通过-tool_calls-让-kimi-大模型拥有联网查询能力)

Kimi 大模型的知识来源于它的训练数据，对于一些时效性强的问题，Kimi 大模型无法从自己已有的知识中获取答案，此时，我们希望 Kimi 大模型能自己在互联网上搜索查询最新的知识，并根据这些知识回答我们提出的问题。

### [](#定义工具)

想象一下，我们自己是如何在网络上找到自己想要的信息的：

1.  我们会先打开搜索引擎，例如百度或必应，在搜索引擎中搜索我们想要的内容，然后浏览搜索结果，根据网站标题和网站简介来决定点击哪个搜索结果；
2.  我们可能会打开一个或多个搜索结果的网页，浏览网页并获取我们需要的知识；

回顾一下我们的动作，我们“使用搜索引擎搜索”和“打开搜索结果对应的网页”，而我们使用的工具是“搜索引擎”和“网页浏览器”，因此，我们需要将动作对应的工具抽象成 JSON Schema 的格式提交给 Kimi 大模型，让 Kimi 大模型也能和人一样使用搜索引擎并浏览网页。

在此之前，让我们先简单介绍一下 JSON Schema 格式：

> [JSON Schema (opens in a new tab)](https://json-schema.org/) is a vocabulary that you can use to annotate and validate JSON documents.
> 
> [JSON Schema (opens in a new tab)](https://json-schema.org/) 是一种用于描述 JSON 数据格式的 JSON 文档。

我们定义以下 JSON Schema：

```json
{
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        }
    }
}
```

这个 JSON Schema 定义了一个 JSON Object，这个 JSON Object 中包含了一个名为 `name` 的字段，并且该字段的类型为 `string`，例如：

```json
{
    "name": "Hei"
}
```

通过 JSON Schema 来描述我们的工具定义，能让 Kimi 大模型更清晰和直观地知道我们的工具需要哪些参数，以及每个参数的类型和介绍。接下来让我们来定义前文提到的“搜索引擎”和“网页浏览器”这两个工具：

```python
tools = [
    {
        "type": "function", # 约定的字段 type，目前支持 function 作为值
        "function": { # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "search", # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """ 
                通过搜索引擎搜索互联网上的内容。
 
                当你的知识无法回答用户提出的问题，或用户请求你进行联网搜索时，调用此工具。请从与用户的对话中提取用户想要搜索的内容作为 query 参数的值。
                搜索结果包含网站的标题、网站的地址（URL）以及网站简介。
            """, # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": { # 使用 parameters 字段来定义函数接收的参数
                "type": "object", # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["query"], # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": { # properties 中是具体的参数定义，你可以定义多个参数
                    "query": { # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string", # 使用 type 定义参数类型
                        "description": """
                            用户搜索的内容，请从用户的提问或聊天上下文中提取。
                        """ # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    },
    {
        "type": "function", # 约定的字段 type，目前支持 function 作为值
        "function": { # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "crawl", # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """
                根据网站地址（URL）获取网页内容。
            """, # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": { # 使用 parameters 字段来定义函数接收的参数
                "type": "object", # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["url"], # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": { # properties 中是具体的参数定义，你可以定义多个参数
                    "url": { # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string", # 使用 type 定义参数类型
                        "description": """
                            需要获取内容的网站地址（URL），通常情况下从搜索结果中可以获取网站的地址。
                        """ # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    }
]
```

在使用 JSON Schema 定义工具时，我们使用以下固定的格式来定义一个工具：

```json
{
    "type": "function",
    "function": {
        "name": "NAME",
        "description": "DESCRIPTION",
        "parameters": {
            "type": "object",
            "properties": {
                
            }
        }
    }
}
```

其中，`name`、`description`、`parameters.properties` 由工具提供方定义，其中 `description` 描述了工具的具体作用、以及在什么场合需要使用工具，`parameters` 描述了成功调用工具所需要的具体参数，包括参数类型、参数介绍等；**最终，Kimi 大模型会根据 JSON Schema 的定义，生成一个满足定义要求的 JSON Object 作为工具调用的参数（arguments）。**

### [](#注册工具)

让我们试试把 `search` 这个工具提交给 Kimi 大模型，看看 Kimi 大模型能否正确调用工具：

```python
from openai import OpenAI
 
 
client = OpenAI(
    api_key="MOONSHOT_API_KEY", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url="https://api.moonshot.cn/v1",
)
 
tools = [
    {
        "type": "function", # 约定的字段 type，目前支持 function 作为值
        "function": { # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "search", # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """ 
                通过搜索引擎搜索互联网上的内容。
 
                当你的知识无法回答用户提出的问题，或用户请求你进行联网搜索时，调用此工具。请从与用户的对话中提取用户想要搜索的内容作为 query 参数的值。
                搜索结果包含网站的标题、网站的地址（URL）以及网站简介。
            """, # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": { # 使用 parameters 字段来定义函数接收的参数
                "type": "object", # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["query"], # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": { # properties 中是具体的参数定义，你可以定义多个参数
                    "query": { # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string", # 使用 type 定义参数类型
                        "description": """
                            用户搜索的内容，请从用户的提问或聊天上下文中提取。
                        """ # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    },
    # {
    # 	"type": "function", # 约定的字段 type，目前支持 function 作为值
    # 	"function": { # 当 type 为 function 时，使用 function 字段定义具体的函数内容
    # 		"name": "crawl", # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
    # 		"description": """
    # 			根据网站地址（URL）获取网页内容。
    # 		""", # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
    # 		"parameters": { # 使用 parameters 字段来定义函数接收的参数
    # 			"type": "object", # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
    # 			"required": ["url"], # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
    # 			"properties": { # properties 中是具体的参数定义，你可以定义多个参数
    # 				"url": { # 在这里，key 是参数名称，value 是参数的具体定义
    # 					"type": "string", # 使用 type 定义参数类型
    # 					"description": """
    # 						需要获取内容的网站地址（URL），通常情况下从搜索结果中可以获取网站的地址。
    # 					""" # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
    # 				}
    # 			}
    # 		}
    # 	}
    # }
]
 
completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "user", "content": "请联网搜索 Context Caching，并告诉我它是什么。"} # 在提问中要求 Kimi 大模型联网搜索
    ],
    temperature=0.6,
    tools=tools, # <-- 我们通过 tools 参数，将定义好的 tools 提交给 Kimi 大模型
)
 
print(completion.choices[0].model_dump_json(indent=4))
```

当上述代码运行成功时，我们获得 Kimi 大模型的返回内容：

```json
{
    "finish_reason": "tool_calls",
    "message": {
        "content": "",
        "role": "assistant",
        "tool_calls": [
            {
                "id": "search:0",
                "function": {
                    "arguments": "{\n    \"query\": \"Context Caching\"\n}",
                    "name": "search"
                },
                "type": "function",
            }
        ]
    }
}
```

注意看，在这次的回复中，`finish_reason` 的值为 `tool_calls`，这意味着本次请求返回的并不是 Kimi 大模型的回复，而是 Kimi 大模型选择执行工具。你可以通过 `finish_reason` 的值来判断当前 Kimi 大模型的回复是否是一次工具调用 `tool_calls`。

在 `meessage` 部分，`content` 字段是空值，这是因为当前正在执行 `tool_calls`，模型并没有生成面向用户的回复；同时新增了 `tool_calls` 字段，`tool_calls` 字段是一个列表，其中包含了本次需要调用的所有工具调用信息，这同时也表明了 `tool_calls` 的另一个特性，即：**模型可以一次性选择多个工具进行调用，可以是多个不同的工具，也可以是相同工具使用不同参数进行调用**。`tool_calls` 中的每个元素都代表了一次工具调用，Kimi 大模型会为每次工具调用生成一个唯一的 `id`，通过 `function.name` 字段表明当前执行的工具函数名称，并把执行的参数放置在 `function.arguments` 中，`arguments` 参数是一个合法的被序列化的 JSON Obejct（额外的，`type` 参数在目前是固定值 `function`）。

接下来，我们应该使用 Kimi 大模型生成的工具调用参数去执行具体的工具。

### [](#执行工具)

Kimi 大模型并不会帮我们执行工具，需要由我们在接收到 Kimi 大模型生成的参数后自行执行参数，在讲述如何执行工具之前，让我们先解答之前提到的问题：

> 为什么 Kimi 大模型自己不能执行工具，还要我们根据 Kimi 大模型生成的工具参数“帮” Kimi 大模型执行工具？既然是我们在执行工具调用，还要 Kimi 大模型干什么？

让我们设想一下我们使用 Kimi 大模型的应用场景： **我们向用户提供一个基于 Kimi 大模型的智能机器人，在这个场景有三个角色：用户、机器人、Kimi 大模型。用户向机器人提问，机器人调用 Kimi 大模型 API，并将 API 的结果返回给用户。当使用 `tool_calls` 时，用户向机器人提问，机器人带着 `tools` 调用 Kimi API，Kimi 大模型返回 `tool_calls` 参数，机器人执行完 `tool_calls`，将结果再次提交给 Kimi API，Kimi 大模型生成返回给用户的消息（`finish_reason=stop`），此时机器人才会把消息返回给用户。** 在这个过程中，`tool_calls` 的全过程对用户而言都是透明的、隐式的。

回到上述问题，作为用户的我们其实并没有在执行工具调用，也不会直接“看到”工具调用，而是给我们提供服务的机器人在完成工具调用，并将最终 Kimi 大模型生成的回复内容呈现给我们。

让我们以“机器人”的视角来讲解如何执行 Kimi 大模型返回的 `tool_calls`：

```python
from typing import *
 
import json
 
from openai import OpenAI
 
 
client = OpenAI(
    api_key="MOONSHOT_API_KEY", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url="https://api.moonshot.cn/v1",
)
 
tools = [
    {
        "type": "function", # 约定的字段 type，目前支持 function 作为值
        "function": { # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "search", # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """ 
                通过搜索引擎搜索互联网上的内容。
 
                当你的知识无法回答用户提出的问题，或用户请求你进行联网搜索时，调用此工具。请从与用户的对话中提取用户想要搜索的内容作为 query 参数的值。
                搜索结果包含网站的标题、网站的地址（URL）以及网站简介。
            """, # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": { # 使用 parameters 字段来定义函数接收的参数
                "type": "object", # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["query"], # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": { # properties 中是具体的参数定义，你可以定义多个参数
                    "query": { # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string", # 使用 type 定义参数类型
                        "description": """
                            用户搜索的内容，请从用户的提问或聊天上下文中提取。
                        """ # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    },
    {
        "type": "function", # 约定的字段 type，目前支持 function 作为值
        "function": { # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "crawl", # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """
                根据网站地址（URL）获取网页内容。
            """, # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": { # 使用 parameters 字段来定义函数接收的参数
                "type": "object", # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["url"], # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": { # properties 中是具体的参数定义，你可以定义多个参数
                    "url": { # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string", # 使用 type 定义参数类型
                        "description": """
                            需要获取内容的网站地址（URL），通常情况下从搜索结果中可以获取网站的地址。
                        """ # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    }
]
 
 
def search_impl(query: str) -> List[Dict[str, Any]]:
    """
    search_impl 使用搜索引擎对 query 进行搜索，目前主流的搜索引擎（例如 Bing）都提供了 API 调用方式，你可以自行选择
    你喜欢的搜索引擎 API 进行调用，并将返回结果中的网站标题、网站链接、网站简介信息放置在一个 dict 中返回。
 
    这里只是一个简单的示例，你可能需要编写一些鉴权、校验、解析的代码。
    """
    r = httpx.get("https://your.search.api", params={"query": query})
    return r.json()
 
 
def search(arguments: Dict[str, Any]) -> Any:
    query = arguments["query"]
    result = search_impl(query)
    return {"result": result}
 
 
def crawl_impl(url: str) -> str:
    """
    crawl_url 根据 url 获取网页上的内容。
 
    这里只是一个简单的示例，在实际的网页抓取过程中，你可能需要编写更多的代码来适配复杂的情况，例如异步加载的数据等；同时，在获取
    网页内容后，你可以根据自己的需要对网页内容进行清洗，只保留文本或移除不必要的内容（例如广告信息等）。
    """
    r = httpx.get(url)
    return r.text
 
 
def crawl(arguments: dict) -> str:
    url = arguments["url"]
    content = crawl_impl(url)
    return {"content": content}
 
 
# 通过 tool_map 将每个工具名称及其对应的函数进行映射，以便在 Kimi 大模型返回 tool_calls 时能快速找到应该执行的函数
tool_map = {
    "search": search,
    "crawl": crawl,
}
 
messages = [
    {"role": "system",
     "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
    {"role": "user", "content": "请联网搜索 Context Caching，并告诉我它是什么。"}  # 在提问中要求 Kimi 大模型联网搜索
]
 
finish_reason = None
 
# 我们的基本流程是，带着用户的问题和 tools 向 Kimi 大模型提问，如果 Kimi 大模型返回了 finish_reason: tool_calls，则我们执行对应的 tool_calls，
# 将执行结果以 role=tool 的 message 的形式重新提交给 Kimi 大模型，Kimi 大模型根据 tool_calls 结果进行下一步内容的生成：
#
#   1. 如果 Kimi 大模型认为当前的工具调用结果已经可以回答用户问题，则返回 finish_reason: stop，我们会跳出循环，打印出 message.content；
#   2. 如果 Kimi 大模型认为当前的工具调用结果无法回答用户问题，需要再次调用工具，我们会继续在循环中执行接下来的 tool_calls，直到 finish_reason 不再是 tool_calls；
#
# 在这个过程中，只有当 finish_reason 为 stop 时，我们才会将结果返回给用户。
 
while finish_reason is None or finish_reason == "tool_calls":
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",
        messages=messages,
        temperature=0.6,
        tools=tools,  # <-- 我们通过 tools 参数，将定义好的 tools 提交给 Kimi 大模型
    )
    choice = completion.choices[0]
    finish_reason = choice.finish_reason
    if finish_reason == "tool_calls": # <-- 判断当前返回内容是否包含 tool_calls
        messages.append(choice.message) # <-- 我们将 Kimi 大模型返回给我们的 assistant 消息也添加到上下文中，以便于下次请求时 Kimi 大模型能理解我们的诉求
        for tool_call in choice.message.tool_calls: # <-- tool_calls 可能是多个，因此我们使用循环逐个执行
            tool_call_name = tool_call.function.name
            tool_call_arguments = json.loads(tool_call.function.arguments) # <-- arguments 是序列化后的 JSON Object，我们需要使用 json.loads 反序列化一下
            tool_function = tool_map[tool_call_name] # <-- 通过 tool_map 快速找到需要执行哪个函数
            tool_result = tool_function(tool_call_arguments)
 
            # 使用函数执行结果构造一个 role=tool 的 message，以此来向模型展示工具调用的结果；
            # 注意，我们需要在 message 中提供 tool_call_id 和 name 字段，以便 Kimi 大模型
            # 能正确匹配到对应的 tool_call。
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call_name,
                "content": json.dumps(tool_result), # <-- 我们约定使用字符串格式向 Kimi 大模型提交工具调用结果，因此在这里使用 json.dumps 将执行结果序列化成字符串
            })
 
print(choice.message.content) # <-- 在这里，我们才将模型生成的回复返回给用户
```

我们使用 while 循环来执行包含工具调用在内的代码逻辑，这是因为 Kimi 大模型通常不会只执行一次工具调用，尤其是在联网搜索这个场景，通常，Kimi 大模型会先选择调用 `search` 工具，通过 `search` 工具获取搜索结果后，再调用 `crawl` 工具将搜索结果中的 `url` 转换为具体的网页内容，整体的 messages 结构如下所示：

```text
system: prompt                                                                                               # 系统提示词
user: prompt                                                                                                 # 用户提问
assistant: tool_call(name=search, arguments={query: query})                                                  # Kimi 大模型返回 tool_call 调用（单个）                            
tool: search_result(tool_call_id=tool_call.id, name=search)                                                  # 提交 tool_call 执行结果
assistant: tool_call_1(name=crawl, arguments={url: url_1}), tool_call_2(name=crawl, arguments={url: url_2})  # Kimi 大模型继续返回 tool_calls 调用（多个）
tool: crawl_content(tool_call_id=tool_call_1.id, name=crawl)                                                 # 提交 tool_call_1 执行结果
tool: crawl_content(tool_call_id=tool_call_2.id, name=crawl)                                                 # 提交 tool_call_2 执行结果
assistant: message_content(finish_reason=stop)                                                               # Kimi 大模型生成面向用户的回复消息，本轮对话结束
```

至此，我们完成了“联网查询”工具调用的全过程，如果你实现了自己的 `search` 和 `crawl` 方法，那么当你向 Kimi 大模型要求联网查询时，它会调用 `search` 和 `crawl` 两个工具，并根据工具调用结果给予你正确的回复。

## [](#常见问题及注意事项)

### [](#关于流式输出)

在流式输出模式（stream）下，`tool_calls` 同样适用，但有一些需要额外注意的地方，列举如下：

+   在流式输出的过程中，由于 `finish_reason` 将会在最后的数据块中出现，因此建议使用 `delta.tool_calls` 字段是否存在来判断当前回复是否包含工具调用；
+   在流式输出的过程中，会先输出 `delta.content`，再输出 `delta.tool_calls`，因此你必须等待 `delta.content` 输出完成后，才能判断和识别 `tool_calls`；
+   在流式输出的过程中，我们会在最初的数据块中，指明当前调用 `tool_calls` 的 `tool_call.id` 和 `tool_call.function.name`，在后续的数据块中将只输出 `tool_call.function.arguments`；
+   在流式输出的过程中，如果 Kimi 大模型一次性返回多个 `tool_calls`，那么我们会额外使用一个名为 `index` 的字段来标识当前 `tool_call` 的索引，以便于你能正确拼接 `tool_call.function.arguments` 参数，我们使用流式输出章节中的代码例子（不使用 SDK 的场合）来说明如何操作：

```python
import os
import json
import httpx  # 我们使用 httpx 库来执行我们的 HTTP 请求
 
tools = [
    {
        "type": "function",  # 约定的字段 type，目前支持 function 作为值
        "function": {  # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "search",  # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """ 
                通过搜索引擎搜索互联网上的内容。
 
                当你的知识无法回答用户提出的问题，或用户请求你进行联网搜索时，调用此工具。请从与用户的对话中提取用户想要搜索的内容作为 query 参数的值。
                搜索结果包含网站的标题、网站的地址（URL）以及网站简介。
            """,  # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": {  # 使用 parameters 字段来定义函数接收的参数
                "type": "object",  # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["query"],  # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": {  # properties 中是具体的参数定义，你可以定义多个参数
                    "query": {  # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string",  # 使用 type 定义参数类型
                        "description": """
                            用户搜索的内容，请从用户的提问或聊天上下文中提取。
                        """  # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    },
]
 
header = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ.get('MOONSHOT_API_KEY')}",
}
 
data = {
    "model": "kimi-k2-turbo-preview",
    "messages": [
        {"role": "user", "content": "请联网搜索 Context Caching 技术。"}
    ],
    "temperature": 0.6,
    "stream": True,
    "n": 2,  # <-- 注意这里，我们要求 Kimi 大模型输出 2 个回复
    "tools": tools,  # <-- 添加工具调用
}
 
# 使用 httpx 向 Kimi 大模型发出 chat 请求，并获得响应 r
r = httpx.post("https://api.moonshot.cn/v1/chat/completions",
               headers=header,
               json=data)
if r.status_code != 200:
    raise Exception(r.text)
 
data: str
 
# 在这里，我们预先构建一个 List，用于存放不同的回复消息，由于我们设置了 n=2，因此我们将 List 初始化为 2 个元素
messages = [{}, {}]
 
# 在这里，我们使用了 iter_lines 方法来逐行读取响应体
for line in r.iter_lines():
    # 去除每一行收尾的空格，以便更好地处理数据块
    line = line.strip()
 
    # 接下来我们要处理三种不同的情况：
    #   1. 如果当前行是空行，则表明前一个数据块已接收完毕（即前文提到的，通过两个换行符结束数据块传输），我们可以对该数据块进行反序列化，并打印出对应的 content 内容；
    #   2. 如果当前行为非空行，且以 data: 开头，则表明这是一个数据块传输的开始，我们去除 data: 前缀后，首先判断是否是结束符 [DONE]，如果不是，将数据内容保存到 data 变量；
    #   3. 如果当前行为非空行，但不以 data: 开头，则表明当前行仍然归属上一个正在传输的数据块，我们将当前行的内容追加到 data 变量尾部；
 
    if len(line) == 0:
        chunk = json.loads(data)
 
        # 通过循环获取每个数据块中所有的 choice，并获取 index 对应的 message 对象
        for choice in chunk["choices"]:
            index = choice["index"]
            message = messages[index]
            usage = choice.get("usage")
            if usage:
                message["usage"] = usage
            delta = choice["delta"]
            role = delta.get("role")
            if role:
                message["role"] = role
            content = delta.get("content")
            if content:
                if "content" not in message:
                    message["content"] = content
                else:
                    message["content"] = message["content"] + content
 
            # 从这里，我们开始处理 tool_calls
            tool_calls = delta.get("tool_calls")  # <-- 先判断数据块中是否包含 tool_calls
            if tool_calls:
                if "tool_calls" not in message:
                    message["tool_calls"] = []  # <-- 如果包含 tool_calls，我们初始化一个列表来保存这些 tool_calls，注意此时的列表中没有任何元素，长度为 0
                for tool_call in tool_calls:
                    tool_call_index = tool_call["index"]  # <-- 获取当前 tool_call 的 index 索引
                    if len(message["tool_calls"]) < (
                            tool_call_index + 1):  # <-- 根据 index 索引扩充 tool_calls 列表，以便于我们能通过下标访问到对应的 tool_call
                        message["tool_calls"].extend([{}] * (tool_call_index + 1 - len(message["tool_calls"])))
                    tool_call_object = message["tool_calls"][tool_call_index]  # <-- 根据下标访问对应的 tool_call
                    tool_call_object["index"] = tool_call_index
 
                    # 下面的步骤，是根据数据块中的信息填充每个 tool_call 的 id、type、function 字段
                    # 在 function 字段中，又包括 name 和 arguments 字段，arguments 字段会由每个数据块
                    # 依次补充，如同 delta.content 字段一般。
 
                    tool_call_id = tool_call.get("id")
                    if tool_call_id:
                        tool_call_object["id"] = tool_call_id
                    tool_call_type = tool_call.get("type")
                    if tool_call_type:
                        tool_call_object["type"] = tool_call_type
                    tool_call_function = tool_call.get("function")
                    if tool_call_function:
                        if "function" not in tool_call_object:
                            tool_call_object["function"] = {}
                        tool_call_function_name = tool_call_function.get("name")
                        if tool_call_function_name:
                            tool_call_object["function"]["name"] = tool_call_function_name
                        tool_call_function_arguments = tool_call_function.get("arguments")
                        if tool_call_function_arguments:
                            if "arguments" not in tool_call_object["function"]:
                                tool_call_object["function"]["arguments"] = tool_call_function_arguments
                            else:
                                tool_call_object["function"]["arguments"] = tool_call_object["function"][
                                                                            "arguments"] + tool_call_function_arguments  # <-- 依次补充 function.arguments 字段的值
                    message["tool_calls"][tool_call_index] = tool_call_object
 
            data = ""  # 重置 data
    elif line.startswith("data: "):
        data = line.lstrip("data: ")
 
        # 当数据块内容为 [DONE] 时，则表明所有数据块已发送完毕，可断开网络连接
        if data == "[DONE]":
            break
    else:
        data = data + "\n" + line  # 我们仍然在追加内容时，为其添加一个换行符，因为这可能是该数据块有意将数据分行展示
 
# 在组装完所有 messages 后，我们分别打印其内容
for index, message in enumerate(messages):
    print("index:", index)
    print("message:", json.dumps(message, ensure_ascii=False))
    print("")
```

以下是使用 openai SDK 处理流式输出中的 `tool_calls` 的代码示例：

```python
import os
import json
 
from openai import OpenAI
 
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)
 
tools = [
    {
        "type": "function",  # 约定的字段 type，目前支持 function 作为值
        "function": {  # 当 type 为 function 时，使用 function 字段定义具体的函数内容
            "name": "search",  # 函数的名称，请使用英文大小写字母、数据加上减号和下划线作为函数名称
            "description": """ 
                通过搜索引擎搜索互联网上的内容。
 
                当你的知识无法回答用户提出的问题，或用户请求你进行联网搜索时，调用此工具。请从与用户的对话中提取用户想要搜索的内容作为 query 参数的值。
                搜索结果包含网站的标题、网站的地址（URL）以及网站简介。
            """,  # 函数的介绍，在这里写上函数的具体作用以及使用场景，以便 Kimi 大模型能正确地选择使用哪些函数
            "parameters": {  # 使用 parameters 字段来定义函数接收的参数
                "type": "object",  # 固定使用 type: object 来使 Kimi 大模型生成一个 JSON Object 参数
                "required": ["query"],  # 使用 required 字段告诉 Kimi 大模型哪些参数是必填项
                "properties": {  # properties 中是具体的参数定义，你可以定义多个参数
                    "query": {  # 在这里，key 是参数名称，value 是参数的具体定义
                        "type": "string",  # 使用 type 定义参数类型
                        "description": """
                            用户搜索的内容，请从用户的提问或聊天上下文中提取。
                        """  # 使用 description 描述参数以便 Kimi 大模型更好地生成参数
                    }
                }
            }
        }
    },
]
 
completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {"role": "user", "content": "请联网搜索 Context Caching 技术。"}
    ],
    temperature=0.6,
    stream=True,
    n=2,  # <-- 注意这里，我们要求 Kimi 大模型输出 2 个回复
    tools=tools,  # <-- 添加工具调用
)
 
# 在这里，我们预先构建一个 List，用于存放不同的回复消息，由于我们设置了 n=2，因此我们将 List 初始化为 2 个元素
messages = [{}, {}]
 
for chunk in completion:
    # 通过循环获取每个数据块中所有的 choice，并获取 index 对应的 message 对象
    for choice in chunk.choices:
        index = choice.index
        message = messages[index]
        delta = choice.delta
        role = delta.role
        if role:
            message["role"] = role
        content = delta.content
        if content:
            if "content" not in message:
                message["content"] = content
            else:
                message["content"] = message["content"] + content
 
        # 从这里，我们开始处理 tool_calls
        tool_calls = delta.tool_calls  # <-- 先判断数据块中是否包含 tool_calls
        if tool_calls:
            if "tool_calls" not in message:
                message["tool_calls"] = []  # <-- 如果包含 tool_calls，我们初始化一个列表来保存这些 tool_calls，注意此时的列表中没有任何元素，长度为 0
            for tool_call in tool_calls:
                tool_call_index = tool_call.index  # <-- 获取当前 tool_call 的 index 索引
                if len(message["tool_calls"]) < (
                        tool_call_index + 1):  # <-- 根据 index 索引扩充 tool_calls 列表，以便于我们能通过下标访问到对应的 tool_call
                    message["tool_calls"].extend([{}] * (tool_call_index + 1 - len(message["tool_calls"])))
                tool_call_object = message["tool_calls"][tool_call_index]  # <-- 根据下标访问对应的 tool_call
                tool_call_object["index"] = tool_call_index
 
                # 下面的步骤，是根据数据块中的信息填充每个 tool_call 的 id、type、function 字段
                # 在 function 字段中，又包括 name 和 arguments 字段，arguments 字段会由每个数据块
                # 依次补充，如同 delta.content 字段一般。
 
                tool_call_id = tool_call.id
                if tool_call_id:
                    tool_call_object["id"] = tool_call_id
                tool_call_type = tool_call.type
                if tool_call_type:
                    tool_call_object["type"] = tool_call_type
                tool_call_function = tool_call.function
                if tool_call_function:
                    if "function" not in tool_call_object:
                        tool_call_object["function"] = {}
                    tool_call_function_name = tool_call_function.name
                    if tool_call_function_name:
                        tool_call_object["function"]["name"] = tool_call_function_name
                    tool_call_function_arguments = tool_call_function.arguments
                    if tool_call_function_arguments:
                        if "arguments" not in tool_call_object["function"]:
                            tool_call_object["function"]["arguments"] = tool_call_function_arguments
                        else:
                            tool_call_object["function"]["arguments"] = tool_call_object["function"][
                                                                            "arguments"] + tool_call_function_arguments  # <-- 依次补充 function.arguments 字段的值
                message["tool_calls"][tool_call_index] = tool_call_object
 
# 在组装完所有 messages 后，我们分别打印其内容
for index, message in enumerate(messages):
    print("index:", index)
    print("message:", json.dumps(message, ensure_ascii=False))
    print("")
```

### [](#关于-tool_calls-和-function_call)

`tool_calls` 是 `function_call` 的进阶版，由于 openai 已将 `function_call` 等参数（例如 `functions`）标记为“已废弃”，因此我们的 API 将不再支持 `function_call`。你可以考虑用 `tool_calls` 代替 `function_call`，相比于 `function_call`，`tool_calls` 有以下几个优点：

+   支持并行调用，Kimi 大模型可以一次返回多个 `tool_calls`，你可以在代码中使用并发的方式同时调用这些 `tool_call` 以减少时间消耗；
+   对于没有依赖关系的 `tool_calls`，Kimi 大模型也会倾向于并行调用，这相比于原顺序调用的 `function_call`，在一定程度上降低了 Tokens 消耗；

### [](#关于-content)

在使用工具调用 `tool_calls` 的过程中，你可能会发现，在 `finish_reason=tool_calls` 的情况下，偶尔会出现 `message.content` 字段不为空的情况，通常这里的 `content` 内容是 Kimi 大模型在解释当前需要调用哪些工具和为什么需要调用这些工具。它的意义在于，如果你的工具调用过程耗时很长，或是完成一轮对话需要串行调用多次工具，那么在调用工具前给予用户一段描述性的语句，能减少用户因为等待而产生的焦虑或不满情绪，同时，向用户说明当前调用了哪些工具和为什么调用工具，也有助于用户理解整个工具调用的流程，并及时给予干预和矫正（例如用户认为当前工具选择错误，可以及时终止工具调用，或是在下轮对话中通过提示词矫正模型的工具选择）。

### [](#关于-tokens)

`tools` 参数中的内容也会被计算在总 Tokens 中，请确保 `tools`、`messages` 中的 Tokens 总数合计不超过模型的上下文窗口大小。

### [](#关于消息布局)

在使用工具调用的场景下，我们的消息不再是：

```text
system: ...
user: ...
assistant: ...
user: ...
assistant: ...
```

这样排布，而是会变成形似

```text
system: ...
user: ...
assistant: ...
tool: ...
tool: ...
assistant: ...
```

这样的排布，需要注意的是，当 Kimi 大模型生成了 `tool_calls` 时，请确保每一个 `tool_call` 都有对应的 `role=tool` 的 message，并且这条 message 设置了正确的 `tool_call_id`，如果 `role=tool` 的 messages 消息数量与 `tool_calls` 的数量不一致会导致错误；如果 `role=tool` 的 messages 中的 `tool_call_id` 与 `tool_calls` 中的 `tool_call.id` 无法对应也会导致错误。

### [](#如果你遇到-tool_call_id-not-found-错误)

如果你遇到 `tool_call_id not found` 错误，可能是由于你未将 Kimi API 返回的 `role=assistant` 消息添加到 messages 列表中，正确的消息序列应该看起来像这样：

```text
system: ...
user: ...
assistant: ...  # <-- 也许你并未将这一条 assistant message 添加到 messages 列表中
tool: ...
tool: ...
assistant: ...
```

你可以在每次收到 Kimi API 的返回值后，都执行 `messages.append(message)` 来将 Kimi API 返回的消息添加到消息列表中，以避免出现 `tool_call_id not found` 错误。

*注意：添加到 messages 列表中位于 `role=tool` 的 message 之前的 assistant messages，必须完整包含 Kimi API 返回的 `tool_calls` 字段及字段值。我们推荐直接将 Kimi API 返回的 `choice.message` “原封不动”地添加到 messages 列表中，以避免可能产生的错误。*

# 11. 使用联网搜索工具

## 使用 Kimi API 的联网搜索功能

在之前的章节中（[使用 Kimi API 完成工具调用](https://platform.moonshot.cn/docs/guide/use-kimi-api-to-complete-tool-calls)），我们详细说明了如何通过 Kimi API 的工具调用 `tool_calls` 特性完成 Kimi 大模型的联网搜索功能，我们回顾一下之前实现过程的内容：

1.  使用 JSON Schema 格式定义工具，在联网搜索的场合，我们定义了 `search` 和 `crawl` 两个工具；
2.  通过 `tools` 参数将定义好的 `search` 和 `crawl` 提交给 Kimi 大模型；
3.  Kimi 大模型会根据当前聊天的上下文，选择调用 `search` 和 `crawl`，并生成相关参数，以 JSON 格式输出；
4.  使用 Kimi 大模型输出的参数，执行 `search` 和 `crawl` 函数，并将函数执行结果提交给 Kimi 大模型；
5.  Kimi 大模型根据工具执行结果，给予用户回复；

在实现联网搜索的过程中，我们需要自己实现 `search` 和 `crawl` 函数，这其中可能包括：

1.  调用搜索引擎接口，或自己实现内容搜索；
2.  获取搜索结果，包括 URL 和摘要等信息；
3.  根据 URL 获取网页内容，可能需要针对不同的网站应用不同的读取规则；
4.  将获取的网页内容清洗并整理成模型便于识别的格式，例如 Markdown；
5.  处理各种错误和异常情况，例如无搜索结果、网页内容获取失败等；

实现上述这些步骤通常被认为是繁琐和富有挑战性的，我们的用户多次提出想要一个简单方便、开箱即用的“联网搜索”功能；因此我们基于 Kimi 大模型原有的工具调用 `tool_calls` 用法，提供了一个 Kimi 内置的工具函数 `builtin_function.$web_search`，以实现联网搜索功能。

`$web_search` 函数的基本用法和流程与通常的工具调用 `tool_calls` 相同，但仍然有一些细小的差别，我们将通过例子详细讲解如何调用 Kimi 内置的 `$web_search` 函数实现联网搜索功能，并在代码和说明中标注需要额外注意的事项。

## [](#web_search-声明)

与普通的 `tool` 不同，`$web_search` 函数并不需要提供具体的参数说明，仅需要在 `tools` 声明中 `type` 和 `function.name` 即可成功注册 `$web_search` 函数：

```python
tools = [
    {
        "type": "builtin_function",  # <-- 我们使用 builtin_function 来表示 Kimi 内置工具，也用于区分普通 function
        "function": {
            "name": "$web_search",
        },
    },
]
```

**`$web_search` 以美元符号 ` 作为前缀，这是我们约定的表示 Kimi 内置函数的一种表达方式**（在普通的 `function` 定义中，不允许出现美元符号 `），后续如果有其他 Kimi 内置函数，也将以美元符号 ` 作为前缀。

在声明 `tools` 时，`$web_search` 可以与其他普通的 `function` 共存，进一步地，`builtin_function` 与普通 `function` 是可以共存的，你可以在 `tools` 中既添加 `builtin_function`，又添加普通 `function`，或是同时添加 `builtin_function` 和普通 `function`。

接下来，让我们改造原先的 `tool_calls` 代码，来讲解如何执行 `tool_calls`。

## [](#web_search-执行)

以下是经过改造后的 `tool_calls` 代码：

```python
from typing import *
 
import os
import json
 
from openai import OpenAI
from openai.types.chat.chat_completion import Choice
 
client = OpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.environ.get("MOONSHOT_API_KEY"),
)
 
 
# search 工具的具体实现，这里我们只需要返回参数即可
def search_impl(arguments: Dict[str, Any]) -> Any:
    """
    在使用 Moonshot AI 提供的 search 工具的场合，只需要原封不动返回 arguments 即可，
    不需要额外的处理逻辑。
 
    但如果你想使用其他模型，并保留联网搜索的功能，那你只需要修改这里的实现（例如调用搜索
    和获取网页内容等），函数签名不变，依然是 work 的。
 
    这最大程度保证了兼容性，允许你在不同的模型间切换，并且不需要对代码有破坏性的修改。
    """
    return arguments
 
 
def chat(messages) -> Choice:
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",
        messages=messages,
        temperature=0.6,
        max_tokens=32768,
        tools=[
            {
                "type": "builtin_function",  # <-- 使用 builtin_function 声明 $web_search 函数，请在每次请求都完整地带上 tools 声明
                "function": {
                    "name": "$web_search",
                },
            }
        ]
    )
    return completion.choices[0]
 
 
def main():
    messages = [
        {"role": "system", "content": "你是 Kimi。"},
    ]
 
    # 初始提问
    messages.append({
        "role": "user",
        "content": "请搜索 Moonshot AI Context Caching 技术，并告诉我它是什么。"
    })
 
    finish_reason = None
    while finish_reason is None or finish_reason == "tool_calls":
        choice = chat(messages)
        finish_reason = choice.finish_reason
        if finish_reason == "tool_calls":  # <-- 判断当前返回内容是否包含 tool_calls
            messages.append(choice.message)  # <-- 我们将 Kimi 大模型返回给我们的 assistant 消息也添加到上下文中，以便于下次请求时 Kimi 大模型能理解我们的诉求
            for tool_call in choice.message.tool_calls:  # <-- tool_calls 可能是多个，因此我们使用循环逐个执行
                tool_call_name = tool_call.function.name
                tool_call_arguments = json.loads(tool_call.function.arguments)  # <-- arguments 是序列化后的 JSON Object，我们需要使用 json.loads 反序列化一下
                if tool_call_name == "$web_search":
                    tool_result = search_impl(tool_call_arguments)
                else:
                    tool_result = f"Error: unable to find tool by name '{tool_call_name}'"
 
                # 使用函数执行结果构造一个 role=tool 的 message，以此来向模型展示工具调用的结果；
                # 注意，我们需要在 message 中提供 tool_call_id 和 name 字段，以便 Kimi 大模型
                # 能正确匹配到对应的 tool_call。
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call_name,
                    "content": json.dumps(tool_result),  # <-- 我们约定使用字符串格式向 Kimi 大模型提交工具调用结果，因此在这里使用 json.dumps 将执行结果序列化成字符串
                })
 
    print(choice.message.content)  # <-- 在这里，我们才将模型生成的回复返回给用户
 
 
if __name__ == '__main__':
    main()
```

回顾上述代码，我们惊讶地发现，在使用 `$web_search` 函数时，其基本流程与普通的 `function` 并无区别，开发者甚至可以不用修改原先执行工具调用 `tool_calls` 的代码。而其中不一样并且尤其显得特别的地方在于，我们在实现 `search_impl` 函数时，并没有过多的搜索、解析、获取网页内容的逻辑，我们只是简单地将 Kimi 大模型生成的参数 `tool_call.function.arguments` 原封不动地返回即可完成工具调用 `tool_calls`，这是为什么呢？

事实上，正如 `builtin_function` 的名称所指示的那样，`$web_search` 是 Kimi 大模型内置的函数，其由 Kimi 大模型定义，也由 Kimi 大模型执行。其流程为：

1.  当 Kimi 大模型生成了 `finish_reason=tool_calls` 的响应时，表明 Kimi 大模型已经意识到当前需要执行 `$web_search` 函数，并且也已经做好执行 `$web_search` 的一切准备工作；
2.  Kimi 大模型会将执行函数所必须得参数以 `tool_call.function.arguments` 的形式返回给调用方，但这些参数并不由调用方执行，调用方只需要将 `tool_call.function.arguments` 原封不动地提交给 Kimi 大模型，即可由 Kimi 大模型执行对应的联网搜索流程；
3.  当用户将 `tool_call.function.arguments` 使用 `role=tool` 的 `message` 提交时，Kimi 大模型随即开始执行联网搜索流程，并根据搜索和阅读结果生成可供用户阅读的消息，即 `finish_reason=stop` 的 `message`；

## [](#关于兼容性的说明)

Kimi API 提供的联网搜索功能，旨在不破坏原有 API 和 SDK 兼容性的前提下，提供一种可靠性高的大模型联网搜索解决方案，其完全兼容 Kimi 大模型原有的工具调用 `tool_calls` 特性，这意味着：**当你想从 Kimi 提供的联网搜索功能切换到自己实现的联网搜索功能时，只需要简单两步改动即可在不破坏代码整体结构的情况下完成：**

1.  将 `$web_search` 的 `tool` 定义修改成你自己实现的 `tool` 定义（包括 `name`、`description` 等），这可能需要在 `tool.function` 中添加额外的说明信息以告知模型具体需要生成哪些参数，你可以在 `parameters` 字段中添加任意你需要的参数信息；
2.  修改 `search_impl` 函数的实现，在使用 Kimi 提供的 `$web_search` 时，你只需要原封不动返回入参 `arguments` 即可，但如果你使用自己的联网搜索服务，你可能需要完整实现文章开头所提到的 `search` 和 `crawl` 功能；

完成上述步骤后，你就成功完成了从 Kimi 提供的联网搜索功能，迁移到自己实现的联网搜索功能的所有事项。

## [](#关于-tokens-消耗)

在使用 Kimi 提供的联网搜索函数 `$web_search` 时，搜索结果同样会被计入提示词所占用的 Tokens 中（即 `prompt_tokens`）。通常情况下，由于联网搜索的结果包含的内容众多，最终产生的 Tokens 消耗也会更多，为了避免在不知情的情况下消耗大量 Tokens，我们在生成 `$web_search` 函数的参数 `arguments` 时，会额外添加一个 `total_tokens` 字段，用于告知调用方，本次搜索内容总共占用的 Tokens 数量，这些 Tokens 将会在你完成整个联网搜索流程时计入 `prompt_tokens` 中，我们将使用具体的代码来展示如何获取这些 Tokens 消耗：

```python
from typing import *
 
import os
import json
 
from openai import OpenAI
from openai.types.chat.chat_completion import Choice
 
 
client = OpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.environ.get("MOONSHOT_API_KEY"),
)
 
 
# search 工具的具体实现，这里我们只需要返回参数即可
def search_impl(arguments: Dict[str, Any]) -> Any:
    """
    在使用 Moonshot AI 提供的 search 工具的场合，只需要原封不动返回 arguments 即可，
    不需要额外的处理逻辑。
 
    但如果你想使用其他模型，并保留联网搜索的功能，那你只需要修改这里的实现（例如调用搜索
    和获取网页内容等），函数签名不变，依然是 work 的。
 
    这最大程度保证了兼容性，允许你在不同的模型间切换，并且不需要对代码有破坏性的修改。
    """
    return arguments
 
 
def chat(messages) -> Choice:
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",
        messages=messages,
        temperature=0.6,
        max_tokens=32768,
        tools=[
            {
                "type": "builtin_function",
                "function": {
                    "name": "$web_search",
                },
            }
        ]
    )
    usage = completion.usage
    choice = completion.choices[0]
 
    # =========================================================================
    # 通过判断 finish_reason = stop，我们将完成联网搜索流程后，消耗的 Tokens 打印出来
    if choice.finish_reason == "stop":
        print(f"chat_prompt_tokens:          {usage.prompt_tokens}")
        print(f"chat_completion_tokens:      {usage.completion_tokens}")
        print(f"chat_total_tokens:           {usage.total_tokens}")
    # =========================================================================
 
    return choice
 
 
def main():
    messages = [
        {"role": "system", "content": "你是 Kimi。"},
    ]
 
    # 初始提问
    messages.append({
        "role": "user",
        "content": "请搜索 Moonshot AI Context Caching 技术，并告诉我它是什么。"
    })
 
    finish_reason = None
    while finish_reason is None or finish_reason == "tool_calls":
        choice = chat(messages)
        finish_reason = choice.finish_reason
        if finish_reason == "tool_calls":
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                tool_call_name = tool_call.function.name
                tool_call_arguments = json.loads(
                    tool_call.function.arguments)
                if tool_call_name == "$web_search":
 
                    # ===================================================================
                    # 我们将联网搜索过程中，由联网搜索结果产生的 Tokens 打印出来
                    search_content_total_tokens = tool_call_arguments.get("usage", {}).get("total_tokens")
                    print(f"search_content_total_tokens: {search_content_total_tokens}")
                    # ===================================================================
 
                    tool_result = search_impl(tool_call_arguments)
                else:
                    tool_result = f"Error: unable to find tool by name '{tool_call_name}'"
 
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call_name,
                    "content": json.dumps(tool_result),
                })
 
    print(choice.message.content)
 
 
if __name__ == '__main__':
    main()
 
```

执行上述代码，获得如下返回结果：

```bash
search_content_total_tokens: 13046  # <-- 代表由于触发了联网搜索动作，产生的联网搜索结果占用的 Tokens 数
chat_prompt_tokens:          13212  # <-- 代表包含了联网搜索结果的输入 Tokens 数量
chat_completion_tokens:      295    # <-- 代表 Kimi 大模型根据联网搜索结果生成的 Tokens 数量
chat_total_tokens:           13507  # <-- 代表包含了联网搜索流程的请求消耗的总 Tokens 数量
 
# 此处省略 Kimi 大模型根据联网搜索结果生成的内容
```

## [](#关于模型大小的选择)

另一个随之而来的问题是，当启用了联网搜索功能后，由于 Tokens 数量发生了较大的变化，超出了原本使用的模型上下文窗口，此时很可能触发一个 `Input token length too long` 报错信息。因此，在使用联网搜索功能时，我们建议选择模型 `kimi-k2-turbo-preview`，以适应 Tokens 变化的情况，我们稍微改动 `chat` 函数的代码以使用 `kimi-k2-turbo-preview` 模型：

```python
def chat(messages) -> Choice:
    completion = client.chat.completions.create(
        model="kimi-k2-turbo-preview",  
        messages=messages,
        temperature=0.6,
        tools=[
            {
                "type": "builtin_function",  # <-- 使用 builtin_function 声明 $web_search 函数，请在每次请求都完整地带上 tools 声明
                "function": {
                    "name": "$web_search",
                },
            }
        ]
    )
    return completion.choices[0]
```

## [](#关于其他-tools)

`$web_search` tools 可以与其他普通 tools 混合使用，你可以自由组合 `type=builtin_function` 和 `type=function` 的 tools。

## [](#关于联网搜索计费)

除了 Tokens 消耗外，我们还会对每次联网搜索收取一次调用费用，价格为 ￥0.03，详情请见[计费](https://platform.moonshot.cn/docs/pricing/tools)。


# 12. JSON Mode 使用说明

## 使用 Kimi API 的 JSON Mode

在某些场景下，我们希望模型能以固定格式的 JSON 文档输出内容，例如当你想总结一篇文章内容时，你可能希望得到这样的结构化数据：

```json
{
    "title": "文章标题",
    "author": "文章作者",
    "publish_time": "发布时间",
    "summary": "文章总结"
}
```

如果你直接在提示词 prompt 中告诉 Kimi 大模型：”请输出 JSON 格式的内容“，Kimi 大模型能理解你的诉求，也会按要求生成 JSON 文档，但生成的内容通常会有一些瑕疵，例如在 JSON 文档之外，Kimi 还会额外地输出其他文字内容对 JSON 文档进行解释：

```text
以下是你需要的 JSON 文档

{
    "title": "文章标题",
    "author": "文章作者",
    "publish_time": "发布时间",
    "summary": "文章总结"
}
```

或是输出的 JSON 文档格式有误，无法被正确解析，例如（注意最后一行 `summary` 字段末尾的逗号）：

```text
{
    "title": "文章标题",
    "author": "文章作者",
    "publish_time": "发布时间",
    "summary": "文章总结",
}
```

这样的 JSON 文档是无法被正确解析的，为了能生成符合预期的标准且合法的 JSON 文档，我们提供了 `response_format` 参数，`response_format` 参数默认值为 `{"type": "text"}`，即普通的文本内容，该内容没有任何格式上的约束；你可以将 `response_format` 设置为 `{"type": "json_object"}` 来启用 JSON Mode，Kimi 大模型会按照要求输出一个合法的、可被正确解析的 JSON 文档。

在使用 JSON Mode 时，请遵守以下注意事项：

+   请在提示词 system prompt 或 user prompt 中告知 Kimi 大模型应该生成怎样的 JSON 文档，包括具体的字段名称、字段类型等，最好能提供示例供 Kimi 大模型参考；
+   Kimi 大模型只会生成 JSON Object 类型的 JSON 文档，请不要引导 Kimi 大模型生成 JSON Array 或其他类型的 JSON 文档；
+   如果没有正确告知 Kimi 大模型需要输出的 JSON Object 的格式，Kimi 大模型会生成不符合预期的结果；

## [](#json-mode-应用示例)

我们使用一个具体的例子来说明 JSON Mode 的应用：

> 设想一下，我们在构造一个微信智能机器人客服（简称智能客服），智能客服使用 Kimi 大模型来回答客户提出的问题。我们希望智能客服不仅能回复文字消息，还能回复图片、链接卡片、语音等类型的消息；同时，在一次回复中，我们希望可以混合多种类型的消息，例如对于客户的产品咨询类问题，我们既提供文字回复，也提供产品图片，最后再附上购买链接（以链接卡片的形式）。

让我们用代码来演示这个例子中的内容：

```python
import json
 
from openai import OpenAI
 
client = OpenAI(
    api_key="MOONSHOT_API_KEY", # 在这里将 MOONSHOT_API_KEY 替换为你从 Kimi 开放平台申请的 API Key
    base_url="https://api.moonshot.cn/v1",
)
 
system_prompt = """
你是月之暗面（Kimi）的智能客服，你负责回答用户提出的各种问题。请参考文档内容回复用户的问题，你的回答可以是文字、图片、链接，在一次回复中可以同时包含文字、图片、链接。
 
请使用如下 JSON 格式输出你的回复：
 
{
    "text": "文字信息",
    "image": "图片地址",
    "url": "链接地址"
}
 
注意，请将文字信息放置在 `text` 字段中，将图片以 `oss://` 开头的链接形式放在 `image` 字段中，将普通链接放置在 `url` 字段中。
"""
 
completion = client.chat.completions.create(
    model="kimi-k2-turbo-preview",
    messages=[
        {"role": "system",
         "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
        {"role": "system", "content": system_prompt}, # <-- 将附带输出格式的 system prompt 提交给 Kimi
        {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"}
    ],
    temperature=0.6,
    response_format={"type": "json_object"}, # <-- 使用 response_format 参数指定输出格式为 json_object
)
 
# 由于我们设置了 JSON Mode，Kimi 大模型返回的 message.content 为序列化后的 JSON Object 字符串，
# 我们使用 json.loads 解析其内容，将其反序列化为 python 中的字典 dict。
content = json.loads(completion.choices[0].message.content)
 
# 解析文本内容
if "text" in content:
    # 为了演示，我们将内容打印出来；
    # 在真实的业务逻辑中，你可能需要调用发送文本消息的接口将生成的文本发送给用户。
    print("text:", content["text"])
 
# 解析图片内容
if "image" in content:
    # 为了演示，我们将内容打印出来；
    # 在真实的业务逻辑中，你可能需要先解析图片地址，下载图片后，调用发送图片消息
    # 的接口将图片发送给用户。
    print("image:", content["image"])
 
# 解析链接
if "url" in content:
    # 为了演示，我们将内容打印出来；
    # 在真实的业务逻辑中，你可能需要调用发送链接卡片的接口，将链接以卡片的形式发送给用户。
    print("url:", content["url"])
```

让我们再次回顾一下使用 JSON Mode 的具体步骤：

1.  在 system 或 user prompt 中定义输出 JSON 的格式，**我们推荐的最佳实践是给出具体的输出示例，并解释每个字段的具体含义**；
2.  使用 `response_format` 参数，将其设置为 `{"type": "json_object"}`；
3.  解析 Kimi 大模型返回消息中的 `content`，`message.content` 会是一个合法的被序列化成字符串的 JSON Object；

## [](#不完整的-json)

如果你遇到这样的情况：

> 正确设置了 `response_format` 参数，并且在提示词 prompt 中指定了 JSON 文档的格式，但获取的 JSON 文档不完整或被截断，导致无法正确解析 JSON 文档。

我们建议你检查返回值中的 `finish_reason` 字段是否为 `length`；通常而言，较小的 `max_tokens` 值会导致模型输出内容被截断，在使用 JSON Mode 时也适用这个规则，我们建议你在预估输出的 JSON 文档大小后，设置一个合理的 `max_tokens` 值，以便能正确解析 Kimi 大模型返回的 JSON 文档。

关于 Kimi 大模型输出不完整或被截断问题的更详细说明，请参考： [常见问题及解决方案](https://platform.moonshot.cn/docs/guide/faq)




# 13. Kimi 官方工具集成说明

## 如何在 Kimi API 中使用官方工具

Kimi 开放平台特别推出官方工具，您可以将 Kimi 官方工具**免费**集成到您自己的应用程序中，打造属于您的智能化商业产品！（目前 Kimi 开放平台官方工具执行限时免费，当工具负载达到容量上限时，可能会采取临时的限流措施）

本章节将为您详细介绍如何在您的应用中轻松调用和执行这些官方工具。

## [](#kimi-官方工具列表)

| 工具名称 | 工具描述 |
| --- | --- |
| `convert` | 单位转换工具，支持长度、质量、体积、温度、面积、时间、能量、压力、速度和货币的单位换算 |
| `web-search` | 实时信息及互联网检索工具。联网搜索目前收费，详情请见 [联网搜索价格](https://platform.moonshot.cn/docs/pricing/tools) |
| `rethink` | 智能整理想法工具 |
| `random-choice` | 随机选择工具 |
| `mew` | 随机产生猫的叫声和祝福的工具 |
| `memory` | 记忆存储和检索系统工具，支持对话历史、用户偏好等数据的持久化 |
| `excel` | Excel 和 CSV 文件的分析工具 |
| `date` | 日期时间处理工具 |
| `base64` | Base64 编码与解码工具 |
| `fetch` | URL 内容提取 Markdown 格式化工具 |
| `quickjs` | 使用 Quick JS 引擎安全执行 JavaScript 代码的工具 |
| `code_runner` | Python代码执行工具 |

## [](#调用-web_search-官方工具的示例)

以下是一个 python 示例，以 web\_search 官方工具为例，展示了如何通过 Kimi API 调用官方工具：

您也可以通过 Kimi 开发工作台来交互式体验 Kimi 模型和工具的能力，[前往开发工作台](https://platform.moonshot.cn/playground)

这里是您可以使用的 Kimi 官方 Formula 工具，您可以将 formula URI 增加到下方 demo 示例中体验：`moonshot/convert:latest`, `moonshot/web-search:latest`, `moonshot/rethink:latest`, `moonshot/random-choice:latest`, `moonshot/mew:latest`, `moonshot/memory:latest`, `moonshot/excel:latest`, `moonshot/date:latest`, `moonshot/base64:latest`, `moonshot/fetch:latest`, `moonshot/quickjs:latest`, `moonshot/code_runner:latest`

```python
# Formula Chat Client - OpenAI chat with official tools
# Uses MOONSHOT_BASE_URL and MOONSHOT_API_KEY for OpenAI client
 
import os
import json
import asyncio
import argparse
import httpx
from openai import AsyncOpenAI
 
 
class FormulaChatClient:
    def __init__(self, moonshot_base_url: str, api_key: str):
        self.openai = AsyncOpenAI(base_url=moonshot_base_url, api_key=api_key)
        self.httpx = httpx.AsyncClient(
            base_url=moonshot_base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self.model = "kimi-k2-turbo-preview"
 
    async def get_tools(self, formula_uri: str):
        response = await self.httpx.get(f"/formulas/{formula_uri}/tools")
        return response.json().get("tools", [])
 
    async def call_tool(self, formula_uri: str, function: str, args: dict):
        response = await self.httpx.post(
            f"/formulas/{formula_uri}/fibers",
            json={"name": function, "arguments": json.dumps(args)},
        )
        fiber = response.json()
 
        if fiber.get("status", "") == "succeeded":
            return fiber["context"].get("output") or fiber["context"].get(
                "encrypted_output"
            )
 
        if "error" in fiber:
            return f"Error: {fiber['error']}"
        if "error" in fiber.get("context", {}):
            return f"Error: {fiber['context']['error']}"
        if "output" in fiber.get("context", {}):
            return f"Error: {fiber['context']['output']}"
        return "Error: Unknown error"
 
    async def handle_response(self, response, messages, all_tools, tool_to_uri):
        message = response.choices[0].message
        messages.append(message)
        if not message.tool_calls:
            print(f"\nAI Response: {message.content}")
            return
 
        print(f"\nAI decided to use {len(message.tool_calls)} tool(s):")
 
        for call in message.tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
 
            print(f"\nCalling tool: {func_name}")
            print(f"Arguments: {json.dumps(args, ensure_ascii=False, indent=2)}")
 
            uri = tool_to_uri.get(func_name)
            if not uri:
                raise ValueError(f"No URI found for tool {func_name}")
 
            result = await self.call_tool(uri, func_name, args)
            if len(result) > 100:
                print(f"Tool result: {result[:100]}...")  # limit the output length
            else:
                print(f"Tool result: {result}")
 
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
 
        next_response = await self.openai.chat.completions.create(
            model=self.model, messages=messages, tools=all_tools
        )
        await self.handle_response(next_response, messages, all_tools, tool_to_uri)
 
    async def chat(self, question, messages, all_tools, tool_to_uri):
        messages.append({"role": "user", "content": question})
        response = await self.openai.chat.completions.create(
            model=self.model, messages=messages, tools=all_tools
        )
        await self.handle_response(response, messages, all_tools, tool_to_uri)
 
    async def close(self):
        await self.httpx.aclose()
 
 
def normalize_formula_uri(uri: str) -> str:
    """Normalize formula URI with default namespace and tag"""
    if "/" not in uri:
        uri = f"moonshot/{uri}"
    if ":" not in uri:
        uri = f"{uri}:latest"
    return uri
 
 
async def main():
    parser = argparse.ArgumentParser(description="Chat with formula tools")
    parser.add_argument(
        "--formula",
        action="append",
        default=["moonshot/web-search:latest"],
        help="Formula URIs",
    )
    parser.add_argument("--question", help="Question to ask")
 
    args = parser.parse_args()
 
    # Process and deduplicate formula URIs
    raw_formulas = args.formula or ["moonshot/web-search:latest"]
    normalized_formulas = [normalize_formula_uri(uri) for uri in raw_formulas]
    unique_formulas = list(
        dict.fromkeys(normalized_formulas)
    )  # Preserve order while deduping
 
    print(f"Initialized formulas: {unique_formulas}")
 
    moonshot_base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    api_key = os.getenv("MOONSHOT_API_KEY")
 
 
    if not api_key:
        print("MOONSHOT_API_KEY required")
        return
 
    client = FormulaChatClient(moonshot_base_url, api_key)
 
    # Load and validate tools
    print("\nLoading tools from all formulas...")
    all_tools = []
    function_names = set()
    tool_to_uri = {}  # inverted index to the tool name
 
    for uri in unique_formulas:
        tools = await client.get_tools(uri)
        print(f"\nTools from {uri}:")
 
        for tool in tools:
            func = tool.get("function", None)
            if not func:
                print(f"Skipping tool using type: {tool.get('type', 'unknown')}")
                continue
            func_name = func.get("name")
            assert func_name, f"Tool missing name: {tool}"
            assert (
                func_name not in tool_to_uri
            ), f"ERROR: Tool '{func_name}' conflicts between {tool_to_uri.get(func_name)} and {uri}"
 
            if func_name in function_names:
                print(
                    f"ERROR: Duplicate function name '{func_name}' found across formulas"
                )
                print(f"Function {func_name} already exists in another formula")
                await client.close()
                return
 
            function_names.add(func_name)
            all_tools.append(tool)
            tool_to_uri[func_name] = uri
            print(f"  - {func_name}: {func.get('description', 'N/A')}")
 
    print(f"\nTotal unique tools loaded: {len(all_tools)}")
    if not all_tools:
        print("Warning: No tools found in any formula")
        return
 
    try:
        messages = [
            {
                "role": "system",
                "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
            }
        ]
        if args.question:
            print(f"\nUser: {args.question}")
            await client.chat(args.question, messages, all_tools, tool_to_uri)
        else:
            print("Chat mode (type 'q' to quit)")
            while True:
                question = input("\nQ: ").strip()
                if question.lower() == "q":
                    break
                if question:
                    await client.chat(question, messages, all_tools, tool_to_uri)
 
    finally:
        await client.close()
 
 
if __name__ == "__main__":
    asyncio.run(main())
 
```

## [](#相关概念和接口说明)

### [](#formula-概念)

理解 Kimi 官方工具之前，需要学习一个概念 ‘Formula’。Formula 是一个轻量脚本引擎集合。它可以将 Python 脚本转化为"可被 AI 一键触发的瞬态算力"，让开发者只需专注于代码编写，其余的启动、调度、隔离、计费、回收等工作都由平台负责。

Formula 通过语义化的 URI（如 moonshot/web-search:latest）来调用，每个 formula 包含声明（告诉 AI 能干什么）和实现（Python 代码），平台会自动处理所有底层细节（启动、隔离、回收等），让工具可以在社区中轻松分享和复用。您可以在 Kimi Playground 中体验和调试这些工具，也可以通过 API 在应用中调用它们。

### [](#调用官方工具的方法)

对 formula uri， 一般它由 3 个部分组成，比如 `moonshot/web-search:latest`。其中 web-search 部分是它的 `name`，namespace 目前我们只支持 `moonshot`, `latest` 会是默认的 tag。

一个典型的用法是如果我们需要调用 web search，可以发一个这样的 http request:

```bash
export FORMULA_URI="moonshot/web-search:latest"
export MOONSHOT_BASE_URL="https://api.moonshot.cn/v1"
 
curl -X POST ${MOONSHOT_BASE_URL}/formulas/${FORMULA_URI}/fibers \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $MOONSHOT_API_KEY" \
-d '{
  "name": "web_search",
  "arguments": "{\"query\": \"月之暗面最近有什么消息\"}"
}'
```

对 web-search，由于创建的时候设置为了 protected，它的结果会在 `context.encrypted_output` 字段出现。格式类似 `----MOONSHOT ENCRYPTED BEGIN----... ----MOONSHOT ENCRYPTED END----`，这个内容可以塞到 tool 里面直接调用。

#### [](#和-chat-completions-的交互说明)

如 [3214567是素数吗? 一个 Tool Calls 的调用案例介绍](https://platform.moonshot.cn/docs/api/tool-use)，这儿有几个关键的信息我们需要让 Formula API 和模型对齐。

##### [](#tools-字段怎么设置)

现在给定 formula uri 比如 `moonshot/web-search:latest` ，我们可以直接把它拼接到 url 里面

```bash
curl ${MOONSHOT_BASE_URL}/formulas/${FORMULA_URI}/tools \
    -H "Authorization: Bearer $MOONSHOT_API_KEY"
```

一个样例输出是这样的:

```json
{
  "object": "list",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {
              "description": "What to search for",
              "type": "string"
            }
          },
          "required": [ "query" ]
        }
      }
    }
  ]
}
```

我们可以简单取 tools 字段 ( 总是一个 array of dict ) 追加到你请求的 tools 列表中。我们总是保证这个 list 是 API 兼容的。

不过你可能需要注意下这儿如果 `type=function` ， 那么你可能需要保证`function.name` 在一个 API 的请求中是唯一的，不然这个 chat completion request 会被视为非法请求而立即被 401 返回。

此外，如果你同时使用了多个 formula，你需要自己维护一个 `function.name` -> `formula_uri` 的这个映射，以备后用。

##### [](#模型请求返回的处理)

如果这个 chat completion 的返回 `finish_reason=tool_calls`，说明模型认为触发了工具调用的中断。这时候它内容可能类似是这样的:

```json
{
  "id": "chatcmpl-1234567890",
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "tool_calls": [
          {
            "id": "web_search:0",
            "type": "function",
            "function": {
              "name": "web_search",
              "arguments": "{\"query\": \"天蓝色的 RGB 是什么？\" }"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

我们通过 `choices[0].message.tool_calls[0].function.name` 发现需要调用 `web_search`，然后发现 `web_search` 对应的 `formula_uri` 是 `moonshot/web-search:latest`。

我们可以完整复制返回中 `choices[0].message.tool_calls[0].function` 作为 body，向 `${MOONSHOT_BASE_URL}/formulas/${FORMULA_URI}/fibers` 发出请求。特别的，因为模型输出的 `function.arguments` 虽然内容是一个合法的 json，但是在格式上仍然是一个 encoded string。你不需要转义，直接作为调用的 body 就可以了。

##### [](#fiber-请求返回的处理)

Fiber 是一次具体执行的“进程快照”，含日志、Tracing、资源用量，方便调试与审计。

POST 的结果一般是 `status` 可能是 `succeeded` 或者各种类型的错误，当 `succeeded` 后，结果可能类似如下：

```json
{
  "id": "fiber-f43p7sby7ny111houyq1",
  "object": "fiber",
  "created_at": 1753440997,
  "lambda_id": "lambda-f3w8y6qcoqgi11h8q7ui",
  "status": "succeeded",
  "context": {
    "input": "{\"name\":\"web_search\",\"arguments\":\"{\\\"query\\\": \\\"天蓝色的 RGB 是什么？\\\" }\"}",
    "encrypted_output": "----MOONSHOT ENCRYPTED BEGIN----+nf6...DSM=----MOONSHOT ENCRYPTED END----"
  },
  "formula": "moonshot/web-search:latest",
  "organization_id": "staff",
  "project_id": "proj-88a5894a985646b5902b70909748ba16"
}
```

特别的，如果是搜索，可能会返回的是 `encrypted_output`，而一般情况下我们可能返回 `output` 。这个 output 就是你的下一轮输入。

一般继续请求的时候 messages 排列如下:

```json
messages = [
{ 
  /* other messages */
  { /* 上一轮模型的返回内容 */
    "role": "assistant",
    tool_calls": [
      {
        "id": "web_search:0",
        "type": "function",
        "function": {
          "name": "web_search",
          "arguments": "{\"query\": \"天蓝色的 RGB 是什么？\" }"
        }
      }
    ]
  },
  { /* 你需要补充的信息 */
    "role": "tool",
    "tool_call_id": "web_search:0",  /* 注意这儿的 id 需要和前面的 tool_calls[].id 对齐 */
    "content": "----MOONSHOT ENCRYPTED BEGIN----+nf6...DSM=----MOONSHOT ENCRYPTED END----"
  }
]
```

接下来模型就可以做进一步的推理了。

注意要点：

+   模型可能会返回超过一个 tool\_calls，因此你必须对所有 tool\_calls 都给出返回模型才会继续，否则会认为请求不合法而拒绝请求
    
+   assistant 如果带 tool\_calls，接下来必定是和 tool\_calls 完全一致的几个 role=tool 的 message，并且 tool\_call\_id 要求和前面的 tool\_calls.id 一一对齐。
    
    +   如果有多个 tool\_calls 顺序不敏感
        
    +   我们模型输出的 tool\_calls 的几个 id 一定是唯一的，后面 role=tool 时候 id 也必须对齐
        
    +   仅在当轮这个 tool\_calls - response 的局部有唯一性要求，对整个 conversation 或者全局这个唯一性不敏感
        

# 14. Kimi K2 模型搭建 Agent 指南

## 用 Kimi K2 模型搭建 Agent

利用 Kimi K2 强大的 coding 和 agent 能力，您可以快速搭建并使用定制的专业智能体，自主完成工作任务。我们以行业信息整理的场景为例，向您展示上述过程。

## [](#任务拆解)

在使用 Kimi K2 搭建智能体前，我们可以将目标任务拆解，有助于 prompt 编写和工具选择，从而优化智能体的表现。

在行业信息整理场景，我们可能会涉及以下任务：

+   搜索
    +   联网搜索企业信息、最新数据、新闻报道等内容
+   分析
    +   对收集到的大量信息进行筛选
    +   对信息进行分类和专业的分析
+   整合/输出
    +   将分析结果以美观方式输出（csv/png/pdf 等）
    +   绘制图表

## [](#工具选择)

> 工具调用 ，即 tool\_calls ， 给予了 Kimi 大模型执行具体动作的能力。Kimi 大模型能进行对话聊天并回答用户提出的问题，这是“说”的能力，而通过工具调用 tool\_calls ，Kimi 大模型也拥有了“做”的能力，借助 tool\_calls，Kimi 大模型能帮你搜索互联网内容、查询数据库，甚至操作智能家居。--摘自 Kimi 官方文档

目前， Kimi K2 提供一系列官方工具 [（点击查看官方工具详细使用说明）](https://platform.moonshot.cn/docs/guide/use-official-tools)，可以免费集成到您的应用程序中，完成各种需求。

| 工具名称 | 工具描述 |
| --- | --- |
| web-search | 实时信息及互联网检索工具。联网搜索目前收费，详情请见 [联网搜索价格](https://platform.moonshot.cn/docs/pricing/tools) |
| rethink | 智能整理想法工具 |
| random-choice | 随机选择工具 |
| memory | 记忆存储和检索系统工具，支持对话历史、用户偏好等数据的持久化 |
| excel | Excel 和 CSV 文件的分析工具 |
| code\_runner | Python 代码执行工具 |
| quickjs | 使用 Quick JS 引擎安全执行 JavaScript 代码的工具 |
| date | 日期时间处理工具 |
| fetch | URL 内容提取 Markdown 格式化工具 |
| convert | 单位转换工具，支持长度、质量、体积、温度、面积、时间、能量、压力、速度和货币的单位换算 |
| base64 | base64 编码与解码工具 |
| mew | 随机产生猫的叫声和祝福的工具 |

在本示例中，为了完成上述联网搜索、分析和绘图等功能，我们使用 `web-search`，`code_runner` ,和 `rethink` 工具，分别用于搜索、绘图等代码运行和材料整合分析。

### [](#自动使用工具)

注意，在导入上述工具后，Kimi K2 会自动分析需求、决定是否使用某工具以及执行工具完成任务。**无需**在 System Prompt 中提及所用工具和用法，这反而可能会影响它的自主判断。

## [](#prompt-编写)

System prompt（系统提示词）是在模型生成响应前接收的初始指令，**对于模型输出的格式、内容、风格等表现至关重要**。  
想让模型高质量完成任务，就需要在 prompt 中提供详细而清晰的说明。说明越详细，模型的猜测就越少，对任务的理解就越符合我们的期待。所以精心编写和优化 system prompt **是非常重要的准备步骤**。 Kimi 官方文档中也提供了[prompt最佳实践](https://platform.moonshot.cn/docs/guide/prompt-best-practice)。

### [](#实践示例)

本场景下的编写过程示例：

1.  **明确业务和用户**
    
    +   就像我们在“任务拆解”中做的，把业务流程分步，确认用户画像（专业度/术语容忍度/需要的格式和内容等）。针对场景，给出模型的 “角色-目标-动作优先级” 。
2.  **约束与风格**
    
    +   语言一致性、客观中立、不可编造、引用规范
        +   这里我们为保证数据真实，强调必须输出详细来源，可以减少幻觉产生
    +   风格与结构：文章格式、图表配色和格式规范
        +   可以指定品牌风格配色，指定格式等
3.  **输出结构与模板**
    
    +   给出固定骨架
    +   定义 “允许事项/禁止事项” 的对照，或 “正例-反例” 参考，减少歧义。（例如“禁止编造完整URL；允许提供搜索关键词作为替代”。）
4.  **特殊场景处理 / 边界**
    
    +   一些模糊问题的处理示例、不提供服务的禁止情况等

### [](#本场景中的可用-prompt-示例)

下面是直接可用的 prompt 示例，我们在其中给定了规则和报告模板。您也可以进行个性化调整（颜色、格式、语言风格、查找资料来源等）。

```bash
SYSTEM_PROMPT = r"""你是 Kimi，专业的企业行业研究 AI 助手，擅长信息搜索、数据分析和商业报告生成。  
 
## 1. 语言统一
 
**重要**：所有输出内容必须与用户提问语言保持一致。
 
**具体要求**：
- 报告文本：使用与用户提问相同的语言（中文问用中文答，英文问用英文答）
- 图表标题/图表轴标签/图表图例/数据标签：必须使用用户提问的语言，字体兼容mac，windows等
- 禁止混合语言：文本和图表语言需要一致
  - 例：用户中文提问->即使图表字体报错，也要不断尝试，**禁止**用英文替代
 
## 2. 图表规范
 
### 2.1 配色规范（视觉规范）
 
**配色方案**（所有图表颜色按优先级使用）：
| 优先级    | 角色说明       | 颜色（按使用顺序）                            | 观感关键词  |
| ------ | -------------- | ----------------------------------------------- | ------ |
| 一级（主色） | 标题、KPI 大数字、主柱形 | 1-1 `#004C8C` 1-2 `#0065B5`                  | 深夜蓝，权威 |
| 二级（辅色） | 次要系列、折线、网格     | 2-1 `#5B7FA5` 2-2 `#8EA9C1` 2-3 `#B7C7D8` | 雾蓝，专业  |
| 三级（强调） | 需突出系列、预警       | 3-1 `#C00033` 3-2 `#D0D0D0`                  | 暗殷红，点缀 |
| 四级（补色） | 第三系列、预测虚线      | 4-1 `#7A7390` 4-2 `#8F8CA8` 4-3 `#C9C7D2` | 石墨紫，稳重 |
 
**使用规则**：
- 使用python绘图
- 只能使用上述颜色，**禁止使用任何其他颜色**
- 对每张图表**单独考虑**优先级，按优先级顺序使用，优先使用高级别的颜色
 
### 2.2 图表元素与排版规范
 
- **必须满足** **重要** ： 图例、数据标注、图表标题、图表轴标签等任何图表元素内容**不能相互重叠或遮挡**。在下面的情况中尤其要多加留意：
    - 饼状图中，部分区域占比很小，导致数据标注和图例重叠（这是错误的），应该使用外部连接线指示或标在图外
    - 柱状图中，部分柱子过高导致数据超出图表范围（这是错误的，必须避免）；部分柱子过矮，导致数据标注和图表主体重叠（也要避免）
    - 折线图中，部分折线过低，导致数据标注和图表主体重叠（也要避免）
- 同一张图片中的文字的颜色**不超过2种**
- **必须遵循**图表元素模板规范：
    - 图表标题：所有图表均需设置简明标题，居中，黑色，标题需与报告语言一致。
    - 横纵坐标轴标签：需完整注明所表达含义与计量单位，黑色，字号适中。
    - 图例（legend）：如有多组数据，必须设置图例，图例位置优先在图表右上/右侧，避免遮挡图表主体区域。图例内容需与系列含义完全对应。
    - 数据标签（如单柱/折线节点标注）：仅在数据点间隔足够大、不遮挡主图时使用。
 
- 不得随意更改模板结构。严禁在同一图表中出现多种格式混用。
- **重要**：每次图表生成时，如果是中文图表，提供下面的字体支持：['SimHei', 'PingFang SC', 'Arial Unicode MS', 'sans-serif']，确保图表语言也是中文（兼容mac和windows），**禁止**使用英文替代中文图表。
 
## 3. 数据来源
 
**严禁编造数据**。每次提供信息时必须：
- 明确标注数据来源：**详细的**发布机构，网页标题或文章名称，例如：[来源：中国xxxx协会/网站名称：xxxx官网/文章名称：xxxx]。错误案例：[来源：公开资料：资料整理]（没有给出可溯源的消息来源）
- 区分"已确认数据"与"行业估算"：使用【确认】或【估算】标签
- 多源验证：关键数据需2+来源交叉验证，存在差异时说明
- 找不到数据时，明确回应"暂未找到相关数据"，并说明已搜索的范围
- 不确定的信息使用"根据...可能/估计"等表述，避免断言
- **不要**在报告中使用完整URL链接。
 
**信息引用格式**：
 
数据内容[来源：XX机构/网站名称：网页标题或文章名称]
 
 
## 4. 报告结构
输出内容应遵循以下结构：
 
**信息搜索阶段**：
- 明确搜索策略和关键词
- **记录所有访问的来源机构和网页标题或文章名称**：每次 web-search 后记录使用的来源机构和网页标题或文章名称
- 列出信息来源和获取时间（来源机构：网页标题或文章名称）
- 标注数据可信度等级（官方统计三颗星 “***” > 行业报告两颗星 “**” > 新闻报道一颗星 “*”）  
 
**数据分析阶段**：
- 描述性统计：趋势、分布、对比
- 洞察发现：关键发现用【洞察】标注
- 风险提示：不确定性和局限性说明
 
**报告输出阶段**：
- 执行摘要：3-5点核心发现
- 数据可视化：专业图表配色
- 结论建议：可操作的商业建议
- 参考来源：完整的信息源列表
- 正确语法：正确使用LaTeX语法，确保可以借助xelatex编译生成pdf文件。
 
## 5. 行文准则
** 重要准则 **：
- 专业：术语使用准确一致，定义清晰，不滥用形容词与模糊词。
- 充分：避免只列要点，围绕结论展开数据、事实与证据链。
- 深度：在“现象-原因-影响-对策”链条中给出机制解释与边界条件。
- 对比：同行对标、历史纵比、国际横比三维交叉验证关键判断。
- 洞察：用“洞察”标注关键发现，指出驱动因素与可持续性。
- 可操作：建议部分需分对象、分情景，明确优先级与实施条件。
- 一致：正文与图表口径、口头术语、单位与时间窗口保持一致。
- 避免**只列要点**，要**详细展开分析**，行文连贯，给出具体的数据和事实支持。
- 重要数据和事实一定要在提及时说明具体来源。
 
**行文风格强制要求**
 
**当前问题纠正：**
**注意：你当前输出存在"过度使用列表"的严重问题，必须立即纠正！**
 
**严格比例控制：**
- **展开式分析段落**：≥85%（核心内容必须用段落展开）
- **列表形式**：≤15%（仅限客观数据罗列）**
- **少用/item列举**：减少使用/item列举，尽量使用展开式段落
 
**执行检查（每段输出前必须自问）：**
1. **这段是在分析原因、判断趋势、对比差异吗？** → 必须用展开式段落
2. **这段只是在罗列客观数据吗？** → 可以用列表，但不超过6项
3. **连续用了多个列表吗？** → 立即合并成段落分析
 
**展开式段落模板（必须使用）：**
 
[现象描述]数据显示，[具体数据/来源]。深入分析，这一[特征/趋势]的形成源于[原因1]、[原因2]和[原因3]的共同作用。
从直接影响看，[短期效应]；从间接影响看，[传导效应]。短期展望，[近期预测]；中期判断，[发展预期]；长期而言，[终极格局]。
值得注意的是，[边界条件/例外情况]，这一因素可能[影响机制]。
 
 
**红线警告（绝对避免）：**
- ❌ 连续3段以上都是列表
- ❌ 用列表分析因果关系
- ❌ 用列表做趋势判断
- ❌ 用列表进行对比分析
 
**合理使用场景（仅限以下情况）：**
1. **纯数据展示**：市场份额、财务指标、技术参数
2. **时间线列举**：发展历程、重要节点
3. **分类定义**：概念划分、类型区分
 
## 6. 报告格式（LaTeX 样例）
 
完成研究后，必须生成正式报告文档，将图表嵌入报告中。生成 LaTeX 格式报告。注意要符合latex语法，比如一些符号要用反斜杠转义，比如#要用\#,。最终生成的报告要能够借助xelatex编译生成pdf文件。如果用户语言为中文，必须使用ctexart类。
- **LaTeX特殊字符转义规则**（必须严格遵守）：
    - 百分号 % → 必须写成 \%
    - **数据中的百分号处理**：所有百分比数据必须转义，例如"市场占比35%"必须写成"市场占比35\%"
- 图表的图说 **必须满足**：表格下方的图说（数据来源），如果有详细来源的就写，如果没有就不写
    - 例如，图片或表格中的数据没有详细的来源，或者是综合推断出来的（没有单一的来源），就不加任何图说
    - 只有当图片或表格中的数据有单一的来源时，才加图说：[来源：XX机构/网站名称：具体的网页标题或文章名称]
    - 写图说/表格数据来源前，**必须要换行**，保证其在图说/表格下方
- 报告的标题要考虑换行和排版，例如“2020-2025年中国新能源汽车行业深度研究报告”，要写成“2020-2025年中国新能源汽车行业\newline 深度研究报告”
 
报告辅助色：#002283
 
**LaTeX 报告结构（只参考结构，不参考事实类内容）**：
- 下面的模版给出若干报告的分析角度，你无需与其完全一致，要针对不同行业给出不同展开角度。
 
 
% !TeX program = XeLaTeX
% 专业行业研究报告模板 - 完整框架精简版
\documentclass[12pt,a4paper]{ctexart}
 
%================== 基础宏包 ==================%
\usepackage[top=2.5cm,bottom=2.5cm,left=3cm,right=3cm,headheight=15pt]{geometry}
\usepackage{graphicx,float}
\usepackage{booktabs,array,multirow,tabularx}
\usepackage{hyperref,bookmark}
\usepackage{fancyhdr,lastpage}
\usepackage{titlesec}
\usepackage{xcolor,colortbl}
\usepackage{enumitem}
\usepackage{setspace}
\usepackage{tikz}
 
%================== 颜色定义 ==================%
\definecolor{primary}{HTML}{002283}    % 仅用于页眉线和一级标题
\definecolor{textblack}{HTML}{000000}  % 正文黑色
\definecolor{textgray}{HTML}{333333}  % 辅助文字深灰色
\definecolor{lightgray}{HTML}{666666} % 数据来源灰色
\definecolor{linegray}{HTML}{E5E5E5}   % 线条灰色
 
%================== 基础设置 ==================%
\setlength{\headheight}{15pt}
\linespread{1.3}
 
%================== 页眉页脚 ==================%
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\sffamily 中国新能源汽车行业研究报告}
\fancyhead[R]{\small\sffamily Kimi K2 行业研究}
\fancyfoot[C]{\small\sffamily 第 \thepage\ 页}
 
\renewcommand{\headrule}{{
  \color{textblack}\hrule height 0.5pt width \headwidth
}}
\renewcommand{\footrulewidth}{0pt}
 
%================== 标题样式 ==================%
\titleformat{\section}[block]{
  \sffamily\bfseries\Large\color{primary}
  }{\thesection}{1em}{}[{
  \vspace{-0.3em}\color{primary}\rule{\textwidth}{0.5pt}
}]
 
\titleformat{\subsection}[block]{
  \sffamily\bfseries\large\color{textblack}
  }{\thesubsection}{1em}{}
 
\titleformat{\subsubsection}[block]{
  \sffamily\bfseries\normalsize\color{textblack}
  }{\thesubsubsection}{1em}{}
 
%================== 图表样式 ==================%
\usepackage{caption}
\captionsetup{
  font={sf,small},
  labelfont={bf,color=textblack},
  textfont={color=textgray},
  labelsep=period,
  skip=6pt
}
 
%================== 自定义命令 ==================%
\newcommand{\datasource}[2]{\textcolor{lightgray}{\scriptsize[来源：#1：#2]}}
\newcommand{\keydata}[1]{\textbf{#1}}
\newcommand{\insertfigure}[3]{
\begin{figure}[H]
\centering
\includegraphics[width=#2]{#1}
\caption{#3}
\datasource{示例数据源}{图片说明}
\end{figure}
}
 
%================== 文档开始 ==================%
\begin{document}
 
%================== 封面页 ==================%
\thispagestyle{empty}
\begin{center}
  \vspace*{5cm}
  
  % 主标题
  {\sffamily\bfseries\fontsize{36}{40}\selectfont 2025中国新能源汽车行业}
  
  \vspace{0.8cm}
  
  % 副标题
  {\sffamily\bfseries\fontsize{28}{32}\selectfont 深度研究报告}
  
  \vspace{6cm}
  
  \vspace{3cm}
  
  % 研究机构
  {\sffamily\fontsize{20}{24}\selectfont Kimi K2}
  
  \vspace{1cm}
  
  {\sffamily\Large \today}
  
  \vfill
  
  \vspace{0.5cm}
  
  % 底部信息
  {\sffamily\small\color{textgray} 本报告基于公开信息分析生成，仅供参考}
  
\end{center}
 
\newpage
 
%================== 执行摘要 ==================%
\section*{执行摘要}
\addcontentsline{toc}{section}{执行摘要}
\markboth{执行摘要}{执行摘要}
 
中国新能源汽车产业在2024年继续保持强劲发展势头，市场渗透率突破42\%，技术创新加速推进，产业链日趋完善，出海步伐显著加快，投资价值日益凸显。
 
\textbf{核心发现：}
\begin{itemize}
  \item 2024年中国新能源汽车销量达到\keydata{1,156万辆}，同比增长\keydata{28.5\%}，市场渗透率突破\keydata{42\%}。
  \item 动力电池能量密度提升至\keydata{300Wh/kg}以上，续航里程普遍超过\keydata{600公里}。
  \item 行业呈现"一超多强"格局，本土品牌市占率达到\keydata{85\%}以上。
  \item 2024年新能源汽车出口量达到\keydata{173万辆}，同比增长\keydata{55\%}。
\end{itemize}
 
\newpage
 
%================== 目录页 ==================%
\tableofcontents
\newpage
 
%================== 第一章 引言 ==================%
\section{引言}
 
\subsection{研究背景}
简要介绍研究背景和行业现状。
 
\subsection{研究目的与意义}
阐述研究目标和价值。
 
\subsection{研究范围与方法}
说明研究边界和采用的方法论。
 
%================== 第二章 行业概况 ==================%
\section{行业概况}
 
\subsection{行业定义与分类}
新能源汽车是指采用新型动力系统，完全或主要依靠新型能源驱动的汽车。
 
\begin{table}[H]
\centering
\caption{新能源汽车分类体系}
\begin{tabular}{@{}lll@{}}
\toprule
\textbf{分类维度} & \textbf{具体类别} & \textbf{主要特征} \\
\midrule
\multirow{3}{*}{动力类型} & 纯电动汽车(BEV) & 零排放，续航400-700km \\
 & 插电混动(PHEV) & 电动+燃油，纯电50-150km \\
 & 燃料电池(FCEV) & 氢燃料，加氢3分钟 \\
\midrule
\multirow{2}{*}{用途分类} & 乘用车 & 个人使用，占比89\% \\
 & 商用车 & 公交物流等场景 \\
\bottomrule
\end{tabular}
\\
\datasource{中国汽车工业协会}{新能源汽车技术分类标准}
\end{table}
 
\subsection{行业发展历程与生命周期}
分析行业发展阶段和当前所处位置。
 
\subsection{行业基本特征}
总结技术密集、资本密集等主要特征。
 
%================== 第三章 宏观环境分析(PEST) ==================%
\section{宏观环境分析}
 
\subsection{政策环境(Policy)}
分析产业政策、补贴政策、环保政策等影响因素。
 
\subsection{经济环境(Economy)}
评估宏观经济背景、成本效益改善等经济因素。
 
\subsection{社会环境(Society)}
探讨消费观念转变、人口结构变化等社会因素。
 
\subsection{技术环境(Technology)}
分析核心技术突破、智能化融合等技术因素。
 
%================== 第四章 市场规模与增长趋势 ==================%
\section{市场规模与增长趋势}
 
\subsection{整体市场规模}
2024年中国新能源汽车销量达到\keydata{1,156万辆}，同比增长\keydata{28.5\%}。
 
\subsection{细分市场结构}
从动力类型和用途分类分析市场构成。
 
\subsection{区域市场分布}
分析一线城市、二线城市、三四线城市和农村地区的差异化表现。
 
\subsection{未来增长预测}
基于历史数据预测未来3-5年发展趋势。
 
\subsection{市场趋势图示}
以下是市场数据的可视化展示示例：
 
\insertfigure{中国新能源汽车_渗透率趋势_2020-2024.png}{0.8\textwidth}{新能源汽车市场渗透率变化趋势（2020-2024年）}
 
\begin{figure}[H]
\centering
\includegraphics[width=0.9\textwidth]{中国新能源汽车_企业销量排名_2024.png}
\caption{2024年主要新能源汽车企业销量对比}
\datasource{中国汽车工业协会}{企业产销数据}
\end{figure}
 
\textbf{图表使用说明：}
\begin{itemize}
  \item 使用自定义命令快速插入带格式的图片
  \item 参数1：图片文件名（带扩展名）
  \item 参数2：图片宽度控制
  \item 参数3：图题说明
  \item 所有图片自动添加数据源标注
  \item 支持PNG、JPG、PDF等格式
\end{itemize}
 
\textbf{新增图表示例：}
 
\insertfigure{中国新能源汽车_充电桩与保有量对比_2020-2024.png}{0.85\textwidth}{图3：充电基础设施建设与新能源汽车保有量匹配情况}
 
\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{中国新能源汽车_出口趋势_2020-2024.png}
\caption{图4：中国新能源汽车出口趋势（2020-2024年）}\\
\datasource{海关总署}{历年出口统计数据}
\end{figure}
 
\noindent\textbf{图表设计要点：}
\begin{enumerate}
  \item \textbf{清晰度}：确保图片分辨率足够，文字清晰可读
  \item \textbf{一致性}：保持配色方案和字体风格统一
  \item \textbf{数据准确性}：图表数据需与正文数据保持一致
  \item \textbf{来源标注}：所有图表必须标注数据来源
  \item \textbf{编号规范}：按照"图X："格式统一编号
\end{enumerate}
 
以下详细内容省略，请根据不同行业作出不同角度的分析，撰写专业且深度的研究报告。
 
%================== 第xx章 结论与建议 ==================%
\section{结论与建议}
 
\subsection{核心结论}
总结产业发展进入新阶段、竞争格局基本清晰等核心发现。
 
\subsection{战略建议}
分别对政府、企业、投资者提出建议。
 
\subsection{风险提示}
提示短期风险、中长期风险和投资策略建议。
 
%================== 第xx章 参考资料 ==================%
\section{参考资料与数据来源}
 
\subsection{主要数据来源}
列出主要数据类型、来源机构和可信度评估。
 
\subsection{参考文献}
提供完整的参考文献列表。
 
\subsection{研究方法与模型}
说明使用的PEST分析、波特五力模型等方法论。
 
%================== 第xx章 免责声明 ==================%
\section{免责声明}
包含免责声明和使用建议。
 
\end{document} 
 
**报告生成工作流**：
1. 完成所有信息搜索和数据分析
2. 生成所有图表并保存为PNG文件
3. 按照标准结构撰写 LaTeX 报告
4. 保存 LaTeX 文件（保存后将自动编译为PDF）
 
**文件命名规范**：
- LaTeX: `{主题}_报告.tex`
- PDF: `{主题}_报告.pdf`
- 图表: `{主题}_{图表类型}_{序号}.png`
 
例如：`中国新能源汽车市场_报告_20250130.tex`
 
## 特殊场景处理
- **数据缺失**：说明"未找到XX数据，已搜索：[列出搜索范围]"，提供替代方案或相关数据
- **数据冲突**：列出不同来源的数据，标注差异："来源A显示X，来源B显示Y，差异可能因为..."
- **敏感话题**：保持客观中立，避免主观判断，专注于数据和事实
- **时效性**：数据超过6个月应标注【历史数据】，提醒可能过时
 
提供准确、专业、有洞察力的商业分析，维护企业级标准。"""
 
```

## [](#开始使用kimi-k2-api)

### [](#安装openai-sdk)

```python
pip3 install --upgrade 'openai>=1.0'
# 安装后通过下面方法验证
python3 -c 'import openai; print("version =",openai.__version__)'
# 输出可能是 version = 1.10.0，表示 OpenAI SDK 已经安装成功，当前 python 实际使用了 openai 的 v1.10.0 的库
```

### [](#配置环境)

在开始前，请确保将您的 API\_KEY 配置为环境变量：

```python
export MOONSHOT_BASE_URL = "https://api.moonshot.cn/v1" # 您申请api对应的base_url
export MOONSHOT_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx" # 替换为您的api_key
```

此外，您还需要确保已安装以下依赖包：

```python
pip3 install openai httpx akshare pandas numpy matplotlib seaborn
 
# macOS
brew install --cask mactex
sudo tlmgr update --self
sudo tlmgr install ctex fontspec
xelatex --version
 
# Windows
choco install texlive -y
tlmgr update --self
tlmgr install xetex ctex fontspec
xelatex --version
```

### [](#完整代码示例)

```python
import os
import json
import asyncio
import argparse
import subprocess
import sys
import httpx
import akshare as ak
from openai import AsyncOpenAI
import glob
 
SYSTEM_PROMPT = r""" 在这里加入您的 system prompt """
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "company_info",
            "description": "根据公司名称获取公司信息（股票代码、市场类型、上市状态等）。当你的知识无法回答用户提出的问题，或用户请求你进行公司信息查询时，调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "用户想要查询的公司的准确名称，请从与用户的对话中提取。"
                    }
                },
                "required": ["name"]
            }
        }
    }
]
 
common_code = """
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
import seaborn as sns
from datetime import datetime, timedelta
import os
import json
 
# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'PingFang SC', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
 
"""
 
def get_company_info(company_name: str) -> str:
    """调用 AKShare API 获取公司信息"""
    try:
        stock_info_df = ak.stock_info_a_code_name()
        matches = stock_info_df[stock_info_df['name'].str.contains(company_name, na=False)]
        if matches.empty:
            return f"未找到公司 '{company_name}' 的相关信息。请检查公司名称是否正确或尝试使用公司简称。"
        results = []
        for _, row in matches.head(5).iterrows(): 
            code = row.get('code', 'N/A')
            name = row.get('name', 'N/A')
        
            try:
                detail_df = ak.stock_individual_info_em(symbol=code)
                detail_dict = dict(zip(detail_df['item'], detail_df['value']))
                
                info = {
                    "股票代码": code,
                    "公司名称": name,
                    "总市值": detail_dict.get('总市值', 'N/A'),
                    "流通市值": detail_dict.get('流通市值', 'N/A'),
                    "行业": detail_dict.get('行业', 'N/A'),
                    "上市时间": detail_dict.get('上市时间', 'N/A'),
                    "股票简称": detail_dict.get('股票简称', name),
                    "总股本": detail_dict.get('总股本', 'N/A'),
                    "流通股": detail_dict.get('流通股', 'N/A'),
                }
            except Exception:
                info = {
                    "股票代码": code,
                    "公司名称": name,
                }
            
            results.append(info)
        
        return json.dumps(results, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"获取公司信息时出错：{str(e)}"
 
class FormulaChatClient:
    def __init__(self, moonshot_base_url: str, api_key: str):
        self.openai = AsyncOpenAI(base_url=moonshot_base_url, api_key=api_key)
        self.httpx = httpx.AsyncClient(
            base_url=moonshot_base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        self.model = "kimi-k2-turbo-preview"
        self.max_tokens = 32768
        self.local_execution_keywords = ["plt.savefig", "plt.save", ".to_excel", "open(", ".to_csv", "pdf.", ".tex"]
 
    async def get_tools(self, formula_uri: str):
        response = await self.httpx.get(f"/formulas/{formula_uri}/tools")
        return response.json().get("tools", [])
 
    async def call_tool(self, formula_uri: str, function: str, args: dict):
        response = await self.httpx.post(
            f"/formulas/{formula_uri}/fibers",
            json={"name": function, "arguments": json.dumps(args)},
        )
        fiber = response.json()
 
        if fiber.get("status") == "succeeded":
            return fiber["context"].get("output") or fiber["context"].get("encrypted_output")
 
        # Handle errors
        error_msg = fiber.get("error") or fiber.get("context", {}).get("error") or \
                    fiber.get("context", {}).get("output") or "Unknown error"
        return f"Error: {error_msg}"
 
    async def handle_response(self, response, messages, all_tools, tool_to_uri):
        message = response.choices[0].message
        messages.append(message)
        
        if not message.tool_calls:
            print(f"\n{message.content}")
            return
 
        print(f"\n[调用工具: {len(message.tool_calls)}个]")
 
        for call in message.tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
 
            print(f"→ {func_name}")
            
            # 处理自定义工具
            if func_name == "company_info":
                company_name = args.get("name", "")
                result = get_company_info(company_name)
                print(f"公司信息: {result}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
                continue
            
            # 处理远程 formula 工具
            uri = tool_to_uri.get(func_name)
            if not uri:
                raise ValueError(f"No URI found for tool {func_name}")
 
            if func_name == "code_runner":
                self.execute_code_runner(args)
 
            result = await self.call_tool(uri, func_name, args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
 
        next_response = await self.openai.chat.completions.create(
            model=self.model, messages=messages, tools=all_tools, max_tokens=self.max_tokens
        )
        await self.handle_response(next_response, messages, all_tools, tool_to_uri)
 
    def convert_tex_to_pdf(self, tex_file):
        pdf_file = tex_file.replace('.tex', '.pdf')
        # 获取tex文件所在目录
        work_dir = os.path.dirname(os.path.abspath(tex_file))
        tex_name = os.path.basename(tex_file)
        
        try:
            subprocess.run(
                ['xelatex', '-interaction=nonstopmode', tex_file],
                capture_output=True,
                text=True,
                cwd=work_dir if work_dir else '.',
            )
            for ext in ['.aux', '.log', '.out']:
                temp_file = os.path.join(work_dir if work_dir else '.', tex_name.replace('.tex', ext))
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
            print(f"  [已生成PDF: {pdf_file}]")
        except FileNotFoundError:
            print("  [PDF转换失败: xelatex未安装]")
        except subprocess.CalledProcessError as e:
            print("  [PDF转换失败: LaTeX编译出错]")
            if e.stdout:
                print(f"  错误输出: {e.stdout[-500:]}")
        except Exception as e:
            print(f"  [PDF转换失败: {str(e)}]")
 
    def execute_code_runner(self, args):
        code = args.get("code", "") if isinstance(args, dict) else str(args or "")
        
        if not code or not any(keyword in code for keyword in self.local_execution_keywords):
            return
        before_tex_files = set(glob.glob('*.tex'))
        try:
            subprocess.run(
                [sys.executable, "-c", common_code+code],
                capture_output=True,
                text=True,
                check=True,
            )
            after_tex_files = set(glob.glob('*.tex'))
            new_tex_files = after_tex_files - before_tex_files
            for tex_file in new_tex_files:
                self.convert_tex_to_pdf(tex_file)
                
        except Exception as e:
            print(f"  [Local execution failed: {e}]")
 
    async def chat(self, question, messages, all_tools, tool_to_uri):
        messages.append({"role": "user", "content": question})
        response = await self.openai.chat.completions.create(
            model=self.model, messages=messages, tools=all_tools, max_tokens=self.max_tokens
        )
        await self.handle_response(response, messages, all_tools, tool_to_uri)
 
    async def close(self):
        await self.httpx.aclose()
 
def normalize_formula_uri(uri: str) -> str:
    """Normalize formula URI with default namespace and tag"""
    if "/" not in uri:
        uri = f"moonshot/{uri}"
    if ":" not in uri:
        uri = f"{uri}:latest"
    return uri
 
async def main():
    parser = argparse.ArgumentParser(description="Formula chat client")
    parser.add_argument(
        "--formula",
        action="append",
        default=["moonshot/web-search:latest", "moonshot/rethink:latest", "moonshot/code-runner:latest"],
        help="Formula URIs",
    )
    parser.add_argument("--question", help="Question to ask")
 
    args = parser.parse_args()
 
    # Process and deduplicate formula URIs
    normalized_formulas = [normalize_formula_uri(uri) for uri in args.formula]
    unique_formulas = list(dict.fromkeys(normalized_formulas))
 
    moonshot_base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
    api_key = os.getenv("MOONSHOT_API_KEY")
 
    if not api_key:
        print("Error: MOONSHOT_API_KEY environment variable is required")
        return
 
    client = FormulaChatClient(moonshot_base_url, api_key)
 
    # Load tools
    all_tools = []
    tool_to_uri = {}
 
    for tool in TOOLS:
        func = tool.get("function")
        if func:
            func_name = func.get("name")
            all_tools.append(tool)
            tool_to_uri[func_name] = "custom"
 
    for uri in unique_formulas:
        tools = await client.get_tools(uri)
        for tool in tools:
            func = tool.get("function")
            if not func:
                continue
            
            func_name = func.get("name")
            if not func_name or func_name in tool_to_uri:
                continue
 
            all_tools.append(tool)
            tool_to_uri[func_name] = uri
 
    if not all_tools:
        print("Error: No tools loaded")
        return
 
    print(f"已加载 {len(all_tools)} 个工具")
 
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        if args.question:
            print(f"\n问题: {args.question}")
            await client.chat(args.question, messages, all_tools, tool_to_uri)
        else:
            print("\n对话模式 (输入 'q' 退出)\n")
            while True:
                question = input("Q: ").strip()
                if question.lower() == "q":
                    break
                if question:
                    await client.chat(question, messages, all_tools, tool_to_uri)
 
    finally:
        await client.close()
 
if __name__ == "__main__":
    asyncio.run(main())
```

其中的 system prompt 您可以直接使用上面的样例，也可以自行修改为合适的内容。运行成功后，您可以与 Kimi K2 对话， Kimi K2 将自动完成行业信息整理任务。生成的文件将保存在本地目录下。

### [](#运行示例)

#### [](#调研并撰写报告)

运行程序后，我们在终端给 Kimi K2 下达下面的指令，等待片刻：

```bash
Q: 帮我调研2023-2025年中国人形机器人行业的发展情况。
```

得到下面的回复（可以看出，这是报告的摘要）：

```bash
# 2023-2025年中国人形机器人行业发展深度研究报告
 
## 执行摘要
 
2023-2025年中国人形机器人产业进入快速发展期，市场规模从15.6亿元增长至32.4亿元，年复合增长率达44.2%。技术创新加速推进，应用场景不断拓展，产业链日趋完善，政策支持力度持续加大，产业正从实验室走向商业化应用。
 
**核心发现：**
- 2025年中国人形机器人市场规模达到**32.4亿元**，出货量突破**1.24万台**，成为全球第二大市场
- 宇树科技、智元机器人等头部企业形成"双寡头"格局，合计市场份额超过**60%**
- 2024年行业融资总额达**200亿元**，同比增长**150%**，资本热度持续升温
- 工业制造成为最大应用场景，占比**35%**，汽车制造业成为首个规模化应用行业
- 北京、上海、深圳等地形成产业集聚，政策支持力度空前，产业发展环境持续优化
 
## 核心数据分析
 
### 市场规模爆发式增长
 
中国人形机器人市场呈现爆发式增长态势。2023年市场规模为15.6亿元，2024年增长至21.8亿元，同比增长39.7%。预计到2025年，市场规模将达到32.4亿元，同比增长48.6%，三年复合增长率达44.2%。
 
从出货量看，2023年中国人形机器人出货量为3500台，2024年激增至7300台，同比增长108.6%。2025年预计出货量将达到1.24万台，同比增长69.9%，显示出强劲的增长势头。
 
### 竞争格局基本形成
 
中国人形机器人产业呈现"双寡头+多强"的竞争格局。宇树科技和智元机器人作为第一梯队，合计市场份额超过60%。
 
**宇树科技**2024年人形机器人出货量达1400台，全球市场份额第一，营收超过10亿元，成为行业首家实现盈利的企业。**智元机器人**2024年出货量达1000台，在具身智能技术方面具有领先优势。
 
### 资本热度持续升温
 
中国人形机器人行业融资呈现爆发式增长态势。2023年融资总额为80亿元，2024年激增至200亿元，同比增长150%。2025年预计融资总额将达到280亿元，同比增长40%。
 
从融资事件数看，2023年发生120起融资事件，2024年增长至200起，同比增长66.7%。2025年预计达到260起，同比增长30%。截至2025年，人形机器人领域已诞生多家独角兽企业，宇树科技估值超过100亿元，智元机器人估值达180亿元。
 
### 应用场景不断拓展
 
工业制造是人形机器人最大的应用场景，2025年预计占比35%，市场规模11.3亿元。汽车制造是首个规模化应用的行业，特斯拉、比亚迪、吉利、蔚来等车企都在积极试验人形机器人应用。
 
服务业是人形机器人的第二大应用场景，2025年预计占比25%，市场规模8.1亿元。医疗康复、教育科研、家庭服务等场景也在快速发展。
 
## 政策环境分析
 
国家层面政策支持力度空前。2023年11月，工信部发布《人形机器人创新发展指导意见》，明确提出到2025年初步建立人形机器人创新体系，到2027年综合实力达到世界先进水平。
 
地方政策形成梯次布局。北京发布《北京市机器人产业创新发展行动方案（2023—2025年）》，设立100亿元机器人产业发展投资基金；上海组建百亿级产业基金，建设国际机器人产业高地；深圳出台专项政策，支持人形机器人核心技术攻关和产业化应用。
 
## 技术发展趋势
 
人形机器人技术体系可分为"大脑"、"小脑"、"肢体"三个层次。大脑层基于大模型的认知决策系统，小脑层负责运动控制系统，肢体层包括机械结构和执行机构。
 
**关键技术突破包括：**
- 具身智能技术：2024年，智元机器人发布具身智能G1到G5技术路线图，在通用位姿估计模型UniPose等方面取得阶段性突破
- 群体智能技术：2025年3月，优必选在极氪5G智慧工厂开展人形机器人协同实训，推动人形机器人从单机自主向群体智能进化
- 多模态感知技术：2025年，部分企业多模态感知精度达到95%以上
 
## 挑战与机遇
 
### 主要挑战
 
**技术挑战**：人形机器人在运动控制、环境感知、智能决策等方面仍有待突破。特别是在复杂环境下的自主作业能力、人机交互的自然性等方面，与国际先进水平仍有差距。
 
**成本挑战**：目前人形机器人成本仍然较高，单台价格从几十万元到数百万元不等，严重制约了大规模商业化应用。
 
**标准挑战**：人形机器人行业标准体系尚不完善，在安全性、可靠性、互操作性等方面缺乏统一标准。
 
### 发展机遇
 
**政策机遇**：国家将人形机器人产业列为战略性新兴产业，政策支持力度持续加大。
 
**市场机遇**：中国拥有全球最大的制造业市场和最完整的工业体系，为人形机器人应用提供了广阔空间。
 
**技术机遇**：人工智能、5G、物联网等新兴技术快速发展，为人形机器人技术突破提供了有力支撑。
 
## 发展趋势预测
 
未来3-5年，人形机器人技术将呈现以下发展趋势：
 
**智能化水平大幅提升**：随着大模型技术的不断发展，人形机器人将具备更强的推理能力和泛化能力，从专用向通用方向发展。
 
**运动能力显著增强**：运动控制算法将不断优化，机器人将具备更强的环境适应能力和操作精度。
 
**成本快速下降**：随着规模化生产和核心零部件国产化，人形机器人成本将下降50%以上。
 
预计到2030年，中国人形机器人市场规模将突破200亿元，出货量达到10万台以上，年复合增长率超过50%。
 
## 投资建议
 
### 投资方向建议
 
**核心零部件领域**：重点关注减速器、伺服电机、传感器等核心零部件企业。这些领域技术门槛高、价值占比大、国产化率低，具有较大投资机会。
 
**整机制造领域**：重点关注技术领先、市场认可度高的整机制造企业。这些企业将在产业爆发期获得最大收益。
 
**应用服务领域**：重点关注在特定应用场景具有深度布局的企业。这些企业将通过应用创新获得差异化竞争优势。
 
### 风险提示
 
**技术风险**：人形机器人技术仍在快速发展中，存在技术路线不确定、技术突破不及预期等风险。
 
**市场风险**：人形机器人市场仍处于培育期，存在市场需求不及预期、商业化进程缓慢等风险。
 
**政策风险**：人形机器人产业高度依赖政策支持，存在政策调整、支持力度减弱等风险。
 
## 结论与建议
 
中国人形机器人产业正处于爆发式增长前夜，2023-2025年是产业发展的关键窗口期。在政策大力支持、技术不断突破、市场持续拓展的多重驱动下，产业有望在未来5-10年内实现跨越式发展。
 
**政策建议**：加强顶层设计，加大支持力度，完善标准体系，强化人才培养，推动国际合作。
 
**企业建议**：加强技术创新，深化应用探索，强化生态合作，提升品牌价值，拓展国际市场。
 
**投资建议**：关注头部企业，布局核心环节，保持长期视角，分散投资风险，关注政策导向。
```

另外，在目录下我们还可以发现 pdf 格式的完整报告：

[完整的报告 (opens in a new tab)](https://statics.moonshot.cn/platform/%E4%B8%AD%E5%9B%BD%E4%BA%BA%E5%BD%A2%E6%9C%BA%E5%99%A8%E4%BA%BA%E8%A1%8C%E4%B8%9A_%E6%8A%A5%E5%91%8A_20250130.pdf)

#### [](#常见问题)

由于上面的 case 代码只是一个简单的尝试，尚待补充和完善，所以在运行时您可能会遇到一些问题，这些问题的解决方法可参考 *（不断更新中）*：

+   code-runner 循环调用报错：
    +   保存 response.json ，检查格式是否正确。
    +   如果格式正确，观察重点字段。如果发现 `"finish_reason"` 是 `"length"` ，说明当前指定的每轮对话 `max_tokens` 太小（当前代码中给定的是32k，您可以合理修改）。
    +   如果不是长度问题，在 `"arguments"` 中提取 `"code"` 的内容，即生成的原始代码，试试能不能运行。可以通过优化 prompt 等方式让生成代码质量提高。

## [](#评估和优化)

通过上面的步骤，我们已经可以顺利使用 Kimi K2 完成行业信息整理的工作。在更加复杂的场景中，您可以通过下面的一些方式优化 Kimi K2 的表现。

### [](#使用合适的-tool-call)

除了 Kimi K2 官方工具外，您还可以定义并执行自己所需的工具。以“查询公司的股票代码等准确信息”为例，下面是可参考的构造和使用流程。

#### [](#定义工具)

通过 JSON Schema 来描述我们的工具定义，能让 Kimi K2 大模型更清晰和直观地知道我们的工具需要哪些参数，以及每个参数的类型和介绍。

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "company_info",
            "description": "根据公司名称获取公司信息（股票代码、市场类型、上市状态等）。当你的知识无法回答用户提出的问题，或用户请求你进行公司信息查询时，调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "用户想要查询的公司的准确名称，请从与用户的对话中提取。"
                    }
                },
                "required": ["name"]
            }
        }
    }
    // 可以仿照上面的格式继续定义更多工具
]
```

这里我们创建了名为 `company_info` 的工具，向大模型描述了工具的应用场景和所需参数 name（公司名称）。

#### [](#执行工具)

我们还需要实现查询功能，在原代码中加入下面的函数：

```python
def get_company_info(company_name: str) -> str:
    """调用 AKShare API 获取公司信息"""
    try:
        stock_info_df = ak.stock_info_a_code_name()
        matches = stock_info_df[stock_info_df['name'].str.contains(company_name, na=False)]
        if matches.empty:
            return f"未找到公司 '{company_name}' 的相关信息。请检查公司名称是否正确或尝试使用公司简称。"
        results = []
        for _, row in matches.head(5).iterrows(): 
            code = row.get('code', 'N/A')
            name = row.get('name', 'N/A')
        
            try:
                detail_df = ak.stock_individual_info_em(symbol=code)
                detail_dict = dict(zip(detail_df['item'], detail_df['value']))
                
                info = {
                    "股票代码": code,
                    "公司名称": name,
                    "总市值": detail_dict.get('总市值', 'N/A'),
                    "流通市值": detail_dict.get('流通市值', 'N/A'),
                    "行业": detail_dict.get('行业', 'N/A'),
                    "上市时间": detail_dict.get('上市时间', 'N/A'),
                    "股票简称": detail_dict.get('股票简称', name),
                    "总股本": detail_dict.get('总股本', 'N/A'),
                    "流通股": detail_dict.get('流通股', 'N/A'),
                }
            except Exception:
                info = {
                    "股票代码": code,
                    "公司名称": name,
                }
            
            results.append(info)
        
        return json.dumps(results, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return f"获取公司信息时出错：{str(e)}"
```

#### [](#注册工具)

另外在对应注册工具的位置进行补充，就可以让模型自动调用我们自己定义的新工具了：

```python
for call in message.tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
 
            print(f"→ {func_name}")
            
            # 处理自定义工具（新增部分）
            if func_name == "company_info":
                company_name = args.get("name", "")
                result = get_company_info(company_name)
                print(f"公司信息: {result}")
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
                continue
            
            # 处理远程 formula 工具（原有部分）
            uri = tool_to_uri.get(func_name)
            if not uri:
                raise ValueError(f"No URI found for tool {func_name}")
 
            if func_name == "code_runner":
                self.execute_code_runner(args)
 
            result = await self.call_tool(uri, func_name, args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
 
        next_response = await self.openai.chat.completions.create(
            model=self.model, messages=messages, tools=all_tools, max_tokens=self.max_tokens
        )
```

上面的完整代码已经加入了本工具，运行后可以进行对话进行测试：

```bash
Q: 帮我查找宁德时代公司的股票代码
 
[调用工具: 1个]
→ company_info
公司信息: [                                                                                                                                                      
  {
    "股票代码": "300750",
    "公司名称": "宁德时代",
    "总市值": 1817339120058.29,
    "流通市值": 1694973917202.29,
    "行业": "电池",
    "上市时间": 20180611,
    "股票简称": "宁德时代",
    "总股本": 4562854001.0,
    "流通股": 4255627601.0
  }
]
 
AI Response：根据查询结果，宁德时代公司的股票信息如下：
 
**股票代码：300750**
 
**公司基本信息：**
- 股票简称：宁德时代
- 行业：电池
- 上市时间：2018年6月11日
- 总股本：45.63亿股
- 流通股：42.56亿股
- 总市值：约1.82万亿元
- 流通市值：约1.69万亿元
```

像这样，我们可以将许多常用的功能定义为工具，将会有效提升大模型的输出效果。

# 15. Prompt 最佳实践

## Prompt 最佳实践

> System Prompt最佳实践：system prompt（系统提示）指的是模型在生成文本或响应之前所接收的初始输入或指令，这个提示对于模型的运作至关[重要 (opens in a new tab)](https://kimi.moonshot.cn/share/col3fn2lnl95v16j0g2g)

## [](#编写清晰的说明)

+   为什么需要向模型输出清晰的说明？

> 模型无法读懂你的想法，如果输出内容太长，可要求模型简短回复。如果输出内容太简单，可要求模型进行专家级写作。如果你不喜欢输出的格式，请向模型展示你希望看到的格式。模型越少猜测你的需求，你越有可能得到满意的结果。

### [](#在请求中包含更多细节可以获得更相关的回答)

> 为了获得高度相关的输出，请保证在输入请求中提供所有重要细节和背景。

| 一般的请求 | 更好的请求 |
| --- | --- |
| 如何在Excel中增加数字？ | 我如何在Excel表对一行数字求和？我想自动为整张表的每一行进行求和，并将所有总计放在名为"总数"的最右列中。 |
| 工作汇报总结 | 将2023年工作记录总结为500字以内的段落。以序列形式列出每个月的工作亮点，并做出2023年全年工作总结。 |

### [](#在请求中要求模型扮演一个角色可以获得更准确的输出)

> 在 API 请求的'messages' 字段中增加指定模型在回复中使用的角色。

```json
{
  "messages": [
    {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
    {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"}
  ]
}
```

### [](#在请求中使用分隔符来明确指出输入的不同部分)

> 例如使用三重引号/XML标签/章节标题等定界符可以帮助区分需要不同处理的文本部分。

```json
{
  "messages": [
    {"role": "system", "content": "你将收到两篇相同类别的文章，文章用XML标签分割。首先概括每篇文章的论点，然后指出哪篇文章提出了更好的论点，并解释原因。"},
    {"role": "user", "content": "<article>在这里插入文章</article><article>在这里插入文章</article>"}
  ]
}
```

```json
{
  "messages": [
    {"role": "system", "content": "你将收到一篇论文的摘要和论文的题目。论文的题目应该让读者对论文主题有清晰的概念，同时也应该引人注目。如果你收到的标题不符合这些标准，请提出5个可选的替代方案"},
    {"role": "user", "content": "摘要:在这里插入摘要。\n\n标题:在这里插入标题"}
  ]
}
```

### [](#明确完成任务所需的步骤)

> 任务建议明确一系列步骤。明确写出这些步骤可以使模型更容易遵循并获得更好的输出。

```json
{
  "messages": [
    {"role": "system", "content": "使用以下步骤来回应用户输入。\n步骤一：用户将用三重引号提供文本。用前缀“摘要：”将这段文本概括成一句话。\n步骤二：将第一步的摘要翻译成英语，并加上前缀 "Translation: "。"},
    {"role": "user", "content": "\"\"\"在此处插入文本\"\"\""}
  ]
}
```

### [](#向模型提供输出示例)

> 向模型提供一般指导的示例描述，通常比展示任务的所有排列让模型的输出更加高效。例如，如果你打算让模型复制一种难以明确描述的风格，来回应用户查询。这被称为“few-shot”提示。

```json
{
  "messages": [
    {"role": "system", "content": "以一致的风格回答"},
    {"role": "user", "content": "在此处插入文本"}
  ]
}
```

### [](#指定期望模型输出的长度)

> 你可以要求模型生成特定目标长度的输出。目标输出长度可以用文数、句子数、段落数、项目符号等来指定。但请注意，指示模型生成特定数量的文字并不具有高精度。模型更擅长生成特定数量的段落或项目符号的输出。

```json
{
  "messages": [
    {"role": "user", "content": "用两句话概括三引号内的文本，50字以内。\"\"\"在此处插入文本\"\"\""}
  ]
}
```

## [](#提供参考文本)

### [](#指导模型使用参考文本来回答问题)

> 如果您可以提供一个包含与当前查询相关的可信信息的模型，那么就可以指导模型使用所提供的信息来回答问题

```json
{
  "messages": [
    {"role": "system", "content": "使用提供的文章（用三引号分隔）回答问题。如果答案在文章中找不到，请写"我找不到答案。" "},
    {"role": "user", "content": "<请插入文章，每篇文章用三引号分隔>"}
  ]
}
```

## [](#拆分复杂的任务)

### [](#通过分类来识别用户查询相关的指令)

> 对于需要大量独立指令集来处理不同情况的任务来说，对查询类型进行分类，并使用该分类来明确需要哪些指令可能会帮助输出。

```json
# 根据客户查询的分类，可以提供一组更具体的指示给模型，以便它处理后续步骤。例如，假设客户需要“故障排除”方面的帮助。
{
  "messages": [
    {"role": "system", "content": "你将收到需要技术支持的用户服务咨询。可以通过以下方式帮助用户：\n\n-请他们检查***是否配置完成。\n如果所有***都配置完成，但问题依然存在，请询问他们使用的设备型号\n-现在你需要告诉他们如何重启设备：\n=设备型号是A，请操作***。\n-如果设备型号是B，建议他们操作***。"}
  ]
}
```

### [](#对于轮次较长的对话应用程序总结或过滤之前的对话)

> 由于模型有固定的上下文长度显示，所以用户与模型助手之间的对话不能无限期地继续。

针对这个问题，一种解决方案是总结对话中的前几个回合。一旦输入的大小达到预定的阈值，就会触发一个查询来总结先前的对话部分，先前对话的摘要同样可以作为系统消息的一部分包含在内。或者，整个对话过程中的先前对话可以被异步总结。

### [](#分块概括长文档并递归构建完整摘要)

> 要总结一本书的内容，我们可以使用一系列的查询来总结文档的每个章节。部分摘要可以汇总并总结，产生摘要的摘要。这个过程可以递归进行，直到整本书都被总结完毕。如果需要使用前面的章节来理解后面的部分，那么可以在总结书中给定点的内容时，包括对给定点之前的章节的摘要。


# 16. 常见问题及解决方案

## 常见问题及解决方案

## [](#为什么-api-返回的结果和-kimi-智能助手返回的结果不一致)

API 和 Kimi 智能助手使用的是同一模型，如果你发现模型输出结果不一致，可以尝试修改 System Prompt；另一方面 Kimi 智能助手提供了诸如计算器等工具，而 API 并未默认提供这些工具，需要用户自行组装；

## [](#kimi-api-是否拥有-kimi-智能助手的上网冲浪功能)

否。Kimi API 仅提供了大模型本身的交互功能，并不具备额外的“内容搜索”和“网页内容浏览”功能，也即是通常意义上的“联网搜索”功能。

现在，Kimi API 提供了联网搜索功能，请查阅我们的指南：

[使用 Kimi API 的联网搜索功能](https://platform.moonshot.cn/docs/guide/use-web-search)

如果你想自己通过 Kimi API 实现联网搜索功能，也可以参考我们撰写的工具调用 `tool_calls` 指南：

[使用 Kimi API 完成工具调用（tool\_calls）](https://platform.moonshot.cn/docs/guide/use-kimi-api-to-complete-tool-calls)

如果你想寻求开源社区的协助，你可以参考以下开源项目：

+   [search2ai (opens in a new tab)](https://github.com/fatwang2/search2ai)
+   [ArchiveBox (opens in a new tab)](https://github.com/ArchiveBox/ArchiveBox)

如果你想寻求由专业供应商提供的服务，有如下服务可供选择：

+   [apify (opens in a new tab)](https://apify.com/)
+   [crawlbase (opens in a new tab)](https://zh-cn.crawlbase.com/enterprise)
+   [jina reader (opens in a new tab)](https://jina.ai/reader/)

## [](#kimi-api-返回的内容不完整或被截断)

如果你发现 Kimi API 返回的内容不完整、被截断或长度不符合预期，你可以先检查响应体中的 `choice.finish_reason` 字段的值，如果该值为 `length`，则表明当前模型生成内容所包含的 Tokens 数量超过请求中的 `max_tokens` 参数，在这种情况下，Kimi API 仅会返回 `max_tokens` 个 Tokens 内容，多余的内容将会被丢弃，即上文所说“内容不完整”或“内容被截断”。

在遇到 `finish_reason=length` 时，如果你想让 Kimi 大模型接着上一次返回的内容继续输出，可以使用 Kimi API 提供的 Partial Mode，详细的文档请参考：

[使用 Kimi API 的 Partial Mode](https://platform.moonshot.cn/docs/guide/use-partial-mode-feature-of-kimi-api)

如果你想避免出现 `finish_reason=length`，我们建议你放大 `max_tokens` 的值，我们推荐的最佳实践是：通过 [estimate-token-count (opens in a new tab)](https://platform.moonshot.cn/docs/api/misc#%E8%AE%A1%E7%AE%97-token) 接口计算输入内容的 Tokens 数量，随后使用 Kimi 大模型所支持的最大 Tokens 数量（例如，对于 `moonshot-v1-32k` 模型，它最大支持 32k Tokens），则可以设置的最大请求的 `max_tokens` 值是 32k。

## [](#kimi-大模型的输出长度是多少)

+   对于 `moonshot-v1-8k` 模型而言，最大输出长度是 `8*1024 － prompt_tokens`；
+   对于 `moonshot-v1-32k` 模型而言，最大输出长度是 `32*1024 － prompt_tokens`；
+   对于 `moonshot-v1-128k` 模型而言，最大输出长度是 `128*1024 － prompt_tokens`；
+   对于 `kimi-k2-0905-preview` 和 `kimi-k2-turbo-preview` 模型而言，最大输出长度是 `256*1024 － prompt_tokens`；

## [](#kimi-大模型支持的汉字数量是多少)

+   对于 `moonshot-v1-8k` 模型而言，大约支持一万五千个汉字；
+   对于 `moonshot-v1-32k` 模型而言，大约支持六万个汉字；
+   对于 `moonshot-v1-128k` 模型而言，大约支持二十万个汉字；
+   对于 `kimi-k2-0905-preview` 和 `kimi-k2-turbo-preview` 模型而言，大约支持四十万个汉字；

*注：以上均为估算值，实际情况可能有所不同。*

## [](#文件抽取内容不准确图像无法被识别)

我们提供各种格式的文件上传和文件解析服务，**对于文本文件，我们会提取文件中的文字内容；对于图片文件，我们会使用 OCR 识别图片中的文字；对于 PDF 文档，如果 PDF 文档中只包含图片，我们会使用 OCR 提取图片中的文字，否则仅会提取文本内容。**；

*注意，对于图片，我们只会使用 OCR 提取图片中的文字内容，因此如果你的图片中不包含任何文字内容，则会引起解析失败的错误。*

完整的文件格式支持列表，请参考：

[文件接口 (opens in a new tab)](https://platform.moonshot.cn/docs/api/files#%E4%B8%8A%E4%BC%A0%E6%96%87%E4%BB%B6)

## [](#使用-files-接口时希望使用-file_id-引用文件内容)

我们目前不支持使用文件 `file_id` 的方式引用文件内容作为上下文。

## [](#使用接口报错-content_filter-the-request-was-rejected-because-it-was-considered-high-risk)

当前请求 Kimi API 的输入或 Kimi 大模型的输出内容包含不安全或敏感内容，**注意：Kimi 大模型生成的内容也可能包含不安全或敏感内容，进而导致 `content_filter` 错误**。

## [](#出现-connection-相关错误)

如果在使用 Kimi API 的过程中，经常出现 `Connection Error`、`Connection Time Out` 等错误，请按照以下顺序检查：

1.  程序代码或使用的 SDK 是否有默认的超时设置；
2.  是否有使用任何类型的代理服务器，并检查代理服务器的网络和超时设置；

另一种可能导致 `Connection` 相关错误的场景是，未启用流式输出 `stream=True` 时，Kimi 大模型生成的 Tokens 数量过多，导致在等待 Kimi 大模型生成过程时，触发了某个中间环节网关的超时时间设置。通常，某些网关应用会通过检测是否接收到服务器端返回的 `status_code` 和 `header` 来判断当前请求是否有效，在不使用流式输出 `stream=True` 的场合，Kimi 服务端会等待 Kimi 大模型生成完毕后发送 `header`，在等待 `header` 返回时，某些网关应用会关闭等待时间过长的连接，进而产生 `Connection` 相关错误。

**我们推荐启用流式输出 `stream=True` 来尽可能减少 `Connection` 相关错误。**

## [](#报错信息显示的-tpmrpm-限制与我的账户-tier-等级不匹配)

如果你在使用 Kimi API 的过程遇到了 `rate_limit_reached_error` 错误，例如：

```text
rate_limit_reached_error: Your account {uid}<{ak-id}> request reached TPM rate limit, current:{current_tpm}, limit:{max_tpm}
```

但报错信息中的 TPM 或 RPM 限制与你在后台查看的 TPM 与 RPM 并不匹配，请先排查是否正确使用了当前账户的 `api_key`；通常情况下 TPM、RPM 与预期不匹配的原因，是使用了错误的 `api_key`，例如误用了其他用户给予的 `api_key`，或个人拥有多个账号的情况下，混用了 `api_key`。

## [](#报错-model_not_found)

请确保你在 SDK 中正确设置了 `base_url=https://api.moonshot.cn`，通常情况下，`model_not_found` 错误产生的原因是，使用 OpenAI SDK 时，未设置 `base_url` 值，导致请求被发送至 OpenAI 服务器，OpenAI 返回了 `model_not_found` 错误。

## [](#kimi-大模型出现数值计算错误)

由于 Kimi 大模型生成过程的不确定性，在数值计算方面，Kimi 大模型可能会出现不同程度的计算错误，我们推荐使用工具调用 `tool_calls` 为 Kimi 大模型提供计算器功能，关于工具调用 `tool_calls`，可以参考我们撰写的工具调用 `tool_calls` 指南：

[使用 Kimi API 完成工具调用（tool\_calls）](https://platform.moonshot.cn/docs/guide/use-kimi-api-to-complete-tool-calls)

## [](#kimi-大模型无法回答今天的日期)

Kimi 大模型无法获取像当前日期这样时效性非常强的信息，但你可以在系统提示词 system prompt 中为 Kimi 大模型提供这样的信息，例如：

```python
import os
from datetime import datetime
from openai import OpenAI
 
client = OpenAI(
    api_key=os.environ['MOONSHOT_API_KEY'],
    base_url="https://api.moonshot.cn/v1",
)
 
# 我们通过 datetime 库生成了当前日期，并将其添加到系统提示词 system prompt 中
system_prompt = f"""
你是 Kimi，今天的日期是 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
 
completion = client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "今天的日期？"},
    ],
    temperature=0.3,
)
 
print(completion.choices[0].message.content)  # 输出：今天的日期是 2024 年 7 月 31 日。
 
```

## [](#在不使用-sdk-的场景下如何处理错误)

在某些场合，你可能会需要自行对接 Kimi API（而不是使用 OpenAI SDK），在自行对接 Kimi API 时，你需要根据 API 返回的状态来决定后续的处理逻辑。通常而言，我们会使用 HTTP 状态码 200 表示请求成功，而使用 4xx、5xx 的状态码表示请求失败，我们会提供一个 JSON 格式的错误信息，关于请求状态具体的处理逻辑，请参考以下的代码片段：

```python
import os
import httpx
 
header = {
    "Authorization": f"Bearer {os.environ['MOONSHOT_API_KEY']}",
}
 
messages = [
    {"role": "system", "content": "你是 Kimi"},
    {"role": "user", "content": "你好。"},
]
 
r = httpx.post("https://api.moonshot.cn/v1/chat/completions",
               headers=header,
               json={
                   "model": "moonshot-v1-128k",  # <-- 如果你使用一个正确的模型，下方会进入 if status_code==200 分支
                   # "model": "moonshot-v1-129k",  # <-- 如果你使用一个错误的模型名称，下方会进入 else 分支
                   "messages": messages,
                   "temperature": 0.3,
               })
 
if r.status_code == 200:  # 当使用正确的模型进行请求时，会进入此分支，进行正常的处理逻辑
    completion = r.json()
    print(completion["choices"][0]["message"]["content"])
else:  # 当使用错误的模型名称进行请求时，会进入此分支，在这里进行错误处理
    # 在这里，为了演示，我们仅将错误打印出来。
    # 在实际的代码逻辑中，你可能需要更多的处理逻辑，例如记录日志、中断请求或进行重试等。
    error = r.json()
    print(f"error: status={r.status_code}, type='{error['error']['type']}', message='{error['error']['message']}'")
```

我们的错误信息会遵循如下的格式：

```json
{
    "error": {
        "type": "error_type",
        "message": "error_message"
    }
}
```

具体的错误信息对照表，请参考如下章节：

[错误说明](https://platform.moonshot.cn/docs/api/chat#%E9%94%99%E8%AF%AF%E8%AF%B4%E6%98%8E)

## [](#为何在提示词-prompt-相似的情况下有的请求响应速度快有的请求响应速度慢)

如果你遇到在相似提示词 prompt 的不同请求中，有的请求响应快（例如响应时间只有 3s），有的请求响应慢（例如响应时间长达 20s），这通常是由于 Kimi 大模型生成的 Tokens 数量不同导致的。通常而言，Kimi 大模型生成的 Tokens 数量与 Kimi API 的响应时间成正比，生成的 Tokens 数量越多，API 完整的响应时间越长。

需要注意的是，Kimi 大模型生成的 Tokens 数量只影响完整请求（指生成完最后一个 Token）的响应时间，你可以设置 `stream=True`，并观察首 Token 返回时间（首 Token 返回时间，我们简称为 TTFT -- Time To First Token），通常情况下，提示词 prompt 的长度相似的场合，首 Token 响应时间不会有太大的波动。

## [](#我设置了-max_tokens2000让-kimi-输出-2000-字的内容但-kimi-输出的内容少于-2000-字)

`max_tokens` 参数的含义是：**调用 `/v1/chat/completions` 时，允许模型生成的最大 Tokens 数量，当模型已经生成的 Tokens 数超过设置的 `max_tokens` 时，模型会停止输出下一个 Token**。

`max_tokens` 的作用在于：

1.  帮助调用方确定该使用哪个模型（例如，当 `prompt_tokens ＋ max_tokens ≤ 8 * 1024` 时，可以选择 `moonshot-v1-8k` 模型）；
2.  防止在某些意外的场合，Kimi 模型输出了过多不符合预期的内容，进而导致额外的费用消耗（例如，Kimi 模型重复输出空白字符）；

`max_tokens` 并不能指示 Kimi 大模型输出多少 Tokens，换句话说，**`max_tokens` 不会作为提示词 prompt 的一部分输入 Kimi 大模型**，如果你想让模型输出特定字数的内容，可以参考以下通用的解决办法：

+   对于要求输出内容字数在 1000 字以内的场合：
    1.  在提示词 prompt 中向 Kimi 大模型明确输出的字数；
    2.  通过人工或程序手段检测输出的字数是否符合预期，如果不符合预期，通过在第二轮对话中向 Kimi 大模型指示“字数多了”或“字数少了”，让 Kimi 大模型输出新一轮的内容。
+   对于要求输出内容字数在 1000 字以上甚至更多时：
    1.  尝试将预期输出的内容按结构或章节切割成若干部分，并制成模板，并使用占位符标记想要 Kimi 大模型输出内容的位置；
    2.  让 Kimi 大模型按照模板，逐个填充每个模板的占位符部分，最终拼装成完整的长文文本。

## [](#我在一分钟内只请求了一次但却触发了-your-account-reached-max-request-错误)

通常，OpenAI 提供的 SDK 包含了重试机制：

> Certain errors are automatically retried 2 times by default, with a short exponential backoff. Connection errors (for example, due to a network connectivity problem), 408 Request Timeout, 409 Conflict, 429 Rate Limit, and >=500 Internal errors are all retried by default.

这种重试机制在遇到错误时，会默认重试 2 次（总计 3 次请求），通常来说，对于网络状况不稳定或者其他可能导致请求发生错误的场合，使用 OpenAI SDK 会将一个请求放大至 2 到 3 次请求，这些请求都会占用你的 RPM（每分钟请求数）次数。

*注：对于使用 OpenAI SDK 且账户等级为 `tier0` 的用户而言，由于存在默认的重试机制，一次错误的请求就会消耗完所有的 RPM 额度。*

## [](#为了便于传输我使用-base64-编码我的文本内容)

请不要这样做，使用 `base64` 编码你的文件会导致产生巨量的 Tokens 消耗。如果你的文件类型是我们 `/v1/files` 文件接口支持的格式，使用文件接口上传并抽取文件内容即可。

对于二进制或其他格式编码的文件，Kimi 大模型暂时无法解析内容，请不要添加到上下文中。

## [](#为什么我在-platformmoonshotai-平台申请的-key不能用在-platformmoonshotcn-平台)

Kimi 开放平台官方提供两个平台，中国境内建议使用 platform.moonshot.cn 平台，境外建议使用 platform.moonshot.ai 平台。两个平台的账户和 key 完全独立，不能混用。

如果用错会出现 401 invalid\_authentication\_error 的报错，收到 401 报错请先检查是否平台的 key 使用错误。

+   国内开放平台 base\_url: [https://api.moonshot.cn/v1 (opens in a new tab)](https://api.moonshot.cn/v1)
+   境外开放平台 base\_url: [https://api.moonshot.ai/v1 (opens in a new tab)](https://api.moonshot.ai/v1)

Last updated on 2026年2月12日

[组织管理最佳实践](https://platform.moonshot.cn/docs/guide/org-best-practice "组织管理最佳实践")[平台服务协议](https://platform.moonshot.cn/docs/agreement/modeluse "平台服务协议")