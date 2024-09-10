

class ToolAgent:
    """
    工具Agent的父类，用于定义工具Agent的基本属性和方法
    简单实现以支持应用，后续进行重构扩展
    """
    def __init__(self,info):
        self.info = info
        # pass


    def work(self, args: dict, preprocess=True, rag=False,postprocess=True ,type: str=None) :
        """
        工具Agent的工作方法，根据用户问题和预处理结果，返回工具Agent的响应
        """
        pass