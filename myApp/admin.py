from django.contrib import admin
from myApp import models
from aip import AipFace
from .views import get_en_name

# Register your models here.

class DetailGradeSubInline(admin.TabularInline):
    model = models.UserInformation
    extra = 0


@admin.register(models.IdentityInformation)
class IdentityAdmin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(models.CollegeInformation)
class CollegeAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = ['pk', 'college_name']


@admin.register(models.MajorInformation)
class MajorAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = ['pk', 'major_name']


@admin.register(models.GradeInformation)
class GradeAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = ['pk', 'grade_name']


@admin.register(models.DetailGradeInformation)
class DetailGradeAdmin(admin.ModelAdmin):
    def show_info(self):
        return "%s-%s-%s" % (self.college_id.college_name, self.major_id.major_name, self.grade_id.grade_name)

    list_per_page = 50
    inlines = [DetailGradeSubInline]
    actions_on_top = False
    actions_on_bottom = False
    list_filter = ['college_id__college_name']
    search_fields = ['college_id__college_name', 'major_id__major_name', 'grade_id__grade_name']
    list_display = [show_info, 'student_num']
    list_editable = ['student_num']

    def save_model(self, request, obj, form, change):
        # 每当创建一个准确班级的时候，在人脸库中加入对应组
        college_id = str(obj.college_id.id)
        major_id = str(obj.major_id.id)
        grade_id = str(obj.grade_id.id)
        app_id = '14807296'
        api_key = 'HrRWN5CIoqfr2Xje4SwUdKdK'
        secret_key = 'fGupsKW4qtIrqYW3bA5ToiLk19oO483X'
        client = AipFace(appId = app_id, apiKey = api_key, secretKey = secret_key)
        group_id_list = college_id + major_id + grade_id
        client.groupAdd(group_id_list)
        super(DetailGradeAdmin, self).save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # 每当删除一个准确班级的时候，在人脸库中删除对应组
        college_id = str(obj.college_id.id)
        major_id = str(obj.major_id.id)
        grade_id = str(obj.grade_id.id)
        app_id = '14807296'
        api_key = 'HrRWN5CIoqfr2Xje4SwUdKdK'
        secret_key = 'fGupsKW4qtIrqYW3bA5ToiLk19oO483X'
        client = AipFace(appId = app_id, apiKey = api_key, secretKey = secret_key)
        group_id_list = college_id + major_id + grade_id
        client.groupDelete(group_id_list)
        super(DetailGradeAdmin, self).delete_model(request, obj)


@admin.register(models.SignInformation)
class SignAdmin(admin.ModelAdmin):
    list_per_page = 50


@admin.register(models.UserInformation)
class UserAdmin(admin.ModelAdmin):
    def gender(self):
        if self.gender is True:
            return '女'
        else:
            return '男'

    def show_identity(self):
        if self.identity.role_name == 'Teacher':
            return '教师'
        else:
            return '学生'

    list_per_page = 40
    list_display = ['name', gender, show_identity, 'grade', 'account', 'password']
    list_filter = ['identity']
    search_fields = ['name']
    list_editable = ['grade']
    fields = ['account', 'password', 'name', 'gender', 'identity', 'grade', 'new_sign', 'isDelete']

    def delete_model(self, request, obj):
        if obj.identity.role_name == 'Student':
            app_id = '14807296'
            api_key = 'HrRWN5CIoqfr2Xje4SwUdKdK'
            secret_key = 'fGupsKW4qtIrqYW3bA5ToiLk19oO483X'
            client = AipFace(appId = app_id, apiKey = api_key, secretKey = secret_key)

            user_id = get_en_name(obj.name)
            college_id = str(obj.college_id.id)
            major_id = str(obj.major_id.id)
            grade_id = str(obj.grade_id.id)
            group_id_list = college_id + major_id + grade_id

            client.deleteUser(user_id = user_id, group_id = group_id_list)
            super(UserAdmin, self).delete_model(request, obj)
