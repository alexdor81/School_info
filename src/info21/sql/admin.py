from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import (P2P, XP, Checks, Friends, Peers, Recommendations, Tasks,
                     TimeTracking, TransferredPoints, Verter)

admin.site.register(Peers)
admin.site.register(Tasks)
admin.site.register(Checks)
admin.site.register(P2P)
admin.site.register(Verter)
admin.site.register(TransferredPoints)
admin.site.register(Friends)
admin.site.register(Recommendations)
admin.site.register(XP)
admin.site.register(TimeTracking)

admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
