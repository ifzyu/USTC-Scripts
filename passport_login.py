import io
import re
import PIL
import requests
import pytesseract
import numpy as np


class PassportLogin(object):
    """
    PassportLogin 类用于 CAS 登录认证
    """

    def __init__(self, service: str):
        """
        初始化 PassportLogin 类
        """
        self.passport = f"https://passport.ustc.edu.cn/login?service={service}"
        self.captcha = "https://passport.ustc.edu.cn/validatecode.jsp?type=login"
        self.session = requests.session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def _get_lt(self) -> str:
        """
        获取登录时需要提供的图形验证码
        """
        response = self.session.get(self.captcha)
        img = PIL.Image.open(io.BytesIO(response.content))
        img_array = np.array(img)
        # 创建一个和原图大小相同的全白图像，之后将原图 r 值属于 [0, 70]
        # 且 g 值属于 [40, 140] 且b 值属于[0, 70] 的像素点设为黑色
        new_img = np.ones(img_array.shape, dtype=np.uint8) * 255
        mask = (
            (img_array[:, :, 0] >= 0)
            & (img_array[:, :, 0] <= 70)
            & (img_array[:, :, 1] >= 40)
            & (img_array[:, :, 1] <= 140)
            & (img_array[:, :, 2] >= 0)
            & (img_array[:, :, 2] <= 70)
        )
        new_img[mask] = [0, 0, 0]
        config = "--psm 7 -c tessedit_char_whitelist=0123456789"
        LT = pytesseract.image_to_string(new_img, config=config).strip()
        return LT

    def _get_cas_lt(self) -> str:
        """
        获取登录时需要提供的验证字段
        """
        response = self.session.get(self.passport)
        CAS_LT = re.search(r"LT-\w+", response.text).group()
        return CAS_LT

    def login(self, username: str, password: str) -> bool:
        """
        登录,需要提供用户名、密码
        """
        self.session.cookies.clear()
        try:
            LT = self._get_lt()
            CAS_LT = self._get_cas_lt()
            login_data = {
                "model": "uplogin.jsp",
                "CAS_LT": CAS_LT,
                "showCode": "1",
                "username": username,
                "password": password,
                "LT": LT,
            }
            self.session.post(self.passport, login_data)
            return self.session.cookies.get("TGC") is not None
        except Exception as e:
            print(e)
            return False
