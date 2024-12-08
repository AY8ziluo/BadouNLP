import json
import random

import numpy as np
import torch as torch
import torch.nn as nn
from matplotlib import pyplot as plt


class HomeworkModel(nn.Module):
    # vocab字表  sentence_length单个输入的文本长度  vector_dim单个字符的长度
    def __init__(self, vector_dim, sentence_length, hidden, vocab):
        super(HomeworkModel, self).__init__()
        self.embedding = nn.Embedding(len(vocab), vector_dim, padding_idx=0)
        self.pool = nn.AvgPool1d(sentence_length)
        self.rnn = nn.RNN(vector_dim, hidden, batch_first=True)
        self.linear = nn.Linear(hidden, 6)
        self.mse_loss = nn.functional.cross_entropy

    def forward(self, x, y=None):
        # nlp任务首先需要进入embedding层  将输入的文字转化为可以计算的张量
        x = self.embedding(x)  #20 * 6  -> 20 * 6 *10
        x, _ = self.rnn(x)    # 20 * 6 * 10 -> 20 * 6 * 10
        x = x.transpose(1, 2)   # 20 * 6 * 10 -> 20 * 10 * 6
        x = self.pool(x) #20 * 10 * 6 -> 20 * 10 *1
        # 去掉池化后空的一维
        x = x.squeeze()  #20 * 10 *1 -> 20 * 10
        x = self.linear(x) # 20 * 10 -> 20 * 6
        y_pred = x
        if y is not None:
            # 如果传进了真实值 则可以在此处返回预测值和真实值之间的loss
            return self.mse_loss(y_pred, y)
        else:
            # 如果没有传进真实值 则只返回预测值
            return y_pred


# 构建字表
def build_vocab():
    # 先放入一个训练数据
    vocab = {'pad': 0}
    # 字符集  可以是某些文章中爬虫下来的文字  组合成一个字符集
    chars = "你我他defghijklmnopqrstuvwxyz"  # 字符集
    for index, char in enumerate(chars):
        # 每个字符集对应一个编号  个人认为是固定为索引  来对应embedding层来方便对应参照取值
        # 由于第0位为训练数据所以从第1位开始设置
        vocab[char] = index + 1
    vocab['unk'] = len(vocab)
    return vocab


def build_sample(vocab, sentence_length):
    # 随机从字表中取出sentence_length长度的随机字符串  准备作为输入x
    # x = [random.choice(list(vocab.keys())) for _ in range(sentence_length)]
    # 先随机生成五个数
    x = [random.choice(list(vocab.keys())) for _ in range(sentence_length -1)]

    if '你' in x:
        y = x.index('你')
        # 如果包含你最后随便加一个数
        x.append('a')
    else:
        # 把你随机放在一个位置
        x.insert(random.randint(0,5),'你')
        y = x.index('你')

    x = [vocab.get(word, vocab['unk']) for word in x]  # 将字转换成序号，为了做embedding
    return x, y


# 根据需要创建训练集
def build_dataset(sample_length, vocab, sentence_length):
    dataset_x = []
    dataset_y = []
    for i in range(sample_length):
        x, y = build_sample(vocab, sentence_length)
        dataset_x.append(x)
        dataset_y.append(y)
    return torch.LongTensor(dataset_x), torch.LongTensor(dataset_y)


# 建立模型
def build_model(vocab, char_dim, hidden, sentence_length):
    model = HomeworkModel(char_dim, sentence_length, hidden, vocab)
    return model


# 测试代码
# 用来测试每轮模型的准确率
# def evaluate(model, vocab, sample_length):
#     model.eval()
#     x, y = build_dataset(200, vocab, sample_length)  # 建立200个用于测试的样本
#     print("本次预测集中共有%d个正样本，%d个负样本" % (sum(y), 200 - sum(y)))
#     correct, wrong = 0, 0
#     with torch.no_grad():
#         y_pred = model(x)  # 模型预测
#         for y_p, y_t in zip(y_pred, y):  # 与真实标签进行对比
#             if float(y_p) < 0.5 and int(y_t) == 0:
#                 correct += 1  # 负样本判断正确
#             elif float(y_p) >= 0.5 and int(y_t) == 1:
#                 correct += 1  # 正样本判断正确
#             else:
#                 wrong += 1
#     print("正确预测个数：%d, 正确率：%f" % (correct, correct / (correct + wrong)))
#     return correct / (correct + wrong)

def evaluate(model, vocab, sample_length):
    model.eval()
    x, y = build_dataset(200, vocab, sample_length)  # 建立200个用于测试的样本
    # print("本次预测集中共有%d个正样本，%d个负样本" % (sum(y), 200 - sum(y)))
    correct, wrong = 0, 0
    with torch.no_grad():
        y_pred = model(x)  # 模型预测
        for y_p, y_t in zip(y_pred, y):  # 与真实标签进行对比
            if np.argmax(y_p) == int(y_t):
                correct += 1
            else:
                wrong += 1
    print("正确预测个数：%d, 正确率：%f" % (correct, correct / (correct + wrong)))
    return correct / (correct + wrong)


def main():
    # 配置参数
    epoch_num = 10  # 训练轮数
    batch_size = 20  # 每次训练样本个数
    train_sample = 500  # 每轮训练总共训练的样本总数
    char_dim = 10  # 每个字的维度
    sentence_length = 6  # 样本文本长度
    hidden = 10 # 隐藏层维度
    learning_rate = 0.005  # 学习率
    # 建立字表
    vocab = build_vocab()
    # 建立模型
    model = build_model(vocab, char_dim, hidden, sentence_length)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = []
    # 训练过程
    for epoch in range(epoch_num):
        model.train()
        watch_loss = []
        for batch in range(int(train_sample / batch_size)):
            x, y = build_dataset(batch_size, vocab, sentence_length)  # 构造一组训练样本
            optim.zero_grad()  # 梯度归零
            loss = model(x, y)  # 计算loss
            loss.backward()  # 计算梯度
            optim.step()  # 更新权重
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss)))
        acc = evaluate(model, vocab, sentence_length)  # 测试本轮模型结果
        log.append([acc, np.mean(watch_loss)])
    # 画图
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  # 画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  # 画loss曲线
    plt.legend()
    plt.show()
    # 保存模型
    torch.save(model.state_dict(), "model.pth")
    # 保存词表
    writer = open("vocab.json", "w", encoding="utf8")
    writer.write(json.dumps(vocab, ensure_ascii=False, indent=2))
    writer.close()
    return


# 使用训练好的模型做预测
def predict(model_path, vocab_path, input_strings):
    char_dim = 20  # 每个字的维度
    sentence_length = 6  # 样本文本长度
    hidden = 10
    vocab = json.load(open(vocab_path, "r", encoding="utf8"))  # 加载字符表
    model = build_model(vocab, char_dim, sentence_length)  # 建立模型
    model.load_state_dict(torch.load(model_path))  # 加载训练好的权重
    x = []
    for input_string in input_strings:
        x.append([vocab[char] for char in input_string])  # 将输入序列化
    model.eval()  # 测试模式
    with torch.no_grad():  # 不计算梯度
        result = model.forward(torch.LongTensor(x))  # 模型预测
    for i, input_string in enumerate(input_strings):
        # print("输入：%s, 预测类别：%d, 概率值：%f" % (input_string, ,result ))  # 打印结果
        print("输入：%s, , 概率值分布：%s" % (input_string ,result[i] ))  # 打印结果


if __name__ == "__main__":
    main()
    # test_strings = ["你nvfee", "wz你dfg", "rqwde你", "n我kw你w"]
    # predict("model.pth", "vocab.json", test_strings)
