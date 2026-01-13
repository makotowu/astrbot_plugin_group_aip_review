import asyncio
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star, register

# 百度内容审核API集成类
class BaiduAuditAPI:
    """百度内容审核API封装类（使用官方SDK）"""
    
    def __init__(self, api_key: str, secret_key: str, strategy_id: str = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.strategy_id = strategy_id
        
        # 初始化百度内容审核客户端
        try:
            from aip import AipContentCensor
            # 百度SDK需要三个参数：appId, apiKey, secretKey
            # 我们没有appId，所以使用空字符串
            self.client = AipContentCensor("", api_key, secret_key)
            logger.info("百度内容审核客户端初始化成功")
        except ImportError:
            logger.error("未安装baidu-aip包，请运行: pip install baidu-aip")
            self.client = None
        except Exception as e:
            logger.error(f"百度内容审核客户端初始化失败: {e}")
            self.client = None
    
    async def text_censor(self, text: str) -> Dict:
        """文本内容审核"""
        if not self.client:
            return {"error": "百度内容审核客户端未初始化"}
        
        try:
            # 由于百度SDK是同步的，使用线程池执行异步操作
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            def sync_text_censor():
                return self.client.textCensorUserDefined(text)
            
            with ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(executor, sync_text_censor)
            
            return result
            
        except Exception as e:
            logger.error(f"文本审核API调用异常: {e}")
            return {"error": f"API调用异常: {e}"}
    
    async def image_censor(self, image_url: str) -> Dict:
        """图片内容审核"""
        if not self.client:
            return {"error": "百度内容审核客户端未初始化"}
        
        try:
            # 下载图片
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            import httpx
            
            async def download_image():
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    if response.status_code != 200:
                        raise Exception("图片下载失败")
                    return response.content
            
            image_data = await download_image()
            
            # 使用百度SDK进行图片审核，由于百度SDK是同步的，使用线程池执行异步操作
            def sync_image_censor():
                return self.client.imageCensorUserDefined(image_data)
            
            with ThreadPoolExecutor() as executor:
                result = await asyncio.get_event_loop().run_in_executor(executor, sync_image_censor)
            
            return result
            
        except Exception as e:
            logger.error(f"图片审核API调用异常: {e}")
            return {"error": f"API调用异常: {e}"}

# 审核结果解析器
class AuditResultParser:
    """审核结果解析器"""
    
    @staticmethod
    def parse_text_result(result: Dict) -> Tuple[str, str]:
        """解析文本审核结果"""
        if "error" in result:
            return "审核失败", result["error"]
        
        conclusion = result.get("conclusion", "")
        data = result.get("data", [])
        
        if conclusion == "合规":
            return "合规", ""
        elif conclusion == "不合规":
            reasons = []
            for item in data:
                if "msg" in item:
                    reasons.append(item["msg"])
            return "不合规", ", ".join(reasons)
        elif conclusion == "疑似":
            return "疑似", "内容疑似违规，需要人工审核"
        else:
            return "审核失败", "未知审核结果"
    
    @staticmethod
    def parse_image_result(result: Dict) -> Tuple[str, str]:
        """解析图片审核结果"""
        if "error" in result:
            return "审核失败", result["error"]
        
        conclusion = result.get("conclusion", "")
        data = result.get("data", [])
        
        if conclusion == "合规":
            return "合规", ""
        elif conclusion == "不合规":
            reasons = []
            for item in data:
                if "msg" in item:
                    reasons.append(item["msg"])
                elif "type" in item:
                    reasons.append(item["type"])
            return "不合规", ", ".join(reasons)
        elif conclusion == "疑似":
            return "疑似", "图片疑似违规，需要人工审核"
        else:
            return "审核失败", "未知审核结果"

# 违规记录管理器
class ViolationManager:
    """违规记录管理器"""
    
    def __init__(self):
        self.user_violations = defaultdict(list)  # 用户违规记录
        self.group_violations = defaultdict(list)  # 群组违规记录
    
    def add_violation(self, group_id: str, user_id: str, violation_type: str):
        """添加违规记录"""
        timestamp = time.time()
        
        # 用户违规记录
        self.user_violations[(group_id, user_id)].append(timestamp)
        
        # 群组违规记录
        self.group_violations[group_id].append(timestamp)
        
        # 清理过期记录
        self._cleanup_expired_records()
    
    def get_user_violation_count(self, group_id: str, user_id: str, time_window: int) -> int:
        """获取用户在指定时间窗口内的违规次数"""
        key = (group_id, user_id)
        if key not in self.user_violations:
            return 0
        
        cutoff_time = time.time() - time_window
        violations = [ts for ts in self.user_violations[key] if ts > cutoff_time]
        return len(violations)
    
    def get_group_violation_count(self, group_id: str, time_window: int) -> int:
        """获取群组在指定时间窗口内的违规次数"""
        if group_id not in self.group_violations:
            return 0
        
        cutoff_time = time.time() - time_window
        violations = [ts for ts in self.group_violations[group_id] if ts > cutoff_time]
        return len(violations)
    
    def _cleanup_expired_records(self):
        """清理过期记录（24小时前的记录）"""
        cutoff_time = time.time() - 86400  # 24小时
        
        # 清理用户记录
        for key in list(self.user_violations.keys()):
            self.user_violations[key] = [ts for ts in self.user_violations[key] if ts > cutoff_time]
            if not self.user_violations[key]:
                del self.user_violations[key]
        
        # 清理群组记录
        for group_id in list(self.group_violations.keys()):
            self.group_violations[group_id] = [ts for ts in self.group_violations[group_id] if ts > cutoff_time]
            if not self.group_violations[group_id]:
                del self.group_violations[group_id]

# 主插件类
@register(
    "astrbot_plugin_group_aip_review",
    "VanillaNahida",
    "基于百度内容审核API的群聊内容安全审查插件",
    "1.0.0"
    )
class GroupAipReviewPlugin(Star):
    """基于百度内容审核API的群聊内容安全审查插件"""
    
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.baidu_api = None
        self.audit_parser = AuditResultParser()
        self.violation_manager = ViolationManager()
        
        # 初始化百度API
        self._init_baidu_api()
    
    def _init_baidu_api(self):
        """初始化百度API"""
        baidu_config = self.config.get("baidu_audit", {})
        api_key = baidu_config.get("api_key")
        secret_key = baidu_config.get("secret_key")
        strategy_id = baidu_config.get("strategy_id")
        
        if not api_key or not secret_key:
            logger.warning("百度API配置不完整，插件将无法正常工作")
            return
        
        self.baidu_api = BaiduAuditAPI(api_key, secret_key, strategy_id)
        logger.info("百度内容审核API初始化完成")
    
    def get_group_config(self, group_id: str) -> Dict:
        """获取群组配置"""
        disposal_config = self.config.get("disposal", {})
        default_config = disposal_config.get("default", {})
        group_custom = disposal_config.get("group_custom", [])
        
        # 获取群组自定义配置（template_list 格式）
        group_config = default_config.copy()
        rule_id = default_config.get("rule_id", "default")
        
        if group_custom and isinstance(group_custom, list):
            # 遍历所有群配置，查找匹配的群
            for custom_config in group_custom:
                if custom_config.get("group_id") == group_id:
                    # 更新配置（排除 group_id 和 __template_key）
                    for key, value in custom_config.items():
                        if key not in ["group_id", "__template_key"]:
                            group_config[key] = value
                    # 更新规则ID
                    if "rule_id" in custom_config:
                        rule_id = custom_config["rule_id"]
                    break
        
        return group_config
    
    async def _send_notification(self, group_id: str, message: str):
        """发送通知消息"""
        try:
            group_config = self.get_group_config(group_id)
            notify_group_id = group_config.get("notify_group_id")
            rule_id = group_config.get("rule_id", "default")
            
            if notify_group_id:
                # 获取所有平台实例
                from astrbot.api.platform import Platform
                platforms = self.context.platform_manager.get_insts()
                
                # 遍历所有平台，找到支持发送群消息的平台
                for platform in platforms:
                    client = platform.get_client()
                    if hasattr(client, 'send_group_msg'):
                        # 在消息中添加规则ID信息
                        notification_with_rule = f"{message}\n规则ID: {rule_id}"
                        await client.send_group_msg(
                            group_id=int(notify_group_id),
                            message=notification_with_rule
                        )
                        logger.info(f"发送通知到群 {notify_group_id}: {notification_with_rule}")
                        break
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    async def _send_private_message(self, user_id: str, message: str):
        """发送私聊消息"""
        try:
            # 获取所有平台实例
            from astrbot.api.platform import Platform
            platforms = self.context.platform_manager.get_insts()
            
            # 遍历所有平台，找到支持发送私聊消息的平台
            for platform in platforms:
                client = platform.get_client()
                if hasattr(client, 'send_private_msg'):
                    await client.send_private_msg(
                        user_id=int(user_id),
                        message=message
                    )
                    logger.info(f"发送私聊消息给用户 {user_id}: {message}")
                    break
        except Exception as e:
            logger.error(f"发送私聊消息失败: {e}")
    
    async def _handle_audit_result(self, event: AstrMessageEvent, audit_type: str, result: str, reason: str):
        """处理审核结果"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        if not group_id:  # 私聊消息
            return
        
        group_config = self.get_group_config(group_id)
        
        if result == "合规":
            # 合规，不执行任何操作
            logger.debug(f"消息审核通过: {audit_type} - 用户 {user_id} 在群 {group_id}")
            
        elif result == "不合规":
            # 不合规，立即撤回消息并记录违规
            await self._handle_non_compliant(event, audit_type, reason, group_config)
            
        elif result == "疑似":
            # 疑似违规，发送通知
            await self._handle_suspicious(event, audit_type, reason, group_config)
            
        elif result == "审核失败":
            # 审核失败，通知Bot主人
            await self._handle_audit_failure(event, audit_type, reason, group_config)
    
    async def _handle_non_compliant(self, event: AstrMessageEvent, audit_type: str, reason: str, group_config: Dict):
        """处理不合规内容"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        # 记录违规
        self.violation_manager.add_violation(group_id, user_id, audit_type)
        
        # 撤回消息
        await self._recall_message(event)
        
        # 发送通知
        rule_id = group_config.get("rule_id", "default")
        notification_msg = f"⚠️ 检测到违规内容\n类型: {audit_type}\n用户: {user_id}\n原因: {reason}\n规则ID: {rule_id}"
        await self._send_notification(group_id, notification_msg)
        
        # 检查是否需要禁言或踢人
        await self._check_and_apply_punishment(event, group_config)
    
    async def _handle_suspicious(self, event: AstrMessageEvent, audit_type: str, reason: str, group_config: Dict):
        """处理疑似违规内容"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        rule_id = group_config.get("rule_id", "default")
        
        # 发送通知给管理员核实
        notification_msg = f"❓ 检测到疑似违规内容\n类型: {audit_type}\n用户: {user_id}\n原因: {reason}\n规则ID: {rule_id}\n请管理员核实处理"
        await self._send_notification(group_id, notification_msg)
    
    async def _handle_audit_failure(self, event: AstrMessageEvent, audit_type: str, reason: str, group_config: Dict):
        """处理审核失败"""
        bot_owner_id = group_config.get("bot_owner_id")
        if bot_owner_id:
            # 通知Bot主人
            notification_msg = f"⚠️ 审核失败通知\n类型: {audit_type}\n原因: {reason}\n请检查API配置或网络连接"
            await self._send_private_message(bot_owner_id, notification_msg)
            logger.warning(f"审核失败，已通知Bot主人: {reason}")
    
    async def _recall_message(self, event: AstrMessageEvent):
        """撤回消息"""
        try:
            message_id = event.message_obj.message_id
            await event.bot.delete_msg(message_id=int(message_id))
            logger.info(f"撤回消息成功: {message_id}")
        except Exception as e:
            logger.error(f"撤回消息失败: {e}")
    
    async def _check_and_apply_punishment(self, event: AstrMessageEvent, group_config: Dict):
        """检查并应用惩罚措施"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        
        time_window = group_config.get("time_window", 300)
        
        # 检查单人违规次数
        user_violations = self.violation_manager.get_user_violation_count(group_id, user_id, time_window)
        single_threshold = group_config.get("single_user_violation_threshold", 3)
        
        if single_threshold > 0 and user_violations >= single_threshold:
            # 禁言用户
            mute_duration = group_config.get("mute_duration", 86400)
            rule_id = group_config.get("rule_id", "default")
            await self._mute_user(event, mute_duration)
            
            # 发送通知到通知群
            notification_msg = f"⚠️ 用户违规禁言通知\n群ID: {group_id}\n用户ID: {user_id}\n违规次数: {user_violations}次\n已禁言 {mute_duration // 3600} 小时，请管理员关注。\n规则ID: {rule_id}"
            await self._send_notification(group_id, notification_msg)
            
            # 检查是否需要踢人
            kick_threshold = group_config.get("kick_user_threshold", 5)
            if kick_threshold > 0 and user_violations >= kick_threshold and group_config.get("kick_user", False):
                await self._kick_user(event, group_config.get("is_kick_user_and_block", False))
        
        # 检查群组违规次数
        group_violations = self.violation_manager.get_group_violation_count(group_id, time_window)
        group_threshold = group_config.get("group_violation_threshold", 5)
        
        if group_threshold > 0 and group_violations >= group_threshold:
            # 开启全员禁言
            rule_id = group_config.get("rule_id", "default")
            await self._mute_all_members(event)
            
            # 在通知群@全体成员
            notification_msg = f"⚠️ 群内出现大量违规内容\n群ID: {group_id}\n违规次数: {group_violations}次\n已开启全员禁言，请管理员及时处理\n规则ID: {rule_id}"
            await self._send_notification(group_id, notification_msg)
    
    async def _mute_user(self, event: AstrMessageEvent, duration: int):
        """禁言用户"""
        try:
            await event.bot.set_group_ban(
                group_id=int(event.get_group_id()),
                user_id=int(event.get_sender_id()),
                duration=duration
            )
            logger.info(f"禁言用户成功: {event.get_sender_id()} {duration}秒")
        except Exception as e:
            logger.error(f"禁言用户失败: {e}")
    
    async def _kick_user(self, event: AstrMessageEvent, block: bool):
        """踢出用户"""
        try:
            group_id = event.get_group_id()
            user_id = event.get_sender_id()
            
            await event.bot.set_group_kick(
                group_id=int(group_id),
                user_id=int(user_id),
                reject_add_request=block
            )
            logger.info(f"踢出用户成功: {user_id}, 是否拉黑: {block}")
            
            # 发送通知到通知群
            notification_msg = f"⚠️ 用户违规踢出通知\n群ID: {group_id}\n用户ID: {user_id}\n已踢出用户，是否拉黑: {'是' if block else '否'}\n请管理员关注"
            await self._send_notification(group_id, notification_msg)
        except Exception as e:
            logger.error(f"踢出用户失败: {e}")
    
    async def _mute_all_members(self, event: AstrMessageEvent):
        """全员禁言"""
        try:
            await event.bot.set_group_whole_ban(
                group_id=int(event.get_group_id()),
                enable=True
            )
            logger.info(f"开启全员禁言成功: 群 {event.get_group_id()}")
        except Exception as e:
            logger.error(f"全员禁言失败: {e}")
    
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """消息事件监听"""
        # 检查是否为群聊消息
        group_id = event.get_group_id()
        if not group_id:
            return
        
        # 检查是否在白名单中
        enabled_groups = self.config.get("enabled_groups", [])
        if not enabled_groups or group_id not in enabled_groups:
            return
        
        # 检查百度API是否可用
        if not self.baidu_api:
            logger.warning("百度API未初始化，跳过审核")
            return
        
        # 提取消息内容
        message_text = event.message_str
        image_urls = []
        
        # 提取图片URL
        for component in event.get_messages():
            if isinstance(component, Image) and component.url:
                image_urls.append(component.url)
        
        # 文本审核
        if self.config.get("enable_text_censor", True) and message_text:
            await self._audit_text(event, message_text)
        
        # 图片审核
        if self.config.get("enable_image_censor", True) and image_urls:
            for image_url in image_urls:
                await self._audit_image(event, image_url)
    
    async def _audit_text(self, event: AstrMessageEvent, text: str):
        """文本审核"""
        try:
            result = await self.baidu_api.text_censor(text)
            audit_result, reason = self.audit_parser.parse_text_result(result)
            
            logger.info(f"文本审核结果: {audit_result} - 原因: {reason}")
            await self._handle_audit_result(event, "文本", audit_result, reason)
            
        except Exception as e:
            logger.error(f"文本审核异常: {e}")
    
    async def _audit_image(self, event: AstrMessageEvent, image_url: str):
        """图片审核"""
        try:
            result = await self.baidu_api.image_censor(image_url)
            audit_result, reason = self.audit_parser.parse_image_result(result)
            
            logger.info(f"图片审核结果: {audit_result} - 原因: {reason}")
            await self._handle_audit_result(event, "图片", audit_result, reason)
            
        except Exception as e:
            logger.error(f"图片审核异常: {e}")
    
    async def initialize(self):
        """插件初始化"""
        logger.info("群聊内容安全审查插件初始化完成")
    
    async def terminate(self):
        """插件销毁"""
        logger.info("群聊内容安全审查插件已卸载")