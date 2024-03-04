import json
import os
import get_modified_files
import find_commit_hash_in_range
import save_git_log_to_file
import parse_git_log
import re
from tqdm import tqdm
import logging
import subprocess

logging.basicConfig(filename="debug.log", level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
temp_folder = "temp"
current_path = "/Users/mac/Desktop/TestEvolution"
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    

def product_code_filter(changed_file_path):
    key_words = ["src/main/java", ".java"]
    for key_word in key_words:
        if key_word not in changed_file_path:
            return False
    return True

def test_product_code_filter(change_file_path, related_product_file_path):
    # test_file_name = change_file_path.split('/')[-1]
    # if 'test' not in test_file_name.lower():
    #     return False
    path_info = '/'.join(related_product_file_path.split('/')[:-1])
    path_info = re.sub(r"src/main/java", "src/test/java", path_info)
    product_file_name = related_product_file_path.split('/')[-1].split('.')[0]
    key_words = [path_info, product_file_name]
    for key_word in key_words:
        if key_word not in change_file_path:
            return False
    return True

def gumtree_filter(old_content, new_content):
    # 筛选新旧文件的修改内容只是注释修改的情况
    if old_content == None or new_content == None:
        return False
    # 获取当前工作路径
    now_path = os.getcwd()
    # 切换至对应的项目目录
    os.chdir(current_path)
    old_path = os.path.join(temp_folder, "temp_old.java")
    new_path = os.path.join(temp_folder, "temp_new.java")
    target_path = os.path.join(temp_folder, "temp_target.json")
    with open(old_path, "w") as file:
        file.write(old_content)
    with open(new_path, "w") as file:
        file.write(new_content)
    command = f"java -jar gumtree.jar textdiff {old_path} {new_path} -f JSON -o {target_path}"
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
        # return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # print(f"Error running command {' '.join(command)}: {e}")
        logging.error(f"Error running command {' '.join(command)}: {e}")
        return False
    ret = read_json(target_path)
    actions =  ret["actions"]
    os.chdir(now_path)
    if len(actions) == 0:
        return False
    for action in actions:
        change_type = action['tree'].split(":")[0]
        if change_type != "TextElement":
            return True
    return False


def save_PT_pair(json_block, output_file_path):
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as file:
            PT_pairs = json.load(file)
    else:
        PT_pairs = []
    PT_pairs.append(json_block)
    with open(output_file_path, 'w') as file:
        json.dump(PT_pairs, file, indent=4)


def construct_PT_pair(project_path, output_dir, commit_info_list):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 切换至对应的项目目录
    os.chdir(project_path)
    # 遍历从该项目下获取的每个commit
    positive_total = 0
    negative_total = 0
    for commit_info in tqdm(commit_info_list):
        # print(f"Processing commit {commit_hash}")
        commit_hash = commit_info['commit']
        commit_hash = commit_hash.split(' ')[-1]
        # 获取该commit下的所有修改文件
        changed_files_paths = get_modified_files.get_changed_files(commit_hash)
        # with open("/Users/mac/Desktop/TestEvolution/changed_files.txt", "a") as file:
        #     file.write(commit_hash + "\n")
        #     for changed_files_path in changed_files_paths:
        #         file.write(changed_files_path + "\n")
        #     file.write("\n")
        # print(len(changed_files_paths))
        # 过滤出product code文件
        product_files_paths = list(filter(product_code_filter, changed_files_paths))
        # print(len(product_files_paths))
        if len(product_files_paths) > 0:
            # 获取该commit之后12个小时内的commit
            positive_related_commits = find_commit_hash_in_range.find_commits(commit_hash, 0, 12)
            # 获取该commit之后12小时到480小时内的commit，468=480-12
            negative_related_commits = find_commit_hash_in_range.find_commits(commit_hash, 12, 468)
            # 对于每个product code文件，获取其相关的test code文件，
            # 12h以内全部为正样本，12h到480h为负样本，不考虑product与test文件的对应关系（后续筛选会处理）
            for product_files_path in product_files_paths:
                for positive_related_commit in positive_related_commits:
                    related_changed_files = get_modified_files.get_changed_files(positive_related_commit)
                    filter_changed_files = []
                    for related_changed_file in related_changed_files:
                        if test_product_code_filter(related_changed_file, product_files_path):
                            filter_changed_files.append(related_changed_file)
                    related_changed_files = filter_changed_files
                    if len(related_changed_files) == 1:
                        # print("find a positive sample")
                        positive_total += 1
                        product_old_content, product_new_content = get_modified_files.get_file_content(commit_hash, product_files_path)
                        test_old_content, test_new_content = get_modified_files.get_file_content(positive_related_commit, related_changed_files[0])
                        if gumtree_filter(product_old_content, product_new_content) and gumtree_filter(test_old_content, test_new_content):
                            json_block = {
                                "tag": "positive",
                                "product_commit": commit_hash,
                                "test_commit": positive_related_commit,
                                "product_file_path": product_files_path,
                                "test_file_path": related_changed_files[0],
                                "product_old_content": product_old_content,
                                "product_new_content": product_new_content,
                                "test_old_content": test_old_content,
                                "test_new_content": test_new_content
                            }
                            save_PT_pair(json_block, os.path.join(output_dir, "samples.json"))
                        

                for negative_related_commit in negative_related_commits:
                    related_changed_files = get_modified_files.get_changed_files(negative_related_commit)
                    filter_changed_files = []
                    for related_changed_file in related_changed_files:
                        if test_product_code_filter(related_changed_file, product_files_path):
                            filter_changed_files.append(related_changed_file)
                    related_changed_files = filter_changed_files
                    if len(related_changed_files) == 1:
                        # print("find a negative sample")
                        negative_total += 1
                        product_old_content, product_new_content = get_modified_files.get_file_content(commit_hash, product_files_path)
                        test_old_content, test_new_content = get_modified_files.get_file_content(negative_related_commit, related_changed_files[0])
                        json_block = {
                            "tag": "negative",
                            "product_commit": commit_hash,
                            "test_commit": negative_related_commit,
                            "product_file_path": product_files_path,
                            "test_file_path": related_changed_files[0],
                            "product_old_content": product_old_content,
                            "product_new_content": product_new_content,
                            "test_old_content": test_old_content,
                            "test_new_content": test_new_content
                        }
                        save_PT_pair(json_block, os.path.join(output_dir, "samples.json"))
                        
    print(f"positive_total: {positive_total}")
    print(f"negative_total: {negative_total}")



if __name__ == "__main__":

    # project_path = "/Users/mac/Desktop/Java"
    project_path = "/Users/mac/Desktop/commons-math"
    temp_file_path = "temp_git_log.txt"
    save_git_log_to_file.save_git_log_to_file(project_path, temp_file_path)
    commit_info = parse_git_log.parse_git_log(temp_file_path)
    commit_hash_list = json.dumps(commit_info, indent=4)
    output_json_path = 'temp_git_log.json'
    with open(output_json_path, 'w') as json_file:
        json_file.write(commit_hash_list)
    commit_hash_list = read_json(output_json_path)
    output_dir = "/Users/mac/Desktop/TestEvolution/common-math_output"
    construct_PT_pair(project_path, output_dir, commit_hash_list)
    # a = "/*\n * Licensed to the Apache Software Foundation (ASF) under one or more\n * contributor license agreements.  See the NOTICE file distributed with\n * this work for additional information regarding copyright ownership.\n * The ASF licenses this file to You under the Apache License, Version 2.0\n * (the \"License\"); you may not use this file except in compliance with\n * the License.  You may obtain a copy of the License at\n *\n *      http://www.apache.org/licenses/LICENSE-2.0\n *\n * Unless required by applicable law or agreed to in writing, software\n * distributed under the License is distributed on an \"AS IS\" BASIS,\n * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n * See the License for the specific language governing permissions and\n * limitations under the License.\n */\npackage org.apache.commons.math4.legacy.random;\n\nimport org.junit.Assert;\nimport org.apache.commons.math4.legacy.exception.DimensionMismatchException;\nimport org.apache.commons.math4.legacy.exception.NullArgumentException;\nimport org.apache.commons.math4.legacy.exception.OutOfRangeException;\nimport org.junit.Before;\nimport org.junit.Test;\n\npublic class HaltonSequenceGeneratorTest {\n\n    private double[][] referenceValues = {\n            { 0.0,    0.0,    0.0  },\n            { 0.5,    0.6667, 0.6  },\n            { 0.25,   0.3333, 0.2  },\n            { 0.75,   0.2223, 0.8  },\n            { 0.125,  0.8888, 0.4  },\n            { 0.625,  0.5555, 0.12 },\n            { 0.375,  0.1111, 0.72 },\n            { 0.875,  0.7777, 0.32 },\n            { 0.0625, 0.4444, 0.92 },\n            { 0.5625, 0.0740, 0.52 }\n    };\n\n    private double[][] referenceValuesUnscrambled = {\n            { 0.0,    0.0    },\n            { 0.5,    0.3333 },\n            { 0.25,   0.6666 },\n            { 0.75,   0.1111 },\n            { 0.125,  0.4444 },\n            { 0.625,  0.7777 },\n            { 0.375,  0.2222 },\n            { 0.875,  0.5555 },\n            { 0.0625, 0.8888 },\n            { 0.5625, 0.0370 }\n    };\n\n    private HaltonSequenceGenerator generator;\n\n    @Before\n    public void setUp() {\n        generator = new HaltonSequenceGenerator(3);\n    }\n\n    @Test\n    public void test3DReference() {\n        for (int i = 0; i < referenceValues.length; i++) {\n            double[] result = generator.get();\n            Assert.assertArrayEquals(referenceValues[i], result, 1e-3);\n            Assert.assertEquals(i + 1, generator.getNextIndex());\n        }\n    }\n\n    @Test\n    public void test2DUnscrambledReference() {\n        generator = new HaltonSequenceGenerator(2, new int[] {2, 3}, null);\n        for (int i = 0; i < referenceValuesUnscrambled.length; i++) {\n            double[] result = generator.get();\n            Assert.assertArrayEquals(referenceValuesUnscrambled[i], result, 1e-3);\n            Assert.assertEquals(i + 1, generator.getNextIndex());\n        }\n    }\n\n    @Test\n    public void testConstructor() {\n        try {\n            new HaltonSequenceGenerator(0);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (OutOfRangeException e) {\n            // expected\n        }\n\n        try {\n            new HaltonSequenceGenerator(41);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (OutOfRangeException e) {\n            // expected\n        }\n    }\n\n    @Test\n    public void testConstructor2() throws Exception{\n        try {\n            new HaltonSequenceGenerator(2, new int[] { 1 }, null);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (OutOfRangeException e) {\n            // expected\n        }\n\n        try {\n            new HaltonSequenceGenerator(2, null, null);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (NullArgumentException e) {\n            // expected\n        }\n\n        try {\n            new HaltonSequenceGenerator(2, new int[] { 1, 1 }, new int[] { 1 });\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (DimensionMismatchException e) {\n            // expected\n        }\n    }\n\n    @Test\n    public void testSkip() {\n        double[] result = generator.skipTo(5);\n        Assert.assertArrayEquals(referenceValues[5], result, 1e-3);\n        Assert.assertEquals(6, generator.getNextIndex());\n\n        for (int i = 6; i < referenceValues.length; i++) {\n            result = generator.get();\n            Assert.assertArrayEquals(referenceValues[i], result, 1e-3);\n            Assert.assertEquals(i + 1, generator.getNextIndex());\n        }\n    }\n\n}"

    # b = "/*\n * Licensed to the Apache Software Foundation (ASF) under one or more\n * contributor license agreements.  See the NOTICE file distributed with\n * this work for additional information regarding copyright ownership.\n * The ASF licenses this file to You under the Apache License, Version 2.0\n * (the \"License\"); you may not use this file except in compliance with\n * the License.  You may obtain a copy of the License at\n *\n *      http://www.apache.org/licenses/LICENSE-2.0\n *\n * Unless required by applicable law or agreed to in writing, software\n * distributed under the License is distributed on an \"AS IS\" BASIS,\n * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n * See the License for the specific language governing permissions and\n * limitations under the License.\n */\npackage org.apache.commons.math4.legacy.random;\n\nimport org.junit.Assert;\nimport org.apache.commons.math4.legacy.exception.DimensionMismatchException;\nimport org.apache.commons.math4.legacy.exception.NotPositiveException;\nimport org.apache.commons.math4.legacy.exception.NullArgumentException;\nimport org.apache.commons.math4.legacy.exception.OutOfRangeException;\nimport org.junit.Before;\nimport org.junit.Test;\n\npublic class HaltonSequenceGeneratorTest {\n\n    private double[][] referenceValues = {\n            { 0.0,    0.0,    0.0  },\n            { 0.5,    0.6667, 0.6  },\n            { 0.25,   0.3333, 0.2  },\n            { 0.75,   0.2223, 0.8  },\n            { 0.125,  0.8888, 0.4  },\n            { 0.625,  0.5555, 0.12 },\n            { 0.375,  0.1111, 0.72 },\n            { 0.875,  0.7777, 0.32 },\n            { 0.0625, 0.4444, 0.92 },\n            { 0.5625, 0.0740, 0.52 }\n    };\n\n    private double[][] referenceValuesUnscrambled = {\n            { 0.0,    0.0    },\n            { 0.5,    0.3333 },\n            { 0.25,   0.6666 },\n            { 0.75,   0.1111 },\n            { 0.125,  0.4444 },\n            { 0.625,  0.7777 },\n            { 0.375,  0.2222 },\n            { 0.875,  0.5555 },\n            { 0.0625, 0.8888 },\n            { 0.5625, 0.0370 }\n    };\n\n    private HaltonSequenceGenerator generator;\n\n    @Before\n    public void setUp() {\n        generator = new HaltonSequenceGenerator(3);\n    }\n\n    @Test\n    public void test3DReference() {\n        for (int i = 0; i < referenceValues.length; i++) {\n            double[] result = generator.get();\n            Assert.assertArrayEquals(referenceValues[i], result, 1e-3);\n            Assert.assertEquals(i + 1, generator.getNextIndex());\n        }\n    }\n\n    @Test\n    public void test2DUnscrambledReference() {\n        generator = new HaltonSequenceGenerator(2, new int[] {2, 3}, null);\n        for (int i = 0; i < referenceValuesUnscrambled.length; i++) {\n            double[] result = generator.get();\n            Assert.assertArrayEquals(referenceValuesUnscrambled[i], result, 1e-3);\n            Assert.assertEquals(i + 1, generator.getNextIndex());\n        }\n    }\n\n    @Test\n    public void testConstructor() {\n        try {\n            new HaltonSequenceGenerator(0);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (OutOfRangeException e) {\n            // expected\n        }\n\n        try {\n            new HaltonSequenceGenerator(41);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (OutOfRangeException e) {\n            // expected\n        }\n    }\n\n    @Test\n    public void testConstructor2() throws Exception{\n        try {\n            new HaltonSequenceGenerator(2, new int[] { 1 }, null);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (OutOfRangeException e) {\n            // expected\n        }\n\n        try {\n            new HaltonSequenceGenerator(2, null, null);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (NullArgumentException e) {\n            // expected\n        }\n\n        try {\n            new HaltonSequenceGenerator(2, new int[] { 1, 1 }, new int[] { 1 });\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (DimensionMismatchException e) {\n            // expected\n        }\n    }\n\n    @Test\n    public void testSkip() {\n        double[] result = generator.skipTo(5);\n        Assert.assertArrayEquals(referenceValues[5], result, 1e-3);\n        Assert.assertEquals(6, generator.getNextIndex());\n\n        for (int i = 6; i < referenceValues.length; i++) {\n            result = generator.get();\n            Assert.assertArrayEquals(referenceValues[i], result, 1e-3);\n            Assert.assertEquals(i + 1, generator.getNextIndex());\n        }\n    }\n\n    @Test\n    public void testSkipToNegative() {\n        try {\n            generator.skipTo(-4584);\n            Assert.fail(\"an exception should have been thrown\");\n        } catch (NotPositiveException e) {\n            // expected\n        }\n    }\n}"


    # print(gumtree_filter(a, b))
