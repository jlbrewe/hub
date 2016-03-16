from django.contrib import admin

from users.models import UserDetails, UserToken, UserEvent


class UserDetailsAdmin(admin.ModelAdmin):

    list_display = ('id', 'get_username', 'guest', 'builder', 'tester', 'get_last_login')

    def get_username(self, obj):
        return obj.user.username
    get_username.admin_order_field = 'user__username'
    get_username.short_description = 'Username'

    def get_last_login(self, obj):
        return obj.user.last_login
    get_last_login.admin_order_field = 'user__last_login'
    get_last_login.short_description = 'Last login'

admin.site.register(UserDetails, UserDetailsAdmin)


class UserTokenAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'issued', 'expires')

admin.site.register(UserToken, UserTokenAdmin)


class UserEventAdmin(admin.ModelAdmin):

    list_display = ('id', 'datetime', 'user', 'name')

admin.site.register(UserEvent, UserEventAdmin)
