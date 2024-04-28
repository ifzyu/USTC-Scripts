import pytz
import icalendar
import json
import requests
from icalendar import Calendar, Event
from datetime import datetime, timedelta

from passport_login import PassportLogin


class LibraryReserve:
    """
    LibraryReserve 类用于图书馆研讨室预约相关操作
    """

    def __init__(self, username, password):
        """
        初始化 LibraryReserve 类
        """
        self.username = username
        self.service_url = "http://hs.lib.ustc.edu.cn/account/Login"
        self.appointment_url = "https://hs.lib.ustc.edu.cn/desktopAppointment"
        with open('library.ics', 'rb') as f:
            self.calendar = Calendar.from_ical(f.read())
        self.login_bot = PassportLogin(self.service_url)
        self.session = self.login_bot.session
        self.login(username, password)

    def __del__(self):
        """
        析构函数
        """
        with open('library.ics', 'wb') as f:
            f.write(self.calendar.to_ical())

    def _check_success(self, response: requests.Response) -> bool:
        """
        根据回应检查有没有预约成功
        """
        msg = json.loads(response.text)
        if not msg["message"]:
            print(msg["content"])
            return False
        else:
            state = msg["content"][0]["appointmentState"]
            print(msg["content"][0]["appointmentHint"])
            return state

    def login(self, username: str, password: str) -> bool:
        """
        登录，需要提供用户名、密码
        """
        max_retries = 3
        for _ in range(max_retries):
            is_success = self.login_bot.login(username, password)
            if is_success:
                return True
        return False

    def affirm_appointment(
        self, date: str, start: str, end: str, resource: str, config: dict
    ) -> bool:
        """
        按指定配置发送预约研讨室数据包
        """
        try:
            url = self.appointment_url + "/affirmAppointment"
            data = {
                "PartionID": 38,
                "theme": "【科研讨论】",
                "otherAppointees": "",
                "isChair": False
            }
            data["userId"] = self.username
            data["dateName"] = date
            data["startTime"] = start
            data["endTime"] = end
            data["resourceId"] = config["resDict"][resource]
            response = self.session.post(url, data=data)
            return self._check_success(response)
        except Exception as e:
            print(e)
            return False

    def schedule_appointment(self, delta: int, config: dict) -> bool:
        """
        按指定配置文件预约指定日期的研讨室，并将日程写入 iCalendar
        """
        try:
            tz = pytz.timezone("Asia/Shanghai")
            today = datetime.now(tz).date()
            date = today + timedelta(days=delta)
            weekday = date.weekday()
            date = date.strftime("%Y-%m-%d")
            for start, end in config["schedule"][weekday]:
                for resource in config["resList"]:
                    if self.affirm_appointment(date, start, end, resource, config):
                        event = Event()
                        event.add('summary', '课程讨论')
                        event.add('dtstart', datetime.strptime(date + " " + start, "%Y-%m-%d %H:%M"))
                        event.add('dtend', datetime.strptime(date + " " + end, "%Y-%m-%d %H:%M"))
                        event.add('location', resource)

                        # 将事件添加到日历中
                        self.calendar.add_component(event)
                        break
            return True
        except Exception as e:
            print(e)
            return False

    def appointment(self, config: dict) -> bool:
        """
        临时预约 当前时间--30分钟后 的研讨室
        """
        try:
            tz = pytz.timezone("Asia/Shanghai")
            today = datetime.now(tz).date()
            # date = input("Enter the date (YYYY-MM-DD): ")
            # start = input("Enter the start time (HH:MM): ")
            # end = input("Enter the end time (HH:MM): ")
            # resource = input("Enter the resource (707A): ")
            date = today.strftime("%Y-%m-%d")
            start = (datetime.now(tz) + timedelta(minutes=1)).strftime("%H:%M")
            end = (datetime.now(tz) + timedelta(minutes=31)).strftime("%H:%M")
            resource = "704A"
            return self.affirm_appointment(date, start, end, resource, config)
        except Exception as e:
            print(e)
            return False
