import unittest


# self.dataset_name_to_id_map = {
#     "tt_qa_bug_stats": 3028770,
#     "feature_delay_stats": 3054442,
#     "meego_bugs": 3223007,
#     "tt_qa_throughput": 3230409,
#     "tt_qa_feature_leadtime": 3223964,
#     "meego_bugs_join": 3241019,
#     "TikTok_QA_Tasks": 2806498
# }
#  pytest --numprocesses=4 tests/test_chatbi.py #pip install pytest pytest-xdist
class TestChatBi(unittest.TestCase):
   test_query = [""]
    chatbi = ChatBI(token='kgqi5rc3cawnf2rwd2yw2zxba36e0bze', username="guoshaoxiong", dataset_id=3230409)
        # self.chatbi = ChatBI(token='kgqi5rc3cawnf2rwd2yw2zxba36e0bze', username="guoshaoxiong", dataset_id=3241019)
    def test_query1(self):
        ins = "查询测试最晚时间是'2024-12-31'，time_tag='start_tag'、Date Range不为空，p_date是'2024-01-01'至'2024-12-31'，是否需求交付Delay='是'的求和数，story_id去重计数，以及两者的比值作为需求Delay率，Value Chains为Music"
        # ins = "time_tag='start_tag'、Date Range不为空，是否需求交付Delay='是'的求和数，story_id去重计数，以及两者的比值作为需求Delay率，Value Chains为Music,在2023年全年的数据，并按月聚合"
        # ins = "查询 `project_space` 在 ('TikTok', 'TikTok Arch', 'TikTok LIVE') 中、`是否是测试Bug` 为0、`线上用户无感知Bug` 为0、`BugBash Bug` 为0、`是否是有效Bug` 为1、`Value Chains` 在 ('音乐', 'Music') 且 `bug_create_date` 在2024年全年的数据，并按月聚合"
        # ins = "查询 `bug_create_time`是'2024年'，`周期内是否在白名单`='否'的`有效Bug数(效率度量)`求和数，`人员`去重计数，以及两者的比值作`人均BUG数`，列出有效BUG数低于人均BUG数的人员明细"
        with open("chatbi_test_result1.txt", "a") as f:
            f.write(ins + "\n")
            for i in range(5):
                try:
                    data = self.chatbi.completion(ins)
                    print(data)
                    f.write(str(data['data']['rows'])+"\n")
                except ChatBIChatException as e:
                    f.write(f"语句查询失败---第{i}次查询\n")
    def test_query2(self):
        ins =  " 查询 project_space 在 ('TikTok', 'TikTok Arch', 'TikTok LIVE') 中，是否是测试 Bug 为 0，线上用户无感知 Bug 为 0，BugBash Bug 为 0，是否是有效 Bug 为 1，Value Chains 为 PGC 且时间为2023 年，按月聚合"
        with open("chatbi_test_result2.txt", "a") as f:
            for i in range(5):
                try:
                    data = self.chatbi.completion(ins)
                    f.write(str(data['data']['rows'])+"\n")
                except ChatBIChatException as e:
                    f.write(f"语句查询失败---第{i}次查询\n")






