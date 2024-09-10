import json
from typing import Union, Any

import yaml
from .exceptions import *
from subprocess import PIPE, TimeoutExpired
import subprocess
import functools
import warnings
import re
import os
import base64
import csv
import hashlib
import glob

def Deprecated(func):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(f"调用了被废弃的方法{func.__name__}！", category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return new_func

def NotImplemented(func):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn(f"此方法并没有被实际实现{func.__name__}！", category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return new_func

def read_jsonfile(filename):
    json_data = None
    try:
        with open(filename, 'r') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundException(f"{filename} is not found")
    
    return json_data

def read_yamlfile(filename):
    yaml_data = None
    try:
        with open(filename, 'r') as f:
            yaml_data = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundException(f"{filename} is not found")
    
    # 把所有的model放入到models中，直接使用dict访问而不使用列表
    return yaml_data

def json_loads(json_data_str : str):
    return json.loads(json_data_str)

#python 函数调用
'''
command = ["ls", "-l"]  # 一个示例命令，在Unix & Linux系统中列出当前目录的内容
timeout_seconds = 2  # 设置超时为2秒
result = run_command(command, timeout_seconds)

print("Standard Output:", result["stdout"])
print("Standard Error:", result["stderr"])
print("Return Code:", result["returncode"])
if "error" in result:
    print("Error:", result["error"])
'''
def sb_process(command, timeout):
    try:
        # 运行命令并捕获输出
        result = subprocess.run(
            command,                     # 命令和参数的列表
            stdout=PIPE,                 # 捕获标准输出
            stderr=PIPE,                 # 捕获标准错误
            text=True,                   # 输出作为文本处理
            timeout=timeout              # 设置超时时间
        )
        return {
            "stdout": result.stdout,     # 正常输出
            "stderr": result.stderr,     # 错误输出
            "returncode": result.returncode  # 进程的返回码
        }
    except TimeoutExpired as e:
        return {
            "stdout": e.stdout,          # 超时情况下的正常输出
            "stderr": e.stderr,          # 超时情况下的错误输出
            "returncode": None,          # 没有返回码
            "error": "timeout"           # 表明发生超时
        }
    except subprocess.CalledProcessError as e:
        return {
            "stdout": e.stdout,          # 错误时的正常输出
            "stderr": e.stderr,          # 错误时的错误输出
            "returncode": e.returncode,  # 子进程的退出码
            "error": str(e)              # 异常信息
        }
        

def delete_files_in_dir_except_keep(directory):
    # 遍历指定目录下的所有文件和子目录
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        # 检查当前路径是否为文件，并且文件名不是 '.keep'
        if os.path.isfile(file_path) and filename != '.keep':
            os.remove(file_path)  # 删除文件


def read_model_config(model_name):
    """
    从yaml配置文件中读取model配置
    """
    config = read_yamlfile(".//llm/model_config.yaml")[model_name]

    if config is None : 
        raise ModelConfigNotFoundException(f"{model_name}'config is not ready")
    
    model_path = config["model_path"]
    cache_dir = config['cache_dir']
    return model_path,cache_dir

def extract_content_between_braces(text):
    # 找到第一个出现的 '{'
    start_index = text.find('{')

    # 找到最后一个出现的 '}'
    end_index = text.rfind('}')

    # 如果两个花括号都找到了，提取中间的内容
    if start_index != -1 and end_index != -1 and end_index > start_index:
        return text[start_index:end_index + 1]
    else:
        return None  # 如果没有找到或者顺序不正确，返回空字符串   

def extract_python_wrapped_content(text):
    # 使用正则表达式匹配被 ```json 和 ``` 包裹的内容
    pattern = r"```python(.*?)```"
    # 使用非贪婪模式进行匹配
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(0)
    else:
        return None

def extract_bash_wrapped_content(text):
    # 使用正则表达式匹配被 ```json 和 ``` 包裹的内容
    pattern = r"```bash(.*?)```"
    # 使用非贪婪模式进行匹配
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(0)
    else:
        return None
    
def add_good_question_and_solution(question, solution):
    csv_file_name = './/vector_database/previous_solution.csv'
    # Define the headers
    headers = ['question', 'solution']
    
    # Check if the CSV file exists
    file_exists = os.path.isfile(csv_file_name)
    
    # Open the CSV file in append mode
    with open(csv_file_name, mode='a', newline='', encoding='utf-8') as file:
        # Create a CSV writer object
        csv_writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        
        # If the file does not exist, write the headers
        if not file_exists:
            csv_writer.writerow(headers)
        
        # Write the question and solution as a new row in the CSV file
        csv_writer.writerow([question, solution])
    

def extract_sql_wrapped_content(text):
    # 使用正则表达式匹配被 ```json 和 ``` 包裹的内容
    pattern = r"```sql(.*?)```"
    # 使用非贪婪模式进行匹配
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(0)
    else:
        return None

def load_file(filename):
    try:
        if filename.endswith('.txt'):
            with open(filename, 'r') as f:
                return f.read()
        elif filename.endswith('.csv'):
            with open(filename, 'r', newline='') as f:
                reader = csv.DictReader(f)
                return list(reader)
        elif filename.endswith('.png'):
            with open(filename, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    except Exception as e:
        raise FileNotFoundError(f"{filename} is not found or cannot be opened") from e

def print_colored_text(text, color):
    # ANSI 转义序列颜色代码
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }

    # 获取颜色代码
    color_code = colors.get(color.lower(), colors["reset"])

    # 打印带颜色的文本
    print(f"{color_code}{text}{colors['reset']}")

def list2str(lst):
    # 使用枚举和字符串格式化生成带序号的字符串
    numbered_list = [f"{item}" for i, item in enumerate(lst)]

    # 将列表转换为字符串，每个元素用换行符分隔
    result_str = '\n'.join(numbered_list)

    return result_str

def TODO(description):
    assert False, f"TODO: {description}"

def calculate_md5(string):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    return md5_hash.hexdigest()

def response_format_for_send(msg: str, images=None, is_result=False, card_type:str=None, is_timeout:bool=False, document:list=None, has_more:bool=False):
    """
    返回给前端的数据格式
    """
    assert card_type is not None, "card_type is None"

    # card_type 必须是notCard, demandCalib, resultConfirm中的一种
    assert card_type in ["notCard", "demandCalib", "resultConfirm"], f"card_type: {card_type} is not valid"
    
    return {
        "msg" : msg,
        "images" : images,
        "is_result" : is_result,
        "card_type" : card_type,
        "is_timeout": is_timeout,
        "document" : document,
        "has_more": has_more
    }

def check_files_in_response_and_return_absolute_paths(response):
    # 指定文件夹路径
    folder_path = "/tmp/report"
    
    # 获取文件夹中的所有文件名
    filenames = os.listdir(folder_path)
    
    # 初始化返回的文件路径列表
    valid_paths = []

    # 循环每个文件，检查是否在response字符串中
    for filename in filenames:
        full_path = os.path.abspath(os.path.join(folder_path, filename))
        # 检查文件的完整路径是否出现在响应中
        if full_path.split('/')[-1] in response:
            # 将文件的绝对路径添加到列表
            valid_paths.append(full_path)
    
    return valid_paths

def load_llm_json(response, keys):
    """
    Args:
        response: 模型回答
        keys: 要检查的key

    Returns: json转成的字典

    """
    json_dict = ""
    try:
        json_content = extract_content_between_braces(response)
        if json_content is not None:
            json_dict = json_loads(json_content)

        for key in keys:
            if key not in json_dict:
                return False
            return json_dict
    except Exception as e:
        raise WrongOutputFormatException("json格式有误") from e

def get_intent(intent_chatter,instruction,keys):
    """

    Args:
        intent_chatter: 意图识别chatter
        instruction: 传给chatter的输入
        keys: 要检查的key

    Returns: josn转成的字典

    """
    json_dict = {}
    for i in range(3):#成功提前返回
        response = intent_chatter.chat(instruction).strip("`")
        print(response)
        try:
            json_dict = load_llm_json(response, keys)
            return json_dict
        except WrongOutputFormatException as e:
            print(f"尝试次数{i}")
            print(e.message)
            continue
    return json_dict
    



def read_latest_csv():
    csv_files = glob.glob("/tmp/report/*.csv")
    print(csv_files)
    # 找出最新的文件
    csv_file_path = max(csv_files, key=os.path.getctime)
    return csv_file_path

def read_csv_first_header(file):
    reader = csv.reader(file)
    header = next(reader)  # 获取第一行数据，即标题(header)
    print("CSV File Header:")
    print(header)
    return header

def replace_space_between_chinese_and_english(text):
    print(f"去除之前：{text}")
    new_text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[a-zA-Z0-9])|(?<=[a-zA-Z0-9])\s+(?=[\u4e00-\u9fff])', '', text)
    print(f"去除之后：{new_text}")
    return new_text