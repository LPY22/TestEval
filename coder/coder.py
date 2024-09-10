import io
import sys
import subprocess
import os
import tempfile
import re

from llm.chatter import Chatter
from utils.utils import extract_sql_wrapped_content, extract_python_wrapped_content, \
    extract_content_between_braces, json_loads
from utils.exceptions import CodeFormalErrorException, MissRequiredKeyInJson, ExtractDataEmptyError


class Coder:
    MAX_DEBUG_TIME = 3
    DEFAULT_DEBUGGER_SYS_PROMPT = """
You are an AI programming assistant. Follow the user's requirements carefully and to the letter.
You will need to change the PYTHON code to satisfy the requirements user need. Make sure your response only contains PYTHON code. Write texts in CHINESE.
"""

    def __init__(self, chatter: Chatter):
        self.chatter = chatter
        self.debugger_chatter = Chatter('gpt-4o-2024-05-13', system_prompt=self.DEFAULT_DEBUGGER_SYS_PROMPT)
        self.__debug_try_time = 0

    def coder(self, prompt, code_type: str, is_debugger=True, code_str: str = None):
        # 限制coder尝试次数，所有次数都失败则将错误信息返回给core
        LIMIT_TIMES = 5
        times = 0
        self.__debug_try_time = 0
        while True:
            try:
                times += 1
                print('Coder 工作中：编写代码')
                if not code_str:  # 如果没有传入code_str 则生成
                    code_str = self.chatter.chat(prompt)
                # self.logger.log_info('\n' + '*'*100)
                # self.logger.log_info('$Code$'*30)
                # self.logger.log_info(f"code_str : {code_str}")
                # self.logger.log_info('$Code$'*30)
                # self.logger.log_info('*'*100 + '\n')
                print('Coder 工作中：执行代码')
                exec_res = self.exec(code_str, code_type, is_debugger)
                print('Code 执行结束...')
                # while(1):
                #     instruction  = input(f"对图表的更多要求：")
                return code_str, exec_res
            # 如果提取代码错误，则重复多次
            # 其他错误，则直接返回给core
            except CodeFormalErrorException as e:
                print(f"CodeFormalErrorException: {str(e)}")
                # self.logger.log_error(f"exception : {e}")
                # 如果达到LIMTI_TIMES，则告知core，代码生成错误，请重新调用
                if times >= LIMIT_TIMES:
                    # self.logger.log_error(f"e: {str(e)}")
                    return code_str, "数据处理代码执行错误，请重新调用"
                self.chatter.delete_last_message()
                prompt = str(e)
            except Exception as e:
                # self.logger.log_error(f"exception : {e}")
                return code_str, f"an error occured {str(e)}"

    def debugger(self, code_str, error_message):
        """
        接收： 代码字符串，错误信息
        返回： 修改后的代码（如果有），是否进行了修复
        """
        # 构造一个提示信息，将错误信息传递给人工智能助手
        # self.logger.log_info(f"进入了 debugger程序，<code_str>: {code_str}\n<error_message>: {error_message}")
        self.__debug_try_time += 1
        if self.__debug_try_time > self.MAX_DEBUG_TIME:
            print("debug次数已用完")
            return "抱歉，debug次数已用完，未能成功执行代码", False
        print(f'Debugger 工作中...,当前次数为{self.__debug_try_time}')
        prompt = f"""
        你的任务是根据收到的代码和代码执行时的错误信息进行错误修复。
        代码：
        {code_str}
        错误信息：
        {error_message}

        你需要通过输出json来完成任务，输出时需要遵循下面的json格式。
        输出格式：
        {{
            "solution": "string, 只能是 修改代码 或者 命令行命令",
            "code": "string, 修改后的sql、python代码 或者 命令行命令。sql和python请使用 ```sql``` ```python```包裹，命令行命令请直接提供纯文本"
        }}
        """

        # 保证模型推理的结果是json格式
        while True:
            response_str = self.debugger_chatter.chat(prompt)
            json_content = extract_content_between_braces(response_str)
            try:
                if json_content is not None:
                    json_content = json_loads(json_content)

                    def json_is_ok(data):
                        # 检查最外层的键
                        if "solution" not in data or "code" not in data:
                            return False
                        # 如果所有键都存在，返回 True
                        return True

                    if not json_is_ok(json_content):
                        raise MissRequiredKeyInJson("模型返回json中缺少约定的键")
            except Exception as e:
                # 如果有错则重新提问
                # self.logger.error("Json parse failed in debugger!")
                # self.logger.error(e)
                self.debugger_chatter.delete_last_message()
                continue
            break
        # self.logger.debug(f"debugger response：{response_str}")

        # 检查修复建议是否包含命令行命令
        if "命令行命令" in json_content['solution']:
            # 提取命令行命令
            command = json_content['code']
            try:
                # 执行命令行命令
                result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # self.logger.debug(f"执行了命令行命令：，{command}，{result}")
                # 执行命令行命令进行修复后返回原代码重新尝试运行
                return code_str, True
            except subprocess.CalledProcessError as e:
                # 如果命令执行失败，直接返回原代码重新进行debug尝试
                # self.logger.error("debugger中命令行命令执行遇到了问题" + e)
                return code_str, False
        elif "修改代码" in json_content['solution']:
            # 返回修改后的代码
            return json_content['code'], True

    def exec(self, code_str, code_type: str, is_debugger):
        try:
            if code_type == 'sql':
                code_str = extract_sql_wrapped_content(code_str)
                if code_str is None:
                    raise CodeFormalErrorException("提供sql代码的格式错误，请使用如下格式：\n```sql\nyour code\n```")
                return self.__sql_exec(code_str)
            elif code_type == 'python':
                code_str = extract_python_wrapped_content(code_str)
                if code_str is None:
                    raise CodeFormalErrorException(
                        "提供python代码的格式错误，请使用如下格式：\n```python\nyour code\n```")
                return self.__python_exec(code_str)
        except Exception as e:
            print(f"Coder执行的错误命令为:{str(e)}")
            if is_debugger and self.__debug_try_time <= self.MAX_DEBUG_TIME:
                code_str, success = self.debugger(code_str, str(e))
                if success:
                    return self.exec(code_str, code_type, is_debugger)
            # 如果debug次数超出限制或者debug失败则返回错误信息
            # self.logger.log_error(f"{code_type} 代码执行错误为:\n{e}")
            raise e

    def __sql_exec(self, sql_code):
        try:
            if sql_code.startswith('```sql') and sql_code.endswith('```'):
                sql_code = sql_code[6:-3]
            # print(f"sql_code : \n{sql_code}")
            import sqlite3
            # 连接数据库
            conn = sqlite3.connect('/tools/database/test.db')
            # 创建游标
            cur = conn.cursor()
            # 执行 SQL 语句
            cur.execute(sql_code)
            # 获取查询结果
            rows = cur.fetchall()
            # 打印查询结果

            # 关闭游标和连接
            cur.close()
            conn.close()
            return rows
        except Exception as e:
            raise e

    def __python_exec(self, python_code):

        captured_output = io.StringIO()
        saved_stdout = sys.stdout
        try:
            if python_code.startswith('```python') and python_code.endswith('```'):
                python_code = python_code[9:-3]
            elif python_code.startswith('```python') and not python_code.endswith('```'):
                python_code = python_code[9:]

            HAN_FONT = """
import matplotlib
from matplotlib.font_manager import FontProperties
from matplotlib import font_manager
font_path = 'font/SourceHanSansSC-Normal-2.otf'  
font_manager.fontManager.addfont(font_path)
font_prop = FontProperties(fname=font_path)
matplotlib.rcParams['font.sans-serif'] = [font_prop.get_name()] 
matplotlib.rcParams['axes.unicode_minus'] = False 
"""
            python_code = HAN_FONT + python_code
            print(f"python code is : \n{python_code}")
            # 将 stdout 重定向到 StringIO 对象
            sys.stdout = captured_output

            # 使用 exec() 函数执行传入的字符串形式的 Python 代码
            # 创建一个字典来存储 exec 执行后的本地变量``
            local_vars = {}

            exec(python_code, locals(), local_vars)
            print(local_vars['file_path'])

            # 恢复原始的 stdout
            sys.stdout = saved_stdout
            # 获取捕获的输出
            output = captured_output.getvalue()
            # 返回 local_vars，这包含了执行代码后的本地变量
            # print("---------output"+output)
            return output
        except Exception as e:
            sys.stdout = saved_stdout
            # 如果执行过程中发生错误，返回错误信息
            print("Coder工作中：执行本地代码...")
            try:
                return self.__python_local_exec(python_code)
            except Exception as e:
                raise (e)

    def __python_local_exec(self, python_code):

        # 创建临时目录
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"tmp")
        os.makedirs(temp_dir, exist_ok=True)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py', dir=temp_dir) as temp_file:
            temp_file.write(python_code.encode())
            temp_file_path = temp_file.name

        try:
            # 执行临时文件
            result = subprocess.run(
                ['python3', temp_file_path],
                capture_output=True,
                text=True
            )

            # 捕获标准输出和标准错误
            stdout = result.stdout
            stderr = result.stderr

            if result.returncode != 0:
                raise Exception(f"{self.__extract_key_error_message(stderr)}")

            return stdout

        finally:
            pass
            # 删除临时文件
            # os.remove(temp_file_path)

    def __extract_key_error_message(self, stderr):
        """
        提取包含 XXXError 的所有语句

        :param traceback_str: 字符串类型，包含完整的报错信息
        :return: 列表，包含所有 XXXError 的语句
        """
        error_lines = re.findall(r'.*\b\w*Error\b.*', stderr)
        cleaned_error_lines = ""
        for line in error_lines:
            pattern = re.compile(r'File ".*?", line \d+, in .*')
            cleaned_line = pattern.sub('', line).strip()
            cleaned_error_lines += cleaned_line + "\n"
        return cleaned_error_lines