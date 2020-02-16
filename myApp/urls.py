from django.conf.urls import url
from . import views
import myApp

app_name = 'myApp'

urlpatterns = [
    url(r'^$', views.index),  # 主页

    # 登录页
    url(r'^StudentLogin/$', views.student_login, name = 'StudentLogin'),  # 学生登陆
    url(r'^TeacherLogin/$', views.teacher_login, name = 'TeacherLogin'),  # 教师登陆
    url(r'^ReselectPassword/$', views.reselect_password, name = 'ReselectPassword'),  # 修改密码界面

    # 个人主页
    url(r'^TeacherIndex/$', views.teacher_index, name = 'TeacherIndex'),  # 教师主页
    url(r'^StudentIndex/$', views.student_index, name = 'StudentIndex'),  # 学生主页

    # 添加新学生账号
    url(r'^SelectAddStudentInfo', views.select_add_student_info, name = 'SelectAddStudentInfo'),  # 选择添加学生班级信息
    url(r'^SingleAddStudent', views.single_add_student, name = 'SingleAddStudent'),  # 单独添加学生信息
    # TODO :: 应当先清除session

    # 人脸识别准备
    url(r'^StudentUploadPhoto/$', views.student_upload_photo, name = 'StudentUploadPhoto'),  # 学生上传照片页
    url(r'^LaunchSignIn/$', views.launch_sign_in, name = 'LaunchSignIn'),  # 教师发起签到页
    url(r'^face/$', views.snap, name = 'face'),  # 人脸识别拍照主页
    url(r'^recognition/$', views.recognition, name = 'recognition'),  # 人脸识别结果显示页
    url(r'^ClearSession/$', views.clear_session, name = 'ClearSession'),  # 清除人脸识别造成的session并返回教师主页

    # 辅助
    url(r'^verifycode/$', views.verifycode, name = 'verifycode'),  # 验证码
    url(r'^OutLogin/$', views.out_login, name = 'OutLogin'),  # 注销
    url(r'^favicon.ico/$', views.return_favicon_ico, name = 'favicon'), # 获得favicon.ico
    url(r'^Todo/$', views.todo, name = 'todo'),

    # LaunchSignIn Select标签的三级联动
    url(r'^AjaxGetMajor/$', views.ajax_get_major, name = 'AjaxGetMajor'),  # Ajax根据学院获得专业
    url(r'^AjaxGetGrade/$', views.ajax_get_grade, name = 'AjaxGetGrade'),  # Ajax根据专业获得班级
]

# 404/500
# handler404 = myApp.views.page_not_found
# handler500 = myApp.views.page_error
# !404/500
