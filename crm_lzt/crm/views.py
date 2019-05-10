from django.shortcuts import render, HttpResponse
from django.http import JsonResponse

# Create your views here.
from rbac.models import User
from rbac.service.permission import initial_session
from geetest import GeetestLib

pc_geetest_id = "d843e77d51b218eb0a435962c7262a4e"
pc_geetest_key = "40c1f641e7d7d9508777dba65d741ff6"


def login(request):
    if request.method == "POST":
        # print(request.POST)
        # 初始化一个给AJAX返回的数据
        ret = {"status": 0, "msg": ""}
        user = request.POST.get("username")
        pwd = request.POST.get("password")
        # print(user, pwd)
        # 获取极验 滑动验证码相关的参数
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')  # geetest_challenge
        validate = request.POST.get(gt.FN_VALIDATE, '')  # geetest_validate
        seccode = request.POST.get(gt.FN_SECCODE, '')  # geetest_seccode
        status = request.session.get(gt.GT_STATUS_SESSION_KEY)
        user_id = request.session.get("user_id")
        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        if result:
            user = User.objects.filter(name=user, pwd=pwd)
            if user:
                user = user.first()
                request.session["user_id"] = user.pk
                initial_session(user, request)
                return JsonResponse({"code": 0, "msg": "/stack/crm/workrecord"})
            else:
                # 用户名密码错误
                ret["status"] = 1
                ret["msg"] = "用户名或密码错误！"
        else:
            ret["status"] = 1
            ret["msg"] = "验证码错误"
        return JsonResponse(ret)
    return render(request, 'login.html')


def get_geetest(request):
    # 处理极验 获取验证码的视图
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)


# def login(request):
#     if request.method == "POST":
#         user = request.POST.get("username")
#         pwd = request.POST.get("password")
#         user = User.objects.filter(name=user, pwd=pwd).first()
#         if user:
#             request.session["user_id"] = user.pk
#             initial_session(user, request)
#             return HttpResponse("OK")
#             # return render(request, 'show.html', {"user": user})
#
#     return render(request, 'login.html')


