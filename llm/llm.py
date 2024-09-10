class LLM:
    """
    所有LLM模型的父类，定义它们都需要实现的接口，以便于统一调用
    """

    def __init__(self):
        pass

    def completion(self, message):
        """
        模型推理

        Args:
            message (str): 输入的文本

        Returns:
            str: 模型推理结果
        """
        pass

    def clear_history(self):
        """
        清空历史信息
        """
        pass

    def delete_last_message(self):
        """
        删除对话上下文中的上一个问答对
        """
        pass

    def token_sizeof_history(self):
        """
        获取历史信息的token数量
        """
        pass