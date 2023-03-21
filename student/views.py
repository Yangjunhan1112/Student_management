from django.shortcuts import render, redirect
from django.db import transaction

from .models import StudentInfo
from account.models import Account
from manager.models import Major, Clazz, ClazzStudents, SchoolTimeTable, StudentCurriculumScore

from django.contrib.auth.hashers import make_password, check_password

from utils.check_login import check_login
from utils.rendom_char import get_random_str


def get_all_majors_clazzs():
    all_major = Major.objects.all()
    all_clazz = Clazz.objects.all()
    return {'clazzs': all_clazz, 'majors': all_major}


@check_login
@transaction.atomic
def student_info(request):
    user_id = request.session.get('user_id')
    req_typ = request.GET.get('typ')

    if request.method == 'GET':
        if not req_typ:
            if not StudentInfo.objects.filter(user_id=user_id).exists():
                return render(request, 'student_info.html',
                              context={'student_id': '未设置', 'name': '未设置', 'sex': '未设置', 'birth_day': '未设置',
                                       'native_place': '未设置', 'major': '未设置', 'clazz': '未设置', 'title': '个人信息'})
            info = StudentInfo.objects.get(user_id=user_id)
            return render(request, 'student_info.html', context=info.__dict__)
        elif req_typ.upper() == 'update'.upper():
            context = {'typ': 'update', 'title': '修改个人信息'}
            if StudentInfo.objects.filter(user_id=user_id).exists():
                context['sid'] = StudentInfo.objects.get(user_id=user_id).id
            context.update(get_all_majors_clazzs())
            return render(request, 'student_info.html', context=context)
        elif req_typ.upper() == 'change_password'.upper():
            return render(request, 'student_info.html', context={'typ': 'change_password', 'title': '修改密码'})

    if request.method == 'POST':
        params = request.POST.dict()
        if params.get('req_typ') == 'info':
            if not params.get('name') or not params.get('sex') or not params.get('birth_day'):
                context = {'typ': 'update', 'message': '提交的数据不完整', 'title': '修改个人信息'}
                context.update(get_all_majors_clazzs())

                return render(request, 'student_info.html', context=context)

            major, clazz = params['clazz'].split('-')
            exists = False
            if StudentInfo.objects.filter(user_id=Account.objects.get(id=user_id)).exists():
                student = StudentInfo.objects.get(user_id=Account.objects.get(id=user_id))
                student.name = params['name']
                student.sex = params['sex']
                student.birth_day = params['birth_day']
                student.native_place = params['native_place']
                student.major = major
                student.clazz = clazz
                exists = True
            else:
                student = StudentInfo(name=params['name'], sex=params['sex'], birth_day=params['birth_day'],
                                      native_place=params['native_place'], major=major, clazz=clazz,
                                      student_id=params.get('student_id', get_random_str(14, True)),
                                      user_id=Account.objects.get(id=user_id)
                                      )
            student.save()
            _clazz = Clazz.objects.get(name=clazz, major_id__name=major)
            if exists:
                cs = ClazzStudents.objects.get(student_id=student.id)
                cs.clazz_id = _clazz
                cs.save()
            else:
                ClazzStudents(student_id=student, clazz_id=_clazz).save()
            return redirect('/student_info/')
        elif params.get('req_typ') == 'password':
            password = params.get('password')
            password_again = params.get('password-again')
            if len(str(password)) < 8:
                return render(request, 'student_info.html',
                              context={'typ': 'change_password', 'message': '密码长度不足8位' , 'title': '修改密码'})
            if password_again != password:
                return render(request, 'student_info.html',
                              context={'typ': 'change_password', 'message': '两次输入的密码不一致', 'title': '修改密码'})
            account = Account.objects.get(id=user_id)
            account.password = make_password(password)
            account.save()
            return render(request, 'student_info.html', context={'typ': 'change_password', 'message': '修改密码完成', 'title': '修改密码'})


@check_login
def student_time_table(request):
    user_id = request.session.get('user_id')
    student = StudentInfo.objects.get(user_id=user_id)
    clazz = ClazzStudents.objects.get(student_id=student.id)

    def get_stt():
        tmp = {
            '1': {'1': None, '2': None, '3': None, '4': None, '5': None},  # key是第几节课，后面的字典是周几
            '2': {'1': None, '2': None, '3': None, '4': None, '5': None},
            '3': {'1': None, '2': None, '3': None, '4': None, '5': None},
            '4': {'1': None, '2': None, '3': None, '4': None, '5': None},
        }
        for stt in SchoolTimeTable.objects.filter(clazz_id=clazz.clazz_id.id).order_by('clazz_week'):
            tmp[str(stt.clazz_time)][str(stt.clazz_week)] = stt
        return tmp

    return render(request, 'student_info.html', context={'time_table': get_stt(), 'typ': 'time_table', 'title': '课表'})


@check_login
def get_student_score(request):
    user_id = request.session.get('user_id')
    student = StudentInfo.objects.get(user_id=user_id)
    clazz = ClazzStudents.objects.get(student_id=student.id)

    tmp = []

    result = []
    for stt in SchoolTimeTable.objects.filter(clazz_id=clazz.clazz_id.id).order_by('clazz_week'):
        if stt.curriculum.id not in tmp:
            tmp.append(stt.curriculum.id)
            scs = StudentCurriculumScore.objects.filter(student_id=student.id, curriculum_id=stt.curriculum.id)
            if scs:
                result.append(scs[0])
    return render(request, 'student_info.html', context={'scores': result, 'typ': 'score', 'title': '成绩查询'})
