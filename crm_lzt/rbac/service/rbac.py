import re
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponse, redirect, render


class ValidPermission(MiddlewareMixin):

    def process_request(self, request):

        current_path = request.path_info

        # 检查是否属于白名单
        valid_url_list = ['/login/', '/reg/', '/admin/.*']
        for valid_url in valid_url_list:
            ret = re.match(valid_url, current_path)
            if ret:
                return None

        # 检查是否登录
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('/login/')

        permission_dict = request.session.get("permission_dict")

        for item in permission_dict.values():
            for url in item["urls"]:
                reg = "^%s$" % url
                ret = re.match(reg, current_path)

                if ret:
                    print(item["actions"])
                    request.actions = item["actions"]
                    return None

        return HttpResponse("您没有访问权限")
