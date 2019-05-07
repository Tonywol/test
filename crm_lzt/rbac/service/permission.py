

def initial_session(user, request):

    permissions = user.roles.all().values("permissions__url", "permissions__group_id", "permissions__action").distinct()
    print(permissions)

    permission_dict = {}
    for item in permissions:
        gid = item.get('permissions__group_id')

        if gid not in permission_dict:
            permission_dict[gid] = {
                "urls": [item["permissions__url"], ],
                "actions": [item["permissions__action"], ]
            }
        else:
            permission_dict[gid]["urls"].append(item["permissions__url"])
            permission_dict[gid]["actions"].append(item["permissions__action"])

    print(permission_dict)

    request.session["permission_dict"] = permission_dict

    # 注册菜单权限

    permissions = user.roles.all().values("permissions__url", "permissions__action", "permissions__title").distinct()
    print(permissions)

    menu_permissions_list = []
    for i in permissions:
        if i["permissions__action"] == "list":
            menu_permissions_list.append((i["permissions__url"], i["permissions__title"]))
    print(menu_permissions_list)

    request.session["menu_permissions_list"] = menu_permissions_list



