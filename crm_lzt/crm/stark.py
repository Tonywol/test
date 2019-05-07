from django.utils.safestring import mark_safe
from stark.service.stark import site, ModelStark
from .models import *
from django.shortcuts import render, HttpResponse
from django.conf.urls import url

site.register(Department)


class UserConfig(ModelStark):

    list_display = ["name", "email", "depart"]


site.register(UserInfo, UserConfig)
site.register(Work)


class CustomerObjConfig(ModelStark):

    def dis_gender(self, obj=None, header=False):
        if header:
            return "性别"
        return obj.get_gender_display()

    def dis_work(self, obj=None, header=False):
        if header:
            return "咨询业务"
        temp = []
        for work in obj.work.all():
            s = "<a href='' style='border:1px solid #369;padding:3px 6px'><span>%s</span></a>&nbsp;" % work
            temp.append(s)
        return mark_safe("".join(temp))

    def public_customer(self, request):

        # 未合作 且3天未跟进或者15天未成单

        from django.db.models import Q
        import datetime
        now = datetime.datetime.now()

        # 三天未跟进 now-last_consult_date>3   --->last_consult_date<now-3
        # 15天未成单 now-current_date>15   --->current_date<now-15

        delta_day3 = datetime.timedelta(days=3)
        delta_day15 = datetime.timedelta(days=15)
        customer_list = CustomerObj.objects.filter(Q(last_consult_date__lt=now-delta_day3) | Q(current_date__lt=now-delta_day15), status=2)
        print(customer_list)
        return render(request, "public.html", locals())

    def follow(self, request, customer_id):

        user_id = request.session.get("user_id")
        import datetime

        now = datetime.datetime.now()
        delta_day3 = datetime.timedelta(days=3)
        delta_day15 = datetime.timedelta(days=15)
        from django.db.models import Q

        # 更改销售顾问及时间
        ret = CustomerObj.objects.filter(pk=customer_id).filter(
            Q(last_consult_date__lt=now - delta_day3) | Q(current_date=now - delta_day15), status=2).update(
            consultant=user_id, last_consult_date=now, current_date=now)
        if not ret:
            return HttpResponse("已经被跟进了")

        CustomerDistribute.objects.create(customer_id=customer_id, consultant_id=user_id, date=now, status=1)

        return HttpResponse("跟进成功")

    def my_customer(self, request):
        user_id = request.session.get("user_id")
        customer_distribute_list = CustomerDistribute.objects.filter(consultant=user_id)

        return render(request, "my_customer.html", locals())

    def extra_url(self):

        temp = []
        temp.append(url(r"public/", self.public_customer))
        temp.append(url(r"follow/(\d+)/", self.follow))
        temp.append(url(r"my_customer/", self.my_customer))

        return temp

    list_display = ["name", dis_gender, "phone", dis_work,  "consultant"]


site.register(CustomerObj, CustomerObjConfig)


class CustomerConfig(ModelStark):
    list_display = ["customer", "work_list", "company", "date"]


site.register(Customer, CustomerConfig)


class StaffRecordConfig(ModelStark):
    list_display = ["staff", "record", "score"]
    search_fields = ["staff__name"]
    list_filter = ["work_record", "staff"]


site.register(StaffRecord, StaffRecordConfig)


class ConRecordConfig(ModelStark):
    list_display = ["customer", "consultant", "date", "note"]


site.register(ConsultRecord, ConRecordConfig)


class WorkRecordConfig(ModelStark):

    def record(self, obj=None, header=False):
        if header:
            return "工作记录"
        return mark_safe("<a href='/stark/crm/staffrecord/?work_record=%s'>记录</a>" % obj.pk)

    list_display = ["work_obj", "day_num", "manager", record]


site.register(WorkRecord, WorkRecordConfig)


class CusDisConfig(ModelStark):
    list_display = ["customer", "consultant", "status"]


site.register(CustomerDistribute, CusDisConfig)

