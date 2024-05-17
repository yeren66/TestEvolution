import pandas as pd
from transformers import AutoTokenizer
import matplotlib.pyplot as plt
import numpy as np

# 指定模型的路径
model_path = '/Users/mac/Desktop/codet5-base'

# 加载 tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 读取 CSV 文件
df = pd.read_csv('train.csv')

# 对 input 和 target 进行 tokenization，并计算长度
input_lengths = df['src_fm_fc_ms_ff'].apply(lambda x: len(tokenizer.encode(x)))
target_lengths = df['target'].apply(lambda x: len(tokenizer.encode(x)))

# 统计 input 和 target 中 token 数小于 256, 512 和 1024 的比例

input_less_than_256 = sum(input_lengths < 256) / len(input_lengths)
target_less_than_256 = sum(target_lengths < 256) / len(target_lengths)

input_less_than_512 = sum(input_lengths < 512) / len(input_lengths)
target_less_than_512 = sum(target_lengths < 512) / len(target_lengths)

input_less_than_1024 = sum(input_lengths < 1024) / len(input_lengths)
target_less_than_1024 = sum(target_lengths < 1024) / len(target_lengths)

count = 0
for i in range(len(input_lengths)):
    if input_lengths[i] + target_lengths[i] < 1024:
        count += 1

print("Percentage of input + target with token count < 1024: ", count / len(input_lengths))
# print(count / len(input_lengths))
        

# 打印结果
print(f"Percentage of inputs with token count < 256: {input_less_than_256 * 100:.2f}%")
print(f"Percentage of targets with token count < 256: {target_less_than_256 * 100:.2f}%")
print(f"Percentage of inputs with token count < 512: {input_less_than_512 * 100:.2f}%")
print(f"Percentage of targets with token count < 512: {target_less_than_512 * 100:.2f}%")
print(f"Percentage of inputs with token count < 1024: {input_less_than_1024 * 100:.2f}%")
print(f"Percentage of targets with token count < 1024: {target_less_than_1024 * 100:.2f}%")



# 绘制条形图
# bins = np.linspace(0, 3000, 300) 

# plt.figure(figsize=(12, 6))
# plt.hist(input_lengths, bins=bins, alpha=0.5, label='Input Lengths')
# plt.hist(target_lengths, bins=bins, alpha=0.5, label='Target Lengths')
# plt.xlabel('Token Length')
# plt.ylabel('Frequency')
# plt.title('Distribution of Token Lengths')
# plt.legend(loc='upper right')
# plt.show()
