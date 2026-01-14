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

1. 在插件市场中搜索插件 `astrbot_plugin_group_aip_review` 或 `群消息内容安全审核插件`
   或者将本仓库地址复制后，在插件管理页面输入链接安装
2. 安装好后，需要在 WebUI 的平台日志页面右上角，安装依赖 `baidu-aip` 
3. 安装好后打开插件配置，配置百度内容审核API参数、策略ID和启用群号（详见配置说明）

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

## 技术支持

如有问题或建议，请通过以下方式联系：
- 插件作者：VanillaNahida
- GitHub仓库：https://github.com/VanillaNahida/astrbot_plugin_group_aip_review