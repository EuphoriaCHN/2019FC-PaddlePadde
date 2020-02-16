from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from . import models
from aip import AipFace
from pypinyin import lazy_pinyin

import json


# Create your views here.

# 获得中文名对应的英文名
# 格式：王钦弘  -->  WangQinhong
def get_en_name(zh_name):
    en_list = lazy_pinyin(zh_name)
    xing = en_list[0]
    ming = ""
    for y in en_list[1:]:
        ming += y
    en = xing.title().lstrip() + ming.title().lstrip()
    en.title().lstrip()
    return en


# 检查登陆信息
def check_login(request, account, password, verify_code, identity):
    # 先比对验证码，CSRF
    if verify_code != request.session['verify_code'].upper():
        return False
    # 从数据库中拿account和password去比对
    try:
        models.UserInformation.objects.get(account = account, password = password, identity = identity)
    except (models.UserInformation.DoesNotExist, models.UserInformation.MultipleObjectsReturned):
        return False
    return True


# 检查为了人脸识别签到所选择的学院-专业-班级信息是否正确
# 并且检查班级人数是否合法
# CMG: College Major Grade
def check_select_cmg_info(request, college, major, grade):
    try:
        grade_info = list(models.DetailGradeInformation.objects.values().filter(college_id__college_name = college,
                                                                                major_id__major_name = major,
                                                                                grade_id__grade_name = grade))
    except models.DetailGradeInformation.DoesNotExist:
        print("Error in views.py 48 : DetailGradeInformation.DoesNotExist")
        return False
    if grade_info[0]['student_num'] < 1:
        # 班级人数非法
        print("Error in view.py 52 : Does not have any Student in this grade")
        return False
    else:
        # 设置session，为了签到页面使用
        request.session['sign_college'] = college
        request.session['sign_major'] = major
        request.session['sign_grade'] = grade
        request.session['sign_student_num'] = grade_info[0]['student_num']
        # 超长代码段来了！
        sign_students_info = {}
        temp_list = []
        students_list = list(models.UserInformation.objects.all().filter(
            grade = models.DetailGradeInformation.objects.get(
                college_id__college_name = college,
                major_id__major_name = major,
                grade_id__grade_name = grade),
            identity = 'Student').values())
        for student in students_list:
            temp_list.append(student['name'])
            temp_list.append(False)
            sign_students_info[get_en_name(student['name'])] = temp_list
            temp_list = []
        # 至此已经获得了对应签到班级的所有学生姓名
        # 存储在了一个字典中，英文名:[中文名，是否签到(default=False)]
        request.session['sign_student_info'] = sign_students_info
    return True


# 为了发起签到而做准备
def ready_to_face_sign(request, college, major, grade):
    # 设置签到日志
    teacher_name = request.session['user_name']
    teacher_id = models.UserInformation.objects.get(name = teacher_name, identity = 'Teacher')
    grade_info = models.DetailGradeInformation.objects.get(college_id__college_name = college,
                                                           major_id__major_name = major,
                                                           grade_id__grade_name = grade)
    new_sign = models.SignInformation.make_new_sign(initiator = teacher_id.id,
                                                    reached = request.session['sign_student_num'],
                                                    target = grade_info)
    new_sign.save()
    request.session['sign_id'] = new_sign.id
    print("Set new sign Successful!")


# 主页
def index(request):
    if request.method == 'POST':
        return render(request, 'myApp/todo.html', None)
    logout(request)
    return render(request, 'myApp/index.html', None)


# 学生登陆页
def student_login(request):
    login_fail = False
    if request.method == "POST":
        account = request.POST.get("form-username")
        password = request.POST.get("form-password")
        verify_code = request.POST.get("form-verifycode").upper()
        if check_login(request, account, password, verify_code, identity = 'Student'):
            this_student = models.UserInformation.objects.get(account = account)
            user_name = this_student.name
            new_sign = this_student.new_sign
            request.session['user_name'] = user_name
            request.session['user_account'] = account
            request.session.set_expiry(0)
            # 检查是否第一次登陆并令其修改密码
            if new_sign is True:
                return HttpResponseRedirect("/ReselectPassword/?identity=Student")
            return HttpResponseRedirect("/StudentIndex/")
        else:
            login_fail = True
    elif request.method == "GET":
        login_fail = False

    return render(request, 'myApp/StudentsLogin.html', {'login_fail': login_fail})


