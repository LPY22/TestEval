import openai
import time

from llm.llm import LLM
from utils.utils import read_yamlfile
from utils.exceptions import ModelConfigNotFoundException,ApiKeyIncorrectException,FileNotFoundException

class ChatGPT(LLM):
    def __init__(self, model_name='gpt-4-0125-preview', system_prompt=""):
        """ChatGPT模型

        Args:
            model_name (str): 模型名称，默认为gpt-4-1106-preview
            system_prompt (str): 模型的系统提示
        """
        super().__init__()
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.__read_config()
        self.ak=self.__get_api_key()
        self.messages = [{'role':'system','content':self.system_prompt}]
        self.current_token_size = 0

    def completion(self, message,retry=False):
        """
        模型推理

        Args:
            message (str): 输入的文本

        Returns:
            str: 模型推理结果
        """
        if not retry:
            self.messages.append({"role":"user","content":message})
        try:
            response, _, prompt_token,answer_token = self.__get_completion(self.messages,self.model_name)
            self.current_token_size += prompt_token
            self.current_token_size += answer_token
            self.messages.append({"role":"assistant","content":response})
            # print(f"response:{response}")
            return response
        except openai.RateLimitError:
            print("达到qpm，睡眠15秒")
            time.sleep(15)
            return self.completion(message,True)

    def clear_history(self):
        """
        清空历史信息
        """
        self.messages= [{"role":"system","content":self.system_prompt}]

    def delete_last_message(self):
        """
        删除对话上下文中的上一个问答对
        """
        if self.messages[-1]['role']=='assistant':
            self.messages=self.messages[:-2]
        elif self.messages[-1]['role']=='user':
            self.messages=self.messages[:-1]


    def token_sizeof_history(self):
        """
        获取历史信息的token数量
        """
        return self.current_token_size
    
    def __read_config(self):
        """
        从yaml配置文件中读取model配置
        """
        config = read_yamlfile(".//llm/model_config.yaml")[self.model_name]

        if config is None : 
            raise ModelConfigNotFoundException(f"{self.model_name}'config is not ready")
        self.__ak_dir = config["ak_dir"]
    
    def __get_api_key(self,line_number=0):
        try:
            with open(self.__ak_dir, 'r') as f:
                lines = f.readlines()
                if line_number > len(lines):
                    raise ApiKeyIncorrectException("api key文件中没有api key")
                else:
                    return lines[line_number-1].strip()
        except FileNotFoundError as e:
            raise FileNotFoundException(f"ak文件不存在:{self.__ak_dir}")
        
    def __get_completion(self,messages,model='gpt-4-1106-preview'):
        if (model=='gpt-4-0125-preview'):
            client = openai.AzureOpenAI(
                azure_endpoint="https://search.bytedance.net/gpt/openapi/online/v2/crawl",
                api_version="2023-07-01-preview",
                api_key=self.ak
            )
            completion = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=messages,
                temperature=0.5,
            )
            return (completion.choices[0].message.content,completion.choices[0].finish_reason,completion.usage.prompt_tokens,completion.usage.completion_tokens)
        elif (model=='gpt-4o-2024-05-13'):
            client = openai.AzureOpenAI(
                azure_endpoint="https://search-va.byteintl.net/gpt/openapi/online/v2/crawl",
                api_version="2023-03-15-preview",
                api_key=self.ak
            )
            completion = client.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=messages,
                temperature=0.5,
            )
            return (completion.choices[0].message.content,completion.choices[0].finish_reason,completion.usage.prompt_tokens,completion.usage.completion_tokens)