from django.conf.urls import url
from django.shortcuts import HttpResponse, render, redirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.forms import ModelForm
from stark.utils.page import Pagination
from django.db.models import Q
from django.db.models.fields.related import ManyToManyField, ForeignKey


class ShowList(object):

    def __init__(self, config, data_list, request):
        self.config = config
        self.data_list = data_list
        self.request = request
        # 分页
        data_count = self.data_list.count()
        current_page = int(self.request.GET.get("page", 1))
        base_path = self.request.path

        self.pagination = Pagination(current_page, data_count, base_path, self.request.GET, per_page_num=3, pager_count=11, )
        self.page_data = self.data_list[self.pagination.start:self.pagination.end]
        # actions
        self.actions = self.config.new_actions()

    def get_filter_tags(self, request):
        print("list_filter:", self.config.list_filter)
        link_dic = {}

        import copy

        for filter_field in self.config.list_filter:
            params = copy.deepcopy(self.request.GET)

            cid = self.request.GET.get(filter_field, 0)

            print("filter_field", filter_field)
            # 通过字符串拿到字段对象
            filter_field_obj = self.config.model._meta.get_field(filter_field)
            print("filter_field_obj", filter_field_obj)
            print(type(filter_field_obj))
            # print("rel...",filter_field_obj.rel.to.objects.all())

            if isinstance(filter_field_obj, ForeignKey) or isinstance(filter_field_obj, ManyToManyField):
                 data_list = filter_field_obj.rel.to.objects.all()
            else:
                 data_list = self.config.model.objects.all().values("pk", filter_field)

            temp = []
            # 处理 全部标签
            if params.get(filter_field):
                del params[filter_field]
                temp.append("<a href='?%s'>全部</a>" % params.urlencode())
            else:
                temp.append("<a  class='active' href='#'>全部</a>")

            # 处理 数据标签
            for obj in data_list:
                if isinstance(filter_field_obj, ForeignKey) or isinstance(filter_field_obj, ManyToManyField):
                    pk = obj.pk
                    text = str(obj)
                    params[filter_field] = pk
                else:  # data_list= [{"pk":1,"title":"go"},....]
                    print("========")
                    pk = obj.get("pk")
                    text = obj.get(filter_field)
                    params[filter_field] = text

                _url = params.urlencode()
                if cid == str(pk) or cid == text:
                    link_tag = "<a class='active' href='?%s'>%s</a>" % (_url, text)
                else:
                    link_tag = "<a href='?%s'>%s</a>" % (_url, text)
                temp.append(link_tag)

            link_dic[filter_field] = temp

        return link_dic

    def get_action_list(self):
        temp = []
        for action in self.actions:
            temp.append({
                "name": action.__name__,
                "desc": action.short_description,
            })  # [{"name":""patch_init,"desc":"批量初始化"}]

        return temp

    def get_header(self):

        # 构建表头
        header_list = []
        print("header", self.config.new_list_play())  # [checkbox,"id","name","age",edit ,deletes]

        for field in self.config.new_list_play():
            if callable(field):
                val = field(self.config, header=True)
                header_list.append(val)
            else:
                if field == "__str__":
                    header_list.append(self.config.model._meta.model_name.upper())
                else:
                    val = self.config.model._meta.get_field(field).verbose_name
                    header_list.append(val)

        return header_list

    def get_body(self):
        # 构建表单数据
        new_data_list = []
        for obj in self.page_data:

            temp = []
            for field in self.config.new_list_play():  # [checkbox,"id","name","age",edit ,deletes]

                # 判断self.list_display中是字段还是可调用的函数
                if callable(field):
                    val = field(self.config, obj)
                else:
                    try:
                        field_obj = self.config.model._meta.get_field(field)
                        if isinstance(field_obj, ManyToManyField):
                            ret = getattr(obj, field).all()
                            t = []
                            for mobj in ret:
                                t.append(str(mobj))
                            val = ",".join(t)
                        else:
                            print("====>", field_obj.choices)
                            if field_obj.choices:
                                val = getattr(obj, "get_" + field + "_display")
                            else:
                                val = getattr(obj, field)
                            if field in self.config.list_display_links:
                                # "app01/userinfo/(\d+)/change"
                                _url = self.config.get_change_url(obj)

                                val = mark_safe("<a href='%s'>%s</a>" % (_url, val))

                    except Exception as e:
                        val = getattr(obj, field)

                temp.append(val)

            new_data_list.append(temp)

        return new_data_list