# 教师登录页
def teacher_login(request):
    login_fail = False
    if request.method == "POST":
        account = request.POST.get("form-username")
        password = request.POST.get("form-password")
        verify_code = request.POST.get("form-verifycode").upper()
        if check_login(request, account, password, verify_code, identity = 'Teacher'):
            this_teacher = models.UserInformation.objects.get(account = account)
            user_name = this_teacher.name
            new_sign = this_teacher.new_sign
            request.session['user_name'] = user_name
            request.session['user_account'] = account
            request.session.set_expiry(0)
            # 检查是否第一次登陆并令其修改密码
            if new_sign is True:
                return HttpResponseRedirect("/ReselectPassword/?identity=Teacher")
            return HttpResponseRedirect("/TeacherIndex/")
        else:
            login_fail = True
    elif request.method == "GET":
        login_fail = False
    return render(request, 'myApp/TeachersLogin.html', {'login_fail': login_fail})


# 学生个人主页
def student_index(request):
    if request.method == 'POST':
        return render(request, 'myApp/todo.html', None)
    user_name = request.session.get('user_name', default = None)
    return render(request, 'myApp/StudentIndex.html', {"user_name": user_name})


# 教师个人主页
def teacher_index(request):
    if request.method == 'POST':
        return render(request, 'myApp/todo.html', None)
    user_name = request.session.get('user_name', default = None)
    return render(request, 'myApp/TeacherIndex.html', {"user_name": user_name})


# 下面的三个函数：
# LaunchSignIn、AjaxGetMajor、AjaxGetGrade
# 于2019/02/17 凌晨 3:37 实现
# 在经历了无数次老泪纵横于心态爆炸
# 终于实现了，谨此纪念
# 救命稻草：
# Django web开发中的二级联动select 列表的简单实现方法
# https://blog.csdn.net/qq_42469759/article/details/82834264
#                                               --- 王钦弘

def launch_sign_in(request):
    select_fail = False
    user_name = request.session.get('user_name', default = None)
    college_list = []
    if request.method == 'POST':
        # 确认信息后发起签到
        college = request.POST.get('college_name', default = None)
        major = request.POST.get('major_name', default = None)
        grade = request.POST.get('grade_name', default = None)
        if check_select_cmg_info(request, college, major, grade):
            # 为发起签到做准备
            ready_to_face_sign(request, college, major, grade)
            return HttpResponseRedirect('/face/')
        else:
            print("check false")
            select_fail = True
    elif request.method == 'GET':
        select_fail = False
        try:
            college_list = models.DetailGradeInformation.objects.all().values('college_id__college_name').distinct()
        except models.DetailGradeInformation.DoesNotExist:
            return render(request, 'myApp/LaunchSignIn.html', {"user_name": user_name})
    return render(request, 'myApp/LaunchSignIn.html',
                  {"user_name": user_name,
                   "college_list": college_list,
                   "select_fail": select_fail})


def ajax_get_major(request):
    major_result = 0
    if request.method == 'GET':
        college_select = request.GET.get('select_college', None)
        # print('get college from ajax "%s"' % (college_select))
        if college_select:
            data = list(models.DetailGradeInformation.objects.filter(
                college_id__college_name = college_select).values('major_id__major_name').distinct())
            major_result = json.dumps(data)
            # print(major_result)
    return HttpResponse(major_result, "application/json")


def ajax_get_grade(request):
    grade_result = 0
    if request.method == 'GET':
        major_select = request.GET.get('select_major', None)
        # print('get major from ajax "%s"' % (major_select))
        if major_select:
            data = list(models.DetailGradeInformation.objects.filter(
                major_id__major_name = major_select).values('grade_id__grade_name').distinct())
            grade_result = json.dumps(data)
            # print(grade_result)
    return HttpResponse(grade_result, "application/json")


