
from rbac.models import *
from django.db import models


class Department(models.Model):
    """
    部门表
    销售部       1001
    人事部       1002

    """
    title = models.CharField(verbose_name='部门名称', max_length=16)
    code = models.IntegerField(verbose_name='部门编号', unique=True, null=False)

    def __str__(self):
        return self.title


class UserInfo(models.Model):
    """
    员工表
    """

    name = models.CharField(verbose_name='员工姓名', max_length=16)
    email = models.EmailField(verbose_name='邮箱', max_length=64)

    user = models.OneToOneField(to=User, on_delete=models.CASCADE)

    depart = models.ForeignKey(verbose_name='部门', to="Department", to_field="code", on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Work(models.Model):
    """
    业务表
    如：
    信息咨询、软件升级、产品维护、it专业服务、集成和开发服务、管理外包服务

    """
    name = models.CharField(verbose_name='业务名称', max_length=32)

    def __str__(self):
        return self.name


class CustomerObj(models.Model):
    """
    客户表
    """
    name = models.CharField(verbose_name='姓名', max_length=16)
    phone = models.CharField(verbose_name='手机号', max_length=64, unique=True, help_text='手机号必须唯一')
    gender_choices = ((1, '男'), (2, '女'))
    gender = models.SmallIntegerField(verbose_name='性别', choices=gender_choices)

    education_choices = (
        (1, '重点大学'),
        (2, '普通本科'),
        (3, '独立院校'),
        (4, '民办本科'),
        (5, '大专'),
        (6, '民办专科'),
        (7, '高中'),
        (8, '其他')
    )
    education = models.IntegerField(verbose_name='学历', choices=education_choices, blank=True, null=True, )
    firm = models.CharField(verbose_name='所属公司', max_length=64, blank=True, null=True)
    address = models.CharField(verbose_name='详细住址', max_length=64, blank=True, null=True)

    work_status_choices = [
        (1, '在职'),
        (2, '无业')
    ]
    work_status = models.IntegerField(verbose_name="职业状态", choices=work_status_choices, default=1, blank=True,
                                      null=True)
    status_choices = [
        (1, "已合作"),
        (2, "未合作")
    ]
    status = models.IntegerField(
        verbose_name="合作状态",
        choices=status_choices,
        default=2,
        help_text=u"选择客户此时的状态"
    )
    consultant = models.ForeignKey(verbose_name="销售顾问", to='UserInfo', related_name='user_consultant',
                                   limit_choices_to={'depart_id': 1001}, on_delete=models.CASCADE)

    work = models.ManyToManyField(verbose_name="咨询业务", to="Work")
    date = models.DateField(verbose_name="咨询日期", auto_now_add=True)
    current_date = models.DateField(verbose_name="当前销售顾问的接单日期", null=True)
    last_consult_date = models.DateField(verbose_name="最后跟进日期", )

    def __str__(self):
        return self.name


class ConsultRecord(models.Model):
    """
    客户跟进记录
    """
    customer = models.ForeignKey(verbose_name="所咨询客户", to='CustomerObj', on_delete=models.CASCADE)
    consultant = models.ForeignKey(verbose_name="跟踪人", to='UserInfo', on_delete=models.CASCADE)
    date = models.DateField(verbose_name="跟进日期", auto_now_add=True)
    note = models.TextField(verbose_name="跟进内容")

    def __str__(self):
        return self.customer.name + ":" + self.consultant.name


class Customer(models.Model):
    """
    客户表（已合作）
    """
    customer = models.OneToOneField(verbose_name='客户信息', to='CustomerObj', on_delete=models.CASCADE)

    username = models.CharField(verbose_name='用户名', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=64)
    emergency_contract = models.CharField(max_length=32, blank=True, null=True, verbose_name='紧急联系人')
    work_list = models.ManyToManyField(verbose_name="合作业务", to='Work', blank=True)
    company = models.CharField(verbose_name='公司', max_length=128, blank=True, null=True)
    location = models.CharField(max_length=64, verbose_name='所在区域', blank=True, null=True)
    date = models.DateField(verbose_name='合作开始时间', help_text='格式yyy-mm-dd', blank=True, null=True)
    memo = models.CharField(verbose_name='备注', max_length=256, blank=True, null=True)

    def __str__(self):
        return self.username


class WorkRecord(models.Model):
    """
    工作记录
    """
    work_obj = models.ForeignKey(verbose_name="业务", to="Work", on_delete=models.CASCADE)
    day_num = models.IntegerField(verbose_name="项目时间", help_text=u"必须为数字")
    date = models.DateField(verbose_name="工作日期", auto_now_add=True)
    manager = models.ForeignKey(verbose_name='项目主管', to='UserInfo', related_name="user_man",
                                limit_choices_to={"depart": 1005}, on_delete=models.CASCADE, default="")
    work_des = models.TextField(verbose_name='工作描述', max_length=500, blank=True, null=True)

    def __str__(self):
        return "{0}(day{1})".format(self.work_obj, self.day_num)


class StaffRecord(models.Model):
    """
    考勤记录
    """
    work_record = models.ForeignKey(verbose_name="项目第几天", to="WorkRecord", on_delete=models.CASCADE)
    staff = models.ForeignKey(verbose_name="负责员工", to='UserInfo', on_delete=models.CASCADE)
    record_choices = (('checked', "已签到"),
                      ('vacate', "请假"),
                      ('late', "迟到"),
                      ('absence', "缺勤"),
                      ('leave_early', "早退"),
                      )
    record = models.CharField("签到记录", choices=record_choices, default="checked", max_length=64)
    score_choices = ((100, 'A+'),
                     (90, 'A'),
                     (85, 'B+'),
                     (80, 'B'),
                     (70, 'B-'),
                     (60, 'C+'),
                     (50, 'C'),
                     (40, 'C-'),
                     (0, ' D'),
                     (-1, 'N/A'),
                     )
    score = models.IntegerField("评分", choices=score_choices, default=-1)
    note = models.CharField(verbose_name="备注", max_length=255, blank=True, null=True)

    def __str__(self):
        return "{0}-{1}".format(self.record, self.staff)


class CustomerDistribute(models.Model):
    """
    客户分布表：一个客户的多种分布状态
    """
    customer = models.ForeignKey("CustomerObj", verbose_name="客户", related_name="customers", on_delete=models.CASCADE)
    consultant = models.ForeignKey(verbose_name="销售顾问", to="UserInfo", limit_choices_to={"depart_id": 1001}, on_delete=models.CASCADE)
    date = models.DateField(verbose_name="日期")
    status = (
        (1, "正在跟进"),
        (2, "已合作"),
        (3, "三天未跟进"),
        (4, "15天未成单"),
    )
    status = models.IntegerField(verbose_name="跟进状态", choices=status, default=1)

    memo = models.CharField(verbose_name="说明", max_length=255)

    def __str__(self):
        return self.customer.name+":"+self.consultant.name