class ModelStark(object):
    list_display = ["__str__", ]
    list_display_links = []
    modelform_class = None
    search_fields = []
    actions = []
    list_filter = []

    def __init__(self, model, site):
        self.model = model
        self.site = site

    def patch_delete(self, request, queryset):
        queryset.delete()

    patch_delete.short_description = "批量删除"

    def edit(self, obj=None, header=False):
        if header:
            return "操作"
        _url = self.get_change_url(obj)
        return mark_safe("<a href='%s'>编辑<a/>" % _url)

    def deletes(self, obj=None, header=False):
        if header:
            return "操作"
        _url = self.get_delete_url(obj)
        return mark_safe("<a href='%s'>删除<a/>" % _url)

    def checkbox(self, obj=None, header=False):
        if header:
            return mark_safe("<input class='choice' type='checkbox' style='zoom:80%'>")
        return mark_safe("<input class='choice_item' type='checkbox' style='zoom:80px' name='selected_pk' value='%s'>" % obj.pk)

    def get_modelform_class(self):
        if not self.modelform_class:
            class ModelFormDemo(ModelForm):

                class Meta:
                    model = self.model
                    fields = "__all__"

            return ModelFormDemo
        else:
            return self.modelform_class

    def get_new_form(self, form):
        for b_field in form:
            from django.forms.boundfield import BoundField
            print(b_field.field)  # 字段对象
            print("name", b_field.name)  # 字段名（字符串）
            print(type(b_field.field))  # 字段类型
            from django.forms.models import ModelChoiceField
            if isinstance(b_field.field, ModelChoiceField):
                b_field.is_pop = True

                # print("=======>", b_field.field.queryset.model)  # 一对多或者多对多字段的关联模型表

                related_model_name=b_field.field.queryset.model._meta.model_name
                related_app_label=b_field.field.queryset.model._meta.app_label

                _url = reverse("%s_%s_add" % (related_app_label, related_model_name))
                b_field.url = _url+"?pop_res_id=id_%s" % b_field.name
        return form

    def add_view(self, request):
        ModelFormDemo = self.get_modelform_class()
        form = ModelFormDemo()
        form = self.get_new_form(form)

        if request.method == "POST":
            form = ModelFormDemo(request.POST)
            if form.is_valid():
                obj = form.save()

                pop_res_id = request.GET.get("pop_res_id")

                if pop_res_id:
                    res = {"pk": obj.pk, "text": str(obj), "pop_res_id": pop_res_id}

                    return render(request, "pop.html", {"res": res})
                else:
                    return redirect(self.get_list_url())

        return render(request, 'add_view.html', locals())

    def delete_view(self, request, id):

        url = self.get_list_url()
        if request.method == "POST":
            self.model.objects.filter(pk=id).delete()
            return redirect(url)

        return render(request, 'delete_view.html', locals())

    def change_view(self, request, id):

        demo = self.get_modelform_class()
        edit_obj = self.model.objects.filter(pk=id).first()

        if request.method == "POST":
            form = demo(request.POST, instance=edit_obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, 'change_view.html', locals())

        form = demo(instance=edit_obj)
        return render(request, 'change_view.html', locals())

    def get_add_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_add" % (app_label, model_name))

        return _url

    def get_delete_url(self, obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_delete" % (app_label, model_name), args=(obj.pk,))

        return _url

    def get_change_url(self, obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_change" % (app_label, model_name), args=(obj.pk,))

        return _url

    def get_list_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_show" % (app_label, model_name))

        return _url

    def new_list_play(self):

        temp = []
        temp.append(ModelStark.checkbox)
        temp.extend(self.list_display)
        if not self.list_display_links:
            temp.append(ModelStark.edit)
        temp.append(ModelStark.deletes)

        return temp

    def new_actions(self):

        temp = []
        temp.append(self.patch_delete)
        temp.extend(self.actions)

        return temp

    def get_search_condition(self, request):
        # 创建Q对象
        search_connection = Q()

        # 如果用户有自定义的查询字段,我们就走这个if下面的代码
        if self.search_fields:
            key_word = request.GET.get("k", "")

            if key_word:
                search_connection.connector = "or"
                for search_field in self.search_fields:
                    search_connection.children.append((search_field + "__contains", key_word))

        return search_connection

    def get_filter_condition(self, request):
        filter_condition = Q()

        for filter_field, val in request.GET.items():
            if filter_field in self.list_filter:
                filter_condition.children.append((filter_field, val))

        return filter_condition

    def show(self, request):

        if request.method == "POST":
            # print(request.POST)
            action = request.POST.get("action")
            selected_pk = request.POST.getlist("selected_pk")
            action_func = getattr(self, action)
            # pk__in查询出多个id的对象
            queryset = self.model.objects.filter(pk__in=selected_pk)
            ret = action_func(request, queryset)

        # 获取search的Q对象
        search_connection = self.get_search_condition(request)

        # 获取filter构建Q对象

        filter_condition = self.get_filter_condition(request)

        # 筛选获取当前表所有数据
        data_list = self.model.objects.all().filter(search_connection).filter(filter_condition)

        # 通过show_list来展示页面
        show_list = ShowList(self, data_list, request)

        # 添加一个查看url
        add_url = self.get_add_url()

        return render(request, "show.html", locals())

    def extra_url(self):

        return []

    def get_urls2(self):
        temp = []

        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        temp.append(url(r"^add/", self.add_view, name="%s_%s_add" % (app_label, model_name)))
        temp.append(url(r"^(\d+)/delete/", self.delete_view, name="%s_%s_delete" % (app_label, model_name)))
        temp.append(url(r"^(\d+)/change/", self.change_view, name="%s_%s_change" % (app_label, model_name)))
        temp.append(url(r"^$", self.show, name="%s_%s_show" % (app_label, model_name)))

        # 扩展url
        temp.extend(self.extra_url())
        return temp

    @property
    def urls2(self):

        return self.get_urls2(), None, None


class StarkSite(object):
    def __init__(self):
        self._registry = {}

    def register(self, model, stark_class=None):
        if not stark_class:
            stark_class = ModelStark

        self._registry[model] = stark_class(model, self)

    def get_urls(self):
        # print(self._registry.items())
        temp = []

        for model, stark_class_obj in self._registry.items():
            model_name = model._meta.model_name
            app_label = model._meta.app_label
            # 分发增删改查
            temp.append(url(r"^%s/%s/" % (app_label, model_name), stark_class_obj.urls2))

        return temp

    @property
    def urls(self):

        return self.get_urls(), None, None


site = StarkSite()









