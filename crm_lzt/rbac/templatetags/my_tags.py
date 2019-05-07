from django import template

# 注册我们自定义的标签，只有注册过的标签，系统才能认识你，这是固定写法
register = template.Library()


@register.inclusion_tag("menu.html")
def get_menu(request):

    # 获取当前用户可以放到菜单栏的权限
    menu_permissions_list = request.session.get("menu_permissions_list")

    return {"menu_permissions_list": menu_permissions_list}
