from stark.service.stark import site
from .models import *


site.register(User)
site.register(Role)
site.register(Permission)
site.register(PermissionGroup)