# 人脸识别签到页
def face(photo_image, group_id_list):
    app_id = '14807296'
    api_key = 'HrRWN5CIoqfr2Xje4SwUdKdK'
    secret_key = 'fGupsKW4qtIrqYW3bA5ToiLk19oO483X'
    client = AipFace(appId = app_id, apiKey = api_key, secretKey = secret_key)

    image_type = "BASE64"
    # groupIdList = "001"
    options = dict()
    options['liveness_control'] = 'LOW'
    options['quality_control'] = 'NORMAL'
    # photoImage = base64.b64encode(photoImage)
    result = client.search(photo_image, image_type, group_id_list, options)
    return result


# 获得学生当前人脸库中有多少照片
def get_student_photo_numbers(requset, group_id_list):
    app_id = '14807296'
    api_key = 'HrRWN5CIoqfr2Xje4SwUdKdK'
    secret_key = 'fGupsKW4qtIrqYW3bA5ToiLk19oO483X'
    client = AipFace(appId = app_id, apiKey = api_key, secretKey = secret_key)

    user_id = get_en_name(str(requset.session.get('user_name')))

    return len(client.faceGetlist(user_id = user_id, group_id = group_id_list)['result']['face_list'])


# 增加照片
def add_student_photo(request, photo_data, group_id_list, user_id):
    app_id = '14807296'
    api_key = 'HrRWN5CIoqfr2Xje4SwUdKdK'
    secret_key = 'fGupsKW4qtIrqYW3bA5ToiLk19oO483X'
    client = AipFace(appId = app_id, apiKey = api_key, secretKey = secret_key)

    try:
        photo_num = get_student_photo_numbers(request, group_id_list)
    except Exception:
        photo_num = 0
    if photo_num > 0:
        import random
        face_list = client.faceGetlist(user_id = user_id, group_id = group_id_list)
        random_face = face_list['result']['face_list'][random.randrange(0, photo_num)]['face_token']
        result = client.match([{
            "image": random_face,
            "image_type": 'FACE_TOKEN'
        }, {
            "image": photo_data,
            "image_type": 'BASE64',
        }])
        # print(result)
        if result['result']['score'] < 60:
            return None

    image_type = "BASE64"
    options = dict()
    options["user_info"] = user_id
    options["quality_control"] = "LOW"
    options["liveness_control"] = "NORMAL"
    return client.addUser(photo_data, image_type, group_id_list, user_id, options)


# 处理截图页
def snap(request):
    if request.method == "POST":
        photo_data = request.body.decode()
        photo_data = str(photo_data[37:-2])  # 截取出对应的BASE64
        college_id = str(models.CollegeInformation.objects.get(college_name = request.session.get('sign_college')).id)
        major_id = str(models.MajorInformation.objects.get(major_name = request.session.get('sign_major')).id)
        grade_id = str(models.GradeInformation.objects.get(grade_name = request.session.get('sign_grade')).id)
        group_id_list = college_id + major_id + grade_id
        result = face(photo_data, group_id_list)
        if result is None:  # 在人脸库中没有找到这个人
            return HttpResponse("签到失败！请重新拍照!")
        elif result['error_code'] != 0:
            return HttpResponse("签到失败！请重新拍照!")
        elif result['result']['user_list'][0]['score'] < 60:
            return HttpResponse("签到失败！请重新拍照!")
        else:
            sign_dict = request.session.get('sign_student_info')
            if sign_dict[result['result']['user_list'][0]['user_id']][1] is True:  # 这个学生已经签过到了！
                return HttpResponse("你已经签到过了！请勿重复签到！")
            else:
                sign_info = models.SignInformation.objects.get(pk = request.session.get('sign_id'))
                sign_info.actual += 1
                sign_info.save()
                user_id = sign_dict[result['result']['user_list'][0]['user_id']][0]
                sign_dict[result['result']['user_list'][0]['user_id']][1] = True  # 将该学生标记成已经签到
                request.session['sign_student_info'] = sign_dict  # 并保存session
                return HttpResponse("签到成功！学生：%s" % user_id)
        # return HttpResponse("RedBeenMilkTee")
        # 不要问为什么是红豆牛奶
        # 感谢冯娜小姐姐提供的编程思想和核心代码
    # else:
    elif request.method == "GET":
        sign_college = request.session.get('sign_college')
        sign_major = request.session.get('sign_major')
        sign_grade = request.session.get('sign_grade')
        sign_info = models.SignInformation.objects.get(pk = request.session.get('sign_id'))
        reached = sign_info.reached
        actual = sign_info.actual

    return render(request, 'myApp/face.html',
                  {'sign_college': sign_college,
                   'sign_major': sign_major,
                   'sign_grade': sign_grade,
                   'reached': reached,
                   'actual': actual,
                   'teacher_name': request.session.get('user_name')})


# 学生上传照片页
def student_upload_photo(request):
    this_student = models.UserInformation.objects.get(account = request.session.get('user_account'))
    college = this_student.grade.college_id
    major = this_student.grade.major_id
    grade = this_student.grade.grade_id
    have_photos = 0
    if request.method == "POST":
        photo_data = request.body.decode()
        photo_data = str(photo_data[37:-2])  # 截取出对应的BASE64
        college_id = str(college.id)
        major_id = str(major.id)
        grade_id = str(grade.id)
        group_id_list = college_id + major_id + grade_id
        user_id = get_en_name(request.session.get('user_name'))
        try:
            print(group_id_list, user_id)
            result = add_student_photo(request = request, photo_data = photo_data, group_id_list = group_id_list,
                                       user_id = user_id)
            if result is None:  # 添加失败
                print("result is None!")
                return HttpResponse("添加失败")
            elif result['error_code'] != 0:
                print(result['error_code'])
                return HttpResponse("添加失败")
            else:
                return HttpResponse("添加成功")
        except Exception:
            print("Exception ERROR!")
            return HttpResponse("添加失败")
    elif request.method == "GET":
        try:
            have_photos = get_student_photo_numbers(request, str(college.id) + str(major.id) + str(grade.id))
        except Exception:
            print("Not Find Any Face in Group %s" % (str(college.id) + str(major.id) + str(grade.id)))
            have_photos = 0
    return render(request, 'myApp/StudentUploadPhoto.html',
                  {'user_name': this_student.name,
                   'college': college.college_name,
                   'major': major.major_name,
                   'grade': grade.grade_name,
                   'have_photos': have_photos})


# 返回本次人脸签到的结果
def recognition(request):
    user_name = request.session.get('user_name')  # 签到发起人
    sign_college = request.session.get('sign_college')  # 签到学院
    sign_major = request.session.get('sign_major')  # 签到专业
    sign_grade = request.session.get('sign_grade')  # 签到班级
    sign_info = models.SignInformation.objects.get(pk = request.session.get('sign_id'))  # 签到id
    reached = sign_info.reached  # 签到应到人数
    actual = sign_info.actual  # 签到实到人数
    sign_dict = request.session.get('sign_student_info')  # 签到学生详细信息
    signed_list = []
    unsigned_list = []
    for i in sign_dict:
        if sign_dict[i][1] is True:
            signed_list.append(sign_dict[i][0])
        else:
            unsigned_list.append(sign_dict[i][0])
    return render(request, 'myApp/FaceAnswer.html',
                  {'teacher_name': user_name,
                   'sign_college': sign_college,
                   'sign_major': sign_major,
                   'sign_grade': sign_grade,
                   'reached': reached,
                   'actual': actual,
                   'signed_list': signed_list,
                   'unsigned_list': unsigned_list})


# 生成验证码
def verifycode(request):
    # 引入画布模块
    from PIL import Image, ImageDraw, ImageFont
    # 引入随机数模块
    import random
    # 定义画布背景色和宽高
    bgcolor = (random.randrange(20, 100), random.randrange(20, 100), random.randrange(20, 100))
    width = 100
    height = 50
    # 创建画面对象
    im = Image.new('RGB', (width, height), bgcolor)
    # 创建画笔对象
    draw = ImageDraw.Draw(im)
    for i in range(0, 100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill = fill)
    # 定义验证码的备选值
    str_dictionary = '0123456789QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'
    rand_str = ''
    for i in range(0, 4):
        rand_str += str_dictionary[random.randrange(0, len(str_dictionary))]
    # 构造字体对象
    # 字体位置：
    # Windwos: C:\Windows\Fonts\
    # Arch Linux: /usr/share/fonts/
    font = ImageFont.truetype(r'C:\Windows\Fonts\AdobeArabic-Bold.otf', 40)  # Windows
    # font = ImageFont.truetype(r'/usr/share/fonts/adobe-source-code-pro/SourceCodePro-It.otf', 40) # Linux 服务器
    # 构造字体颜色
    fontcolor1 = (255, random.randrange(0, 255), random.randrange(0, 255))
    fontcolor2 = (255, random.randrange(0, 255), random.randrange(0, 255))
    fontcolor3 = (255, random.randrange(0, 255), random.randrange(0, 255))
    fontcolor4 = (255, random.randrange(0, 255), random.randrange(0, 255))
    # 绘制四个字
    draw.text((5, 2), rand_str[0], font = font, fill = fontcolor1)
    draw.text((25, 2), rand_str[1], font = font, fill = fontcolor2)
    draw.text((50, 2), rand_str[2], font = font, fill = fontcolor3)
    draw.text((75, 2), rand_str[3], font = font, fill = fontcolor4)
    # 释放画笔
    del draw
    # 存到session，用于进一步验证
    request.session['verify_code'] = rand_str
    request.session.set_expiry(300)  # TODO :: 验证码失效时间（说不定还能干点其他的事？）
    # 内存文件操作
    import io
    buf = io.BytesIO()
    # 将图片保存在内存中，格式为png
    im.save(buf, 'png')
    # 将图片在内存中的数据返回给客户端，MIME类型为图片png
    return HttpResponse(buf.getvalue(), 'image/png')


# 注销
def out_login(request):
    logout(request)
    return HttpResponseRedirect('/')


# 清除Session
def clear_session(request):
    user_name = request.session.get('user_name')
    logout(request)
    request.session['user_name'] = user_name
    request.session.set_expiry(0)
    return HttpResponseRedirect('/TeacherIndex/')


# 修改密码界面
def reselect_password(request):
    if models.UserInformation.objects.get(account = request.session['user_account']).new_sign is True:
        why_select = '检测到您第一次登陆'
    else:
        why_select = '在这里修改你的密码'
    user_identity = ''
    if request.method == 'POST':
        user = models.UserInformation.objects.get(account = request.session['user_account'])
        old_password = request.POST.get('form-password-old')
        new_password = request.POST.get('form-password-new')
        new_password_again = request.POST.get('form-password-again')
        verifycode_input = request.POST.get('form-verifycode').upper()
        verify_code = request.session.get('verify_code').upper()
        if user.password == old_password and new_password == new_password_again and \
                old_password != new_password and verifycode_input == verify_code:
            user.password = new_password
            if user.new_sign is True and user.identity.role_name == 'Student':  # 如果是学生并且第一次登陆
                user.new_sign = False
                user.save()
                return HttpResponseRedirect('/StudentUploadPhoto/')  # 学生第一次登陆修改密码后，引导去添加照片页面
            else:
                user.new_sign = False
                user.save()
            if user.identity.role_name == 'Student':
                return HttpResponseRedirect('/StudentIndex/')
            else:
                return HttpResponseRedirect('/TeacherIndex/')
    elif request.method == 'GET':
        # 异常请求，如果错误为500错误页面
        models.UserInformation.objects.get(account = request.session['user_account'],
                                           identity__role_name = request.GET.get('identity'))
        if request.GET.get('identity') == 'Teacher':
            user_identity = "老师"
        else:
            user_identity = "学生"
    return render(request, 'myApp/ReselectPassword.html',
                  {'why_select': why_select,
                   'user_name': request.session['user_name'],
                   'user_identity': user_identity})


