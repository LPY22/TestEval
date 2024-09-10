from llm.llm import LLM
from utils.exceptions import NotSupportedModelException

class Chatter:
    """
    基础的Chatter类，作为通用的中间层用于接入不同的llm模型
    model : str 模型名称
    client: 模型客户端，用于调用模型
    """
    def __init__(self, model, system_prompt = ""):
        self.model = model
        self.client = self.__get_cilent_by_model(self.model, system_prompt=system_prompt)
    
    def chat(self, message):
       # print(f"self.client.messages\n{self.client.messages}")
        return self.client.completion(message)
    
    def embedding(self, message):
        return self.client.embedding(message)

    def delete_last_message(self):
        """
        删除对话上下文中的上一个问答对
        """
        self.client.delete_last_message()

    def clear(self):
        self.client.clear_history()

    def __get_cilent_by_model(self, model,system_prompt = "") :
        '''
        返回LLM类模型实例
        '''
        if model == 'doubao-32-pro':
            from . import doubao_32_pro
            return doubao_32_pro.Doubao32Pro(model_name=model, system_prompt=system_prompt)
        # if model == 'sus-chat-34b':
        #     from . import sus_chat_34b
        #     return sus_chat_34b.SusChat34b()
        # elif model == 'gpt-4-0125-preview':
        #     from . import chat_gpt
        #     return chat_gpt.ChatGPT(model_name=model,system_prompt=system_prompt)
        elif model == 'gpt-4o-2024-05-13':
            from . import chat_gpt
            return chat_gpt.ChatGPT(model_name=model,system_prompt=system_prompt)
        # elif model =='qwen-14b-chat':
        #     from . import qwen_14b_chat
        #     return qwen_14b_chat.Qwen14bChat(system_prompt)
        # elif model == 'codegemma-7b-it':
        #     from . import codegemma_7b_it
        #     return codegemma_7b_it.Codegemma7bIt()
        # elif model == 'hermes-2-pro-mistral-7b':
        #     from . import hermes_2_pro_mistral_7b
        #    return hermes_2_pro_mistral_7b.Hermes2ProMistral7b(system_prompt)
        
        else :
           raise NotSupportedModelException(f'{model} not supported') 
