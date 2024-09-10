# 后续讨论如何处理异常
class AgentException(Exception):
    """Agent的基本异常类
    message : str
    """

    def __init__(self, message : str):
        super().__init__(message)
        self.message = message

class NotSupportedModelException(AgentException):
    """不支持的模型"""

class MissRequiredKeyInJson(AgentException):
    """"模型返回json中缺少约定的键"""    

class WrongOutputFormatException(AgentException):
    """模型返回的json格式不正确"""
    
class ApiKeyIncorrectException(AgentException):
    """调用api的api key错误"""
    
class ApiCallException(AgentException):
    """调用api时报错"""

class MemoryNotHealthException(AgentException):
    """记忆不正确"""

class ModelNotRunException(AgentException):
    """模型未启动，即没有调用run方法"""
    def __init__(self, message : str ):
        super().__init__(message)
        self.message = message

class FileNotFoundException(AgentException):
    """文件未能找到"""

class ModelConfigNotFoundException(FileNotFoundException):
    """模型的config文件未配置"""

class CoreTemplateNotFoundException(FileNotFoundException):
    """core的模板未找到"""

class CodeFormalErrorException(AgentException):
    """代码提取后为空"""

class CodeExecException(AgentException):
    """代码执行时报错"""

class ChatBIChatException(AgentException):
    """询问ChatBI时报错"""

class WaitingTimeOutException(AgentException):
    """等待超时"""

class ExtractDataEmptyError(AgentException):
    """取数结果为空"""
    
class ForceEndGetMessageException(Exception):
    """强制关闭get_msg轮询"""


class ProcessDataError(AgentException):
    """数据处理失败"""