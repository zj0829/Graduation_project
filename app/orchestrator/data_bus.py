import asyncio

class DataBus:
    def __init__(self):
        # 订阅者字典
        self.subscribers = {}
    
    async def publish(self, topic, message):
        """
        发布消息
        
        Args:
            topic (str): 主题
            message (dict): 消息内容
        """
        # 检查是否有订阅者
        if topic in self.subscribers:
            # 通知所有订阅者
            for subscriber in self.subscribers[topic]:
                try:
                    await subscriber(message)
                except Exception as e:
                    print(f"通知订阅者时出错: {e}")
    
    def subscribe(self, topic, callback):
        """
        订阅主题
        
        Args:
            topic (str): 主题
            callback (function): 回调函数
        """
        # 如果主题不存在，创建新的订阅者列表
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        # 添加订阅者
        self.subscribers[topic].append(callback)
    
    def unsubscribe(self, topic, callback):
        """
        取消订阅
        
        Args:
            topic (str): 主题
            callback (function): 回调函数
        """
        # 检查主题是否存在
        if topic in self.subscribers:
            # 移除订阅者
            if callback in self.subscribers[topic]:
                self.subscribers[topic].remove(callback)
    
    def get_subscribers(self, topic):
        """
        获取主题的订阅者
        
        Args:
            topic (str): 主题
            
        Returns:
            list: 订阅者列表
        """
        return self.subscribers.get(topic, [])
    
    def get_all_topics(self):
        """
        获取所有主题
        
        Returns:
            list: 主题列表
        """
        return list(self.subscribers.keys())