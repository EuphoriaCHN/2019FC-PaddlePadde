from django.db import models


# Create your models here.

# DIY Model Objects Manager
class ModelManager(models.Manager):
    def get_queryset(self):
        return super(ModelManager, self).get_queryset().filter(isDelete = False)


# 权限信息数据表
class IdentityInformation(models.Model):
    role_name = models.CharField(max_length = 20, primary_key = True)

    def __str__(self):
        return "%s" % self.role_name

    class Meta:
        db_table = "identity"


# 学院信息数据表
class CollegeInformation(models.Model):
    college_name = models.CharField(max_length = 40, unique = True)

    def __str__(self):
        return "%s" % self.college_name

    class Meta:
        db_table = "college"


# 专业信息数据表
class MajorInformation(models.Model):
    major_name = models.CharField(max_length = 40, unique = True)

    def __str__(self):
        return "%s" % self.major_name

    class Meta:
        db_table = "major"


# 班级信息数据表
class GradeInformation(models.Model):
    grade_name = models.CharField(max_length = 40, unique = True)

    def __str__(self):
        return "%s" % self.grade_name

    class Meta:
        db_table = "grade"


# 详细班级信息数据表
class DetailGradeInformation(models.Model):
    college_id = models.ForeignKey(CollegeInformation, to_field = 'college_name', on_delete = models.CASCADE)
    major_id = models.ForeignKey(MajorInformation, to_field = 'major_name', on_delete = models.CASCADE)
    grade_id = models.ForeignKey(GradeInformation, to_field = 'grade_name', on_delete = models.CASCADE)
    student_num = models.IntegerField(default = 0)

    def __str__(self):
        return "%s-%s-%s" % (self.college_id.college_name, self.major_id.major_name, self.grade_id.grade_name)

    class Meta:
        db_table = "user_grade"


# 签到信息数据表
class SignInformation(models.Model):
    sign_time = models.DateTimeField(auto_now_add = True)
    initiator = models.IntegerField()
    target = models.ForeignKey(DetailGradeInformation, on_delete = models.CASCADE)
    reached = models.IntegerField()
    actual = models.IntegerField()

    def __str__(self):
        return "%s" % str(self.sign_time)

    class Meta:
        db_table = "sign"

    @classmethod
    def make_new_sign(cls, initiator, target, reached):
        sign = cls(initiator = initiator, target = target, reached = reached, actual = 0)
        return sign


# 用户信息数据表
class UserInformation(models.Model):
    account = models.CharField(max_length = 20, unique = True)
    password = models.CharField(max_length = 20)
    name = models.CharField(max_length = 20)
    gender = models.BooleanField()
    grade = models.ForeignKey(DetailGradeInformation, on_delete = models.CASCADE, null = True, blank = True)
    identity = models.ForeignKey(IdentityInformation, on_delete = models.CASCADE)
    first_create_time = models.DateTimeField(auto_now_add = True)
    last_modify_time = models.DateTimeField(auto_now = True)
    new_sign = models.BooleanField(default = True)
    isDelete = models.BooleanField(default = False)

    objects = ModelManager()  # DIY Model Objects Manager

    def __str__(self):
        return "%s" % self.name

    class Meta:
        db_table = "user"

    @classmethod
    def add_student(cls, account, password, name, gender):
        new_student = cls(account = account, password = password, name = name, gender = gender)
        return new_student