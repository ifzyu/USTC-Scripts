import os
import yaml
import argparse

from library_reserve import LibraryReserve


if __name__ == "__main__":
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="中国科大图书馆预约")
    parser.add_argument("delta", type=int, help="指定偏移天数，负数进入开发模式")
    args = parser.parse_args()

    # 优先从环境变量中读取学号和密码，若不存在则要求用户在终端输入
    username = os.environ.get("STUID")
    password = os.environ.get("PASSWORD")

    if username is None or password is None:
        username = input("学号：")
        password = input("密码：")

    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    bot = LibraryReserve(username, password)

    if args.delta < 0:   
        bot.appointment(config)
    else:
        bot.schedule_appointment(args.delta, config)
