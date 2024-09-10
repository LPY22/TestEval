from fontTools.ttLib.tables.ttProgram import instructions

from llm.chatter import Chatter
from coder.coder import Coder
from utils.utils import response_format_for_send, check_files_in_response_and_return_absolute_paths, print_colored_text
from llm.tool_agent import ToolAgent
from utils.utils import read_latest_csv,read_csv_first_header
import pandas as pd
import numpy as np
import os
import glob


class PainterAgent(ToolAgent):
    DEFAULT_PROMPR_OP_INS = """You are an AI programming assistant. Follow the user's requirements carefully and to the letter.\
        You will need to write a PYTHON statement to process the data user need. Make sure your response only contains PYTHON code. Write texts in CHINESE. The font is been set, you don't need to worry about that.
        Code below is already executed:
        import matplotlib
        from matplotlib.font_manager import FontProperties
        from matplotlib import font_manager
        font_path = 'font/SourceHanSansSC-Normal-2.otf'  
        font_manager.fontManager.addfont(font_path) 
        font_prop = FontProperties(fname=font_path)
        matplotlib.rcParams['font.sans-serif'] = [font_prop.get_name()] 
        matplotlib.rcParams['axes.unicode_minus'] = False 
        """
    DEFAULT_PROMPR_PD_INS = """
        You are an AI programming assistant. Follow the user's requirements carefully and to the letter.
        You will need to change the PYTHON code to satisfy the requirements user need. Make sure your response only contains PYTHON code. Write texts in CHINESE.
        """
    history = []

    painter = None

    opt_painter = None

    file_names = None

    file_arg = None

    model_name = "doubao-32-pro"
    align_user_intent_chatter = None

    def __init__(self,info, painter_prompt: str = None, optimal_prompt: str = None, model_name: str = None, file_args:dict = None):
        super().__init__(info)
        if painter_prompt:
            self.DEFAULT_PROMPR_PD_INS = painter_prompt
        if optimal_prompt:
            self.DEFAULT_PROMPR_OP_INS = optimal_prompt
        if model_name:
            self.model_name = model_name
        for key in file_args:
            if file_args[key] is not None:
                self.file_arg = (key,file_args[key])
        self.painter = Coder(Chatter(model=self.model_name,system_prompt = self.DEFAULT_PROMPR_PD_INS))
        self.opt_painter = Coder(Chatter(model=self.model_name,system_prompt=self.DEFAULT_PROMPR_OP_INS))
        self.align_user_intent_chatter = Chatter(model=self.model_name)

    def work(self, instruictions,args:dict=None, preprocess=True, rag=False, type:str=None, opt_next=False,):
        global header, csv_content, csv_file_path
        dir_path = os.path.dirname(os.path.abspath(__file__))
        if self.file_arg[0] == "path":
            csv_file_path = read_latest_csv()
            # 打开文件，读取前5行内容，并将其存储在一个字符串变量中
            csv_content_lines = []
            try:
                import csv
                with open(csv_file_path, 'r', encoding='utf-8') as file:
                    header = read_csv_first_header(file = file)
                    for _ in range(5):
                        line = file.readline()
                        # 如果读取到了文件末尾，readline()会返回空字符串
                        print(line)
                        if not line:
                            break
                        csv_content_lines.append(line)


                # 将读取的行连接成一个字符串
                csv_content = ''.join(csv_content_lines)
            except Exception as e:
                return f"csv文件读取失败，请检查文件路径是否正确，错误信息为：{str(e)}"
        elif self.file_arg[0] == "content":
            #先写文件，再读文件
            df = self.file_arg[1]
            header  = list(df.columns)
            csv_content = df.iloc[:5,:].to_string()
            print(header)
            print(csv_content)

            csv_file_path = os.path.join(dir_path, "files", self.info['tableName'])
            if not os.path.exists(csv_file_path):
                self.file_arg[1].to_csv(csv_file_path, index=False)
        
        # instruction = self.align_user_intent(args['instruction'], header=header)
        instruction = instruictions.pop(0)
        image_path =  os.path.join(dir_path,"images_gpt")

        # print(f"修改后的图片指令为：{instruction}")

        DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER = f"""
    用户要求:
    {instruction}
    csv文件路径：
    {csv_file_path}
    csv数据列有：
    {header}
    csv数据前几行为：
    {csv_content}
    你的任务是根据用户的要求使用python进行图表绘制。将结果保存在png文件中。

    [表结构选择]
    绘制图表时，请确保图表的横轴和纵轴的标签和图例清晰。
    根据数据的的范围合理的设置x,y轴的范围区间，保证图像信息的展示在合理的位置，同时比例合适。
    根据任务的要求和数据展示的目的选择适合该的图表类型，如折线图、柱状图、饼图等，也可以在一张图中使用多种类型如折线加柱状图。
    如果一种图表中数据较多，可以将其按照一定的规则分开，使得表达更加清晰。


    [颜色设置]
    请使用”tab20c“色组进行绘图，该色组颜色排序为[0:深蓝, 1:蓝色, 2:浅蓝, 3:超浅蓝, 4:深橙, 5:橙色, 6:浅橙, 7:超浅橙, 8:深绿, 9:绿色, 10:浅绿, 11:超浅绿, 12:深紫, 13:紫色, 14:浅紫, 15:超浅紫, 16:深灰, 17:灰色, 18:浅灰色, 19:超浅灰]
    你可以通过执行`colors = plt.get_cmap('tab20c')` 并使用索引`color=colors(0))`来确定颜色
    请合理使用不同颜色保证图片的可读性，以保证可读性为前提，如果单张图片无法保证可读性，可以绘制多张图。

    [注意]
    注意:代码中字符串如果有中文英文数字混合直接相连，不加空格。正确格式：English英文，123数字。

    [图片保存设置]
    文件命名使用英文,末尾加个时间戳用于区分
    python代码的最后一行为：
    print("图表绘制完成，生成的图片保存在 {image_path}/XXXXX.png")
        """

        # logger.log_info(DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER)

        code, response = self.painter.coder(DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER, "python")
        if opt_next:
            response = self.graphic_chart_painter_optimize(code, response, instructions,header)
        
        self.painter.chatter.clear()   

        return response
    def get_history(self):
        """
        将历史对话提取成字符串格式
        """
        history = ""
        # print(f"[历史对话]\n{history_list}")
        if len(self.history) == 0:
            return ""
        else:
            # 将历史对话提取成字符串格式
            for i in range(len(self.history)):
                history += f"{self.history[i]['role']}: {self.history[i]['content']}\n"
            return history
        
    def clear_history(self):
        self.history.clear()
    
    def align_user_intent(self,instruction: str, header: str) :
        """
        对齐用户的意图，将用户的问题转化为一个清晰准确的问题。
        每次迭代都是一个多轮对话的过程，通过对话来将一个抽象的问题转化为一个清晰准确的问题。
        """
        ALIGN_USER_INTENT_PROMPT_FRONT = f"""
        你是一个能够洞悉用户意图并且擅长总结的专家，你需要根据用户的[当前意图]、[历史]和[数据]来对齐用户的意图。
        依据[历史]中用户的偏好，对[当前意图]进行调整，使其更加符合用户的偏好。
        [历史]可能为空，这时候直接返回当前意图即可。

        [历史]
        """
        ALIGN_USER_INTENT_PROMPT_BACK = f"""

        [当前意图]
        {instruction}

        回答调整后的[当前意图]。
        """
    
        ALIGN_USER_INTENT_PROMPT = ALIGN_USER_INTENT_PROMPT_FRONT + self.get_history() + ALIGN_USER_INTENT_PROMPT_BACK
        return self.align_user_intent_chatter.chat(ALIGN_USER_INTENT_PROMPT)

    def graphic_chart_painter_optimize(self, code, response,instructions,header):
        # 示例 response 字符串
        # 调用函数并打印结果
        instruction = instructions.pop(0)
        instruction = self.align_user_intent(instruction, header=header)
        DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER_OPTIMIZE = f"""
    代码字段是用户使用matplotlib进行绘制的python代码，
    用户可能对代码中数据的聚合方式，表的形式以及颜色的表示形式等方面不满意，
    你的任务是根据用户新的需求修改python代码，使其更加符合用户的需求。
    注意不要在中英文/中文和数字之间加空格，正确的输出格式：English英文，123数字。

    你所使用的颜色是”tab20c“色组，其中包括
    [0:深蓝, 1:蓝色, 2:浅蓝, 3:超浅蓝, 4:深橙, 5:橙色, 6:浅橙, 7:超浅橙, 8:深绿, 9:绿色, 10:浅绿, 11:超浅绿, 12:深紫, 13:紫色, 14:浅紫, 15:超浅紫, 16:深灰, 17:灰色, 18:浅灰色, 19:超浅灰]
    你可以通过执行`colors = plt.get_cmap('tab20c')` 并使用索引`color=colors(0))`来确定颜色

    用户要求:
    {instruction}

    代码:
    {code}
    """            
                # logger.log_info(DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER_OPTIMIZE)
        #         self.history.append({'role': 'user', 'content': requirement})
        #         # print(DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER_OPTIMIZE)
        #         code, response = self.opt_painter.coder(DEFAULT_PROMPT_GRAPHIC_CHART_PAINTER_OPTIMIZE, "python")
        #     else:
        #         continue
        # self.opt_painter.chatter.clear()
        # return response

if __name__ == '__main__':
    # chatbi = ChatBI(token='kgqi5rc3cawnf2rwd2yw2zxba36e0bze', username="guoshaoxiong", dataset_id=3028770)
    # data = chatbi.completion("依据BUG创建时间提取出2024年5月的所有BUG信息，包含'BUG创建时间'、'报告人'、'bug总数'和'有效bug数'，计算每个报告人的有效bug数占比，并按照有效bug数占比从大到小排序。")
    # print(data)

    # painter_agent = PainterAgent()
    from fakeData import df
    file_args,info = dict(),dict()
    file_args["content"] = df
    info["tableName"] = "projectTest_table.csv"
    # print(df)
    painter_agent = PainterAgent(info=info,file_args=file_args,model_name="doubao-32-pro")
    # painter_agent = PainterAgent(info=info,file_args=file_args,model_name="gpt-4o-2024-05-13")
    args = {
        "instruction": "请根据数据绘制一个折线图，横轴为日期，并将图表保存到本地。",
    }
    instructions = ["请根据数据绘制一个折线图"]
    file_path = os.path.dirname(os.path.abspath(__file__))
    print(file_path)
    # for i in range(3):
    painter_agent.work(instructions)
        # instructions = ["请根据数据绘制一个折线图"]