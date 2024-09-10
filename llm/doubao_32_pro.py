import os.path

import volcenginesdkcore
import volcenginesdkark
from volcenginesdkcore.rest import ApiException
from volcenginesdkarkruntime import Ark

from utils.exceptions import ModelConfigNotFoundException
from llm.llm import LLM
from utils.utils import read_yamlfile
from utils.exceptions import ModelConfigNotFoundException, ApiCallException


class Doubao32Pro(LLM):
    def __init__(self, model_name='doubao-32-pro', system_prompt=""):
        """ChatGPT模型

        Args:
            model_name (str): 模型名称，默认为gpt-4-1106-preview
            system_prompt (str): 模型的系统提示
        """
        super().__init__()
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.api_config = self.__read_config()
        self.ak = self.api_config['ak']
        self.sk = self.api_config['sk']
        self.apikey = self.api_config.get('apikey', None)
        self.region = self.api_config['region']
        self.endpoint = self.api_config['endpoint']
        self.baseurl = self.api_config['baseurl']
        self.messages = [{'role':'system','content':self.system_prompt}]

    def completion(self, message, retry=False):
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
            response = self.__get_completion(self.messages, self.model_name)
            self.messages.append({"role":"assistant", "content": response})
            # print(f"response:{response}")
            return response
        except Exception as e:
            print(f"doubao-32-pro error:{e}")
    
    def embedding(self, query):
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = self.ak
        configuration.sk = self.sk
        configuration.region = self.region
        ENDPOINT_ID = self.endpoint
        #BASE_URL = "https://ml-maas-api.bytedance.net"
        BASE_URL = self.baseurl
        # set default configuration
        if self.apikey is not None:
             try:
                client = Ark(api_key=self.apikey, base_url=BASE_URL)
                emb = client.embeddings.create(
                    model=ENDPOINT_ID,
                    input=query,
                    encoding_format='float',
                    user='sunzhengping',
                    timeout=10
                )
                return emb
             except ApiException as e:
                raise ApiCallException(f"call api error:{e}")
        else:
            volcenginesdkcore.Configuration.set_default(configuration)

            # use global default configuration
            api_instance = volcenginesdkark.ARKApi()
            get_api_key_request = volcenginesdkark.GetApiKeyRequest(
                duration_seconds=30*24*3600,
                resource_type="endpoint",
                resource_ids=[
                    ENDPOINT_ID
                ],
            )

            try:
                resp = api_instance.get_api_key(get_api_key_request)
                client = Ark(api_key=resp.api_key, base_url=BASE_URL)
                emb = client.embeddings.create(
                    model=ENDPOINT_ID,
                    input=query,
                    encoding_format='float',
                    user='sunzhengping',
                    timeout=10
                )
                return emb
            except ApiException as e:
                raise ApiCallException(f"call api error:{e}")

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
        pass
    
    def __read_config(self):
        """
        从yaml配置文件中读取model配置
        """
        config_file = read_yamlfile("llm/model_config.yaml")[self.model_name]['config_file']

        if config_file is None : 
            raise ModelConfigNotFoundException(f"{self.model_name}'config_file is not ready")
        
        config = read_yamlfile(config_file)[self.model_name]
        
        # config中要包含ak, sk, region, edpoint, baseurl
        needs = ['region','endpoint','baseurl']
        if 'apikey' not in config:
            needs+=['ak','sk']
        for need in needs:
            if need not in config:
                raise ModelConfigNotFoundException(f"{self.model_name}'{need} is not ready")
        
        return config

    def __get_completion(self, messages, model='doubao-32-pro'):
        if (model=='doubao-32-pro'):
            configuration = volcenginesdkcore.Configuration()
            configuration.ak = self.ak
            configuration.sk = self.sk
            configuration.region = self.region
            ENDPOINT_ID = self.endpoint
            #BASE_URL = "https://ml-maas-api.bytedance.net"
            BASE_URL = self.baseurl
            # set default configuration
            volcenginesdkcore.Configuration.set_default(configuration)
            if self.apikey is not None:
                api_key = self.apikey
            else:
                # use global default configuration
                api_instance = volcenginesdkark.ARKApi()
                get_api_key_request = volcenginesdkark.GetApiKeyRequest(
                    duration_seconds=30*24*3600,
                    resource_type="endpoint",
                    resource_ids=[
                        ENDPOINT_ID
                    ],
                )
                api_key = api_instance.get_api_key(get_api_key_request).api_key

            try:
                client = Ark(api_key=api_key, base_url=BASE_URL)
                completion = client.chat.completions.create(
                    model=ENDPOINT_ID,
                    messages=messages,
                )
                return completion.choices[0].message.content
            except ApiException as e:
                raise ApiCallException(f"call api error:{e}")
