# coding:utf-8
import itchat
from itchat.content import *
import jieba
import math
import time
import os
import hashlib
from email.utils import formatdate
from email.header import Header
import smtplib


# threshold for target content detection
# if you want more recall, decreasing threshold
# if you want more precision, increasing threshold
# -recall means more targets including but noise as well
# -precision means losing some targets and make more clear
# if you want more precision threshold = 0.3 recommended
threshold = 0.1

# global training set
train = dict()


@itchat.msg_register([TEXT, SHARING], isGroupChat=True)
def group_reply_text(msg):
    chatroom_id = msg['FromUserName']
    chatroom_name = msg['User']['NickName']
    username = msg['ActualNickName']
    content = ''
    if msg['Type'] == TEXT:
        content = msg['Content']
    elif msg['Type'] == SHARING:
        content = msg['Text']

    # time right now and format YY-mm-dd HH:MM:SS
    time = now()

    # calculate cosine similarity
    value = content_judge(train, content)

    # standard output string
    s = content_write(time, chatroom_id, chatroom_name, username, content, str(value))
    print(s)

    # record every group every information
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(s)

    if value > threshold:
        # if value > threshold then save in corresponding file
        target_ouput(s, chatroom_name, time[:10], content)


def read_stopword(file_path):
    """
    load stop word set 
    :param file_path: stop word set path
    :return: list
    """
    stop_words = list()
    with open(file_path, "r", encoding='utf-8') as f:
        for word in f:
            stop_words.append(word.strip())
    return stop_words


def tokenization(s):
    stop_word = read_stopword("source/stopword.txt")
    target_list = list()
    ss = str()
    for word in s:
        if word.isdigit():
            continue
        ss += word
    seg_list = jieba.cut(ss)
    for word in seg_list:
        if word not in stop_word:
            if word in ' \t\r\n\f\x0a':
                continue
            if len(word) < 2:
                continue
            target_list.append(word)
    return target_list


def term_frequency_train(file_path):
    target_list = list()
    tf_train = dict()
    with open(file_path, 'r', encoding='utf-8') as f:
        for sentence in f:
            target_list = tokenization(sentence)
            for word in target_list:
                if word in tf_train:
                    tf_train[word] += 1
                else:
                    tf_train[word] = 1
    return tf_train


def term_frequency_test(sentence):
    tf_test = dict()
    target_list = tokenization(sentence)
    for word in target_list:
        if word in tf_test:
            tf_test[word] += 1
        else:
            tf_test[word] = 1
    return tf_test


def len_dict(dic):
    tmp = 0
    for t in dic:
        tmp += math.pow(dic[t], 2)
    return math.sqrt(tmp)


def cosine_similarity(tf_train, tf_test):
    """
    calculate content similarity
    :param tf_train: training set
    :param tf_test: test set
    :return: similarity value
    """
    tmp = 0
    flag = 0
    for t in tf_test:
        # filter rental in need content
        if '求' in t:
            flag = 1
            if t == '要求':
                print(t)
                flag = 0
        if t in tf_train:
            tmp += tf_train[t] * tf_test[t]
    n = len_dict(tf_test)*len_dict(tf_train)

    # handle divided by zero
    if n == 0.0:
        return 0.0

    # cosine similarity calculate
    value = tmp / n

    # set rental in need cost
    rental_need_cost = 0.2
    if flag is 1:
        return value - rental_need_cost
    else:
        return value


def content_judge(tf_train, content):
    tf_test = term_frequency_test(content)
    value = cosine_similarity(tf_train, tf_test)

    # set length cost, in case when some key words included
    # but not target content
    length = 40
    length_cost = 0.1

    if len(content) < length:
        value -= length_cost
    return value


def str_new_line(name, value=''):
    if value == '':
        return name + '\n'
    return name + ': ' + value + '\n'


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def content_write(time, chatroom_id, chatroom_name, username, content, value):
    s = str_new_line('start')
    s += str_new_line('时间', time)
    s += str_new_line('群ID', chatroom_id)
    s += str_new_line('群名', chatroom_name)
    s += str_new_line('用户名', username)
    s += str_new_line('内容', content)
    s += str_new_line('阈值', value)
    s += str_new_line('end')
    s += '\n'
    return s


def target_ouput(s, chatroom_name, time_name, content):
    """
    Store target content in txt file, file name is chat room name + date
    if date change, create new file
    """
    directory = 'data/'+time_name
    if not os.path.exists(directory):
        os.makedirs(directory)
    flag = repeat_process(content, chatroom_name, directory)
    if not flag:
        with open(directory+'/'+chatroom_name+'.txt', 'a', encoding='utf-8') as f:
            f.write(s)
    else:
        print("repeat delete"+'\n\n')


def repeat_process(content, chatroom_name, directory):
    """
    check wehther repeat or not
    :param content: msg content
    :param chatroom_name: chat room name
    :param directory: target file path
    :return: True if it repeat otherwise False
    """
    target = read_target_file(directory, chatroom_name)
    hashed_content = hashlib.md5(content.encode('utf-8')).hexdigest()
    if hashed_content in target:
        return True
    else:
        target.append(hashed_content)
        return False


def read_target_file(directory, chatroom_name):
    """
    read exist target file and hash contents
    :param directory: the file path
    :param chatroom_name: chat room name 
    :return: a list include whole hashed value if empty return empty list 
    """
    target = list()
    if os.path.exists(directory+'/'+chatroom_name+'.txt'):
        with open(directory + '/' + chatroom_name + '.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                if line[:2] == '内容':
                    content = line.split(":")[1]
                    content = content.strip()
                    hashed_content = hashlib.md5(content[:].encode('utf-8')).hexdigest()
                    target.append(hashed_content)
    return target


def ex():
    # smtp server address
    smtp_server = "xxx"

    # smtp server port
    port = 587

    # from address, it's better the same with your mail address
    from_address = 'xxx'

    # password, it's better to apply application password
    # then it won't be authentication problem
    my_pass = 'xxx'

    # send to email addresses, saving in list
    to_address = ['xxx', 'xxx']

    # ip address, very important
    host = 'xxx'

    # mail subject
    subject = '提醒：微信号已经登出'

    # mail body
    content = '0'

    ret = True
    try:
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
            from_address,
            str.join(',', to_address),
            Header(subject, 'utf-8').encode(),
            formatdate(),
            content)

        server = smtplib.SMTP(smtp_server, port)  # 发件人邮箱中的SMTP服务器，端口是587
        server.ehlo(name=host)
        server.starttls()
        server.ehlo(name=host)
        server.login(from_address, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(from_address, to_address, msg)  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件

        server.quit()  # 关闭连接
        print("邮件发送成功")
    except smtplib.SMTPException:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
        print("邮件发送失败")
    return ret


if __name__ == '__main__':
    train = term_frequency_train('source/train.txt')
    print('load training set success')
    jieba.set_dictionary("source/dict.txt")
    jieba.initialize()
    # if you want output QR in cmd, try:
    # itchat.auto_login(enableCmdQR=True)
    itchat.auto_login(hotReload=True, exitCallback=ex, enableCmdQR=2)
    itchat.run()