# 选择添加学生班级信息
def select_add_student_info(request):
    select_fail = False
    user_name = request.session.get('user_name', default = None)
    college_list = list()
    if request.method == 'POST':
        # 确认信息后即可添加信息
        college = request.POST.get('college_name', default = None)
        major = request.POST.get('major_name', default = None)
        grade = request.POST.get('grade_name', default = None)
        select_add_mode = request.POST.get('SelectMode', default = None)
        if 'null_grade' == grade:
            if select_add_mode == 'single_add':  # 未选择班级却试图单独添加学生
                select_fail = True
            else:  # TODO :: 未选择班级，批量添加学生
                pass
        else:  # 指定某特定班级
            if select_add_mode == 'single_add':  # 为某个班级添加一个学生
                request.session['add_student_college'] = college
                request.session['add_student_major'] = major
                request.session['add_student_grade'] = grade
                return HttpResponseRedirect('/SingleAddStudent/')
            else:  # TODO :: 为某个班级批量添加学生
                pass
    elif request.method == 'GET':
        select_fail = False
        try:
            college_list = models.DetailGradeInformation.objects.all().values('college_id__college_name').distinct()
        except models.DetailGradeInformation.DoesNotExist:
            return render(request, 'myApp/SelectAddStudentInfo.html',
                          {"user_name": user_name,
                           "login_err": "No Data!"})
    return render(request, 'myApp/SelectAddStudentInfo.html',
                  {"user_name": user_name,
                   "college_list": college_list,
                   "select_fail": select_fail})


# 单独添加学生
def single_add_student(request):
    user_name = request.session.get('user_name', default = None)
    select_fail = False
    successful_add = False

    if request.method == 'POST':
        account = request.POST.get('form-account')
        name = request.POST.get('form-name')
        gender = request.POST.get('form-gender')
        if check_add_student_info(account, name):
            try:
                add_student(request, account, name, gender)
                select_fail = False
                successful_add = True
                add_grade = models.DetailGradeInformation.objects.get(
                    college_id__college_name = request.session.get("add_student_college"),
                    major_id__major_name = request.session.get("add_student_major"),
                    grade_id__grade_name = request.session.get("add_student_grade")
                )
                add_grade.student_num += 1
                add_grade.save()
            except Exception:
                select_fail = True
                successful_add = False
        else:
            select_fail = True
            successful_add = False

    return render(request, 'myApp/SingleAddStudent.html',
                  {'user_name': user_name,
                   'select_fail': select_fail,
                   'successful_add': successful_add})


# 检查所输入的添加学生的信息合法化
def check_add_student_info(account, name):
    # 检查名字是否都为中文
    for ch in name:
        if not ('\u4e00' <= ch <= '\u9fa5'):
            print("Add new Student False! Error input in Name")
            return False
    # 检查学号长度以及是否为纯数字
    if not account.isdigit():
        print("Add new Student False! Error input in Account Type")
        return False
    if len(account) < 6:
        print("Add new Student False! Error input in Account Length")
        return False
    # 检查该学生是否已经存在
    try:
        models.UserInformation.objects.get(account = account, identity__role_name = 'Student')
        print("Add new Student False! Student already exist(One)")
        return False
    except models.UserInformation.MultipleObjectsReturned:
        print("Add new Student False! Student already exist(MultipleObjectsReturned)")
        return False
    except models.UserInformation.DoesNotExist:
        return True


# 根据信息添加学生
def add_student(request, account, name, gender):
    college = request.session.get('add_student_college', default = None)
    major = request.session.get('add_student_major', default = None)
    grade = request.session.get('add_student_grade', default = None)
    if gender == 'boy':
        gender = False
    else:
        gender = True
    password = account[-6:]
    detail_grade = models.DetailGradeInformation.objects.get(college_id__college_name = college,
                                                             major_id__major_name = major,
                                                             grade_id__grade_name = grade)
    identity = models.IdentityInformation.objects.get(role_name = 'Student')

    if college != None and major != None and grade != None:
        new_student = models.UserInformation.add_student(account, password, name, gender)
        new_student.grade = detail_grade
        new_student.identity = identity
        new_student.save()


# 返回奇怪的favicon.ico图片
def return_favicon_ico(request):
    try:
        with open("favicon.ico", 'rb') as file:
            image_data = file.read()
        return HttpResponse(image_data, content_type = "image/png")
    except Exception as exception:
        print(exception)
        return HttpResponse(str(exception))


# TODO::todo界面
def todo(request):
    return render(request, 'myApp/todo.html', None)


# 404
def page_not_found(request):
    return render(None, '404.html')


# 500
def page_error(request):
    return render(None, '500.html')
