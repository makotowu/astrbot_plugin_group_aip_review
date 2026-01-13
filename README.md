# AstrBot 群聊内容安全审查插件

基于百度内容审核API的群聊内容安全审查插件，支持文本和图片内容审核，自动处置违规内容。

## 功能特性

- ✅ **文本内容审核**：实时检测群聊文本消息的合规性
- ✅ **图片内容审核**：自动审核群聊中的图片内容
- ✅ **智能违规处置**：根据审核结果自动撤回消息、禁言、踢人等
- ✅ **多层级配置**：支持全局默认配置和群组自定义配置
- ✅ **违规记录管理**：统计用户和群组的违规次数，智能触发惩罚机制
- ✅ **通知机制**：审核结果实时通知到指定群组

## 安装方法

1. 将插件文件夹放置到 AstrBot 的 `data/plugins/` 目录下
2. 在 AstrBot WebUI 的插件管理页面启用该插件
3. 配置百度内容审核API参数（详见配置说明）

## 配置说明

### 百度API配置

在插件配置页面填写以下必填项：

- `api_key`：百度云API Key（从百度云控制台获取）
- `secret_key`：百度云Secret Key（从百度云控制台获取）
- `strategy_id`：自定义审核策略ID（可选）

### 审核处置配置

#### 默认全局配置

- `notify_group_id`：默认通知群ID（所有无自定义的群共用）
- `bot_owner_id`：Bot主人ID（审核失败时通知）
- `single_user_violation_threshold`：单人短时间违规次数阈值（默认3次，设置为0表示不启用单人禁言功能）
- `group_violation_threshold`：群内短时间违规次数阈值（默认5次，设置为0表示不启用全员禁言功能）
- `time_window`：统计时间窗口（秒，默认300秒=5分钟）
- `mute_duration`：单人禁言时长（秒，默认86400秒=1天）
- `kick_user`：是否启用踢人（默认false）
- `kick_user_threshold`：踢人阈值（默认5次，设置为0表示不启用踢人功能）
- `is_kick_user_and_block`：是否踢出并拉黑用户（默认false）

#### 群组自定义配置

支持为每个群组单独配置，格式为：

```json
{
  "群ID": {
    "rule_id": "规则标识",
    "notify_group_id": "通知群ID",
    "single_user_violation_threshold": 2,
    "group_violation_threshold": 4,
    "time_window": 600,
    "mute_duration": 43200
  }
}
```

**配置说明：**
- `rule_id`：规则标识，用于区分不同的审核规则（默认default/strict/lenient）
- `群ID`：要配置的群号（纯数字）
- `notify_group_id`：违规内容通知群ID
- `single_user_violation_threshold`：单人短时间违规次数阈值（默认3次）
- `group_violation_threshold`：群内短时间违规次数阈值（默认5次）
- `time_window`：统计时间窗口（秒，默认300秒=5分钟）
- `mute_duration`：单人禁言时长（秒，默认86400秒=1天）
- `kick_user`：是否启用踢人（默认false）
- `kick_user_threshold`：踢人阈值（默认5次）
- `is_kick_user_and_block`：是否踢出并拉黑用户（默认false）

### 功能开关

- `enabled_groups`：启用插件的群号列表（默认空列表，不对任何群生效）
- `enable_text_censor`：是否启用文本审核（默认true，设置为false表示不启用文本审核功能）
- `enable_image_censor`：是否启用图片审核（默认true，设置为false表示不启用图片审核功能）
- `log_level`：日志级别（默认INFO）

## 审核结果处理

### 合规
- 不执行任何操作，只记录日志

### 不合规
- 立即撤回消息
- 记录违规次数
- 向对应群绑定的通知群发送消息
- 根据违规次数触发禁言、踢人等惩罚

### 疑似
- 向对应群绑定的通知群发送消息
- 联系管理员核实

### 审核失败
- 通知Bot主人

## 惩罚机制

### 单人违规处置
- **3次违规**：禁言用户1天
- **5次违规**：踢出用户（可选是否拉黑）

### 群组违规处置
- **5次违规**：开启全员禁言

## 依赖说明

- `baidu-aip`：百度内容审核API Python SDK
- `httpx`：异步HTTP客户端（AstrBot内置）

## 注意事项

1. **API配额**：百度内容审核API有调用次数限制，请合理配置审核频率
2. **网络要求**：插件需要访问百度云API，请确保网络连接正常
3. **权限要求**：Bot需要具备管理员权限才能执行撤回、禁言等操作
4. **配置备份**：建议定期备份插件配置，防止数据丢失

## 故障排除

### 常见问题

1. **API调用失败**：检查API Key和Secret Key是否正确
2. **消息撤回失败**：检查Bot是否具有管理员权限
3. **审核结果不准确**：可在百度云控制台调整审核策略

### 日志查看

插件运行日志可在 AstrBot 日志文件中查看，关键词：`群聊内容安全审查插件`

## 更新日志

### v1.0.0
- 初始版本发布
- 支持文本和图片内容审核
- 实现完整的违规处置机制
- 支持群组自定义配置

## 技术支持

如有问题或建议，请通过以下方式联系：
- 插件作者：VanillaNahida
- GitHub仓库：https://github.com/VanillaNahida/astrbot_plugin_group_aip_review