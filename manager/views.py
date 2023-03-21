import traceback

from datetime import datetime

from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse, HttpResponse

from utils.check_login import check_login
from utils.rendom_char import get_random_str

from .models import ClazzStudents, Major, Clazz, Curriculum, SchoolTimeTable
from teacher.models import TeacherInfo
from account.models import Account
from student.models import StudentInfo


@check_login
def manager_index(request):
    all_students = ClazzStudents.objects.all()  # 已更新过班级专业的学生才能看见
    return render(request, 'admin_info.html', context={'students': all_students, 'title': '所有学生信息'})


@check_login
@transaction.atomic
def add_student_info(request):
    all_clazzs = Clazz.objects.all()
    if request.method == "GET":
        return render(request, 'add_student.html', context={'clazzs': all_clazzs, 'title': '新增学生'})
    if request.method == 'POST':
        params = request.POST.dict()
        for p in params.values():
            if not p:
                return render(request, 'add_student.html',
                              context={'messages': ['提交的数据不全'], 'clazzs': all_clazzs, 'title': '新增学生'})

        if Account.objects.filter(username=params['username']).exists():
            return render(request, 'add_student.html',
                          context={'messages': ['账号已存在，请更换账号提交'], 'clazzs': all_clazzs,
                                   'title': '新增学生'})

        account = Account(username=params['username'], password=make_password(params['password']), customer_type=0)
        account.save()
        _clazz = params['clazz_info'].split('-')
        _clazz_obj = Clazz.objects.get(id=_clazz[0])
        student = StudentInfo(name=params['name'], sex=params['sex'], birth_day=params['birth_day'],
                              native_place=params['native_place'], clazz=_clazz_obj.name,
                              major=_clazz_obj.major_id.name,
                              student_id=get_random_str(14, True), user_id=account)
        student.save()
        ClazzStudents(student_id=student, clazz_id=_clazz_obj).save()
        return render(request, 'add_student.html',
                      context={'messages': ['成功创建学生账号'], 'clazzs': all_clazzs, 'title': '新增学生'})


@check_login
def teachers_info(request):
    return render(request, 'admin_teacher.html',
                  context={'teachers': TeacherInfo.objects.all(), 'title': '所有老师信息'})


@check_login
@transaction.atomic
def add_teacher_info(request):
    if request.method == "GET":
        return render(request, 'add_teacher.html')
    if request.method == 'POST':
        params = request.POST.dict()
        for p in params.values():
            if not p:
                return render(request, 'add_teacher.html',
                              context={'messages': ['提交的数据不全'], 'title': '新增老师'})
        if Account.objects.filter(username=params['username']).exists():
            return render(request, 'add_teacher.html',
                          context={'messages': ['账号已存在，请更换注册账号'], 'title': '新增老师'})
        account = Account(username=params['username'], password=make_password(params['password']), customer_type=1)
        account.save()
        TeacherInfo(name=params['name'], sex=params['sex'], birth_day=params['birth_day'],
                    teacher_id=get_random_str(14, True), user_id=account).save()
        return render(request, 'add_teacher.html', context={'messages': ['成功创建老师账号'], 'title': '新增老师'})


@check_login
def major(request):
    return render(request, 'major.html', context={'majors': Major.objects.all(), 'title': '所有专业'})


@check_login
def clazz(request):
    return render(request, 'clazz.html', context={'clazzs': Clazz.objects.all(), 'title': '所有班级'})


@check_login
def add_major(request):
    if request.method == 'GET':
        return render(request, 'add_major.html', context={'title': '新增专业'})
    else:
        params = request.POST.dict()
        for p in params.values():
            if not p:
                return render(request, 'add_major.html', context={'messages': ['提交的数据不全'], 'title': '新增专业'})
        try:
            Major(major_code=params['major_code'], name=params['name']).save()
            return render(request, 'add_major.html', context={'messages': ['新建专业成功'], 'title': '新增专业'})
        except Exception as e:
            return render(request, 'add_major.html', context={'messages': ['专业已存在，创建失败'], 'title': '新增专业'})


@check_login
def add_clazz(request):
    all_majors = Major.objects.all()
    if request.method == 'GET':

        return render(request, 'add_clazz.html', context={'majors': all_majors, 'title': '新增班级'})
    else:
        params = request.POST.dict()
        for p in params.values():
            if not p:
                return render(request, 'add_clazz.html',
                              context={'messages': ['提交的数据不全'], 'majors': all_majors, 'title': '新增班级'})
        try:
            _major = params['major'].split('-')
            _major_obj = Major.objects.get(major_code=_major[0], name=_major[1])
            Clazz(name=params['name'], major_id=_major_obj).save()
            return render(request, 'add_clazz.html',
                          context={'messages': ['新建班级成功'], 'majors': all_majors, 'title': '新增班级'})
        except Exception as e:
            print(traceback.format_exc())
            return render(request, 'add_clazz.html',
                          context={'messages': ['创建失败，请联系管理员'], 'majors': all_majors, 'title': '新增班级'})


@check_login
def curriculum(request):
    return render(request, 'curriculum.html',
                  context={'curriculums': Curriculum.objects.all(), 'title': '所有课程信息'})


@check_login
def add_curriculum(request):
    all_teachers = TeacherInfo.objects.all()
    if request.method == 'GET':
        return render(request, 'add_curriculum.html', context={'teachers': all_teachers, 'title': '新增课程'})
    elif request.method == 'POST':
        params = request.POST.dict()
        for p in params.values():
            if not p:
                return render(request, 'add_curriculum.html',
                              context={'messages': ['提交的数据不全'], 'teachers': all_teachers, 'title': '新增课程'})
        teacher = TeacherInfo.objects.get(id=params['teacher_info'].split('-')[0])
        Curriculum(name=params['name'], teacher_id=teacher).save()
        return render(request, 'add_curriculum.html',
                      context={'messages': ['成功创建课程成功'], 'teachers': all_teachers, 'title': '新增课程'})


@check_login
@transaction.atomic
def change_clazz_time_table(request):
    all_curr = Curriculum.objects.all()  # 所有课程
    context = {'curriculums': all_curr, 'title': '修改班级课表'}

    if request.method == 'GET':
        clazz_id = request.GET.get('clazz_id')
    elif request.method == 'POST':
        clazz_id = request.POST.dict().get('clazz_id')
    else:
        return redirect('manager_index')

    def get_stt():
        tmp = {
            '1': {'1': None, '2': None, '3': None, '4': None, '5': None},  # key是第几节课，后面的字典是周几
            '2': {'1': None, '2': None, '3': None, '4': None, '5': None},
            '3': {'1': None, '2': None, '3': None, '4': None, '5': None},
            '4': {'1': None, '2': None, '3': None, '4': None, '5': None},
        }
        for stt in SchoolTimeTable.objects.filter(clazz_id=clazz_id).order_by('clazz_week'):
            tmp[str(stt.clazz_time)][str(stt.clazz_week)] = stt
        return tmp

    context['time_table'] = get_stt()
    context['clazz_id'] = clazz_id

    if request.method == 'GET':
        return render(request, 'change_clazz_time_table.html', context=context)
    elif request.method == 'POST':
        data = request.POST.dict()
        for k, v in data.items():
            if not v:
                context['messages'] = ['提交的数据不完整']
                return render(request, 'change_clazz_time_table.html',
                              context=context)
        week = data.get('week')
        table_time = data.get('table_time')
        _curriculum = data.get('curriculum')

        _curriculum = Curriculum.objects.get(id=_curriculum)
        if SchoolTimeTable.objects.filter(clazz_id=clazz_id, clazz_week=week, clazz_time=table_time).exists():
            SchoolTimeTable.objects.get(clazz_id=clazz_id, clazz_week=week, clazz_time=table_time).delete()

        print(clazz_id)
        SchoolTimeTable(clazz_id=Clazz.objects.get(id=clazz_id), clazz_time=table_time, clazz_week=week,
                        curriculum=_curriculum).save()
        context['messages'] = ['新建或者修改成功']
        context['time_table'] = get_stt()

        return render(request, 'change_clazz_time_table.html',
                      context=context)


@check_login
@transaction.atomic
def change_student_info(request):
    all_clazz = Clazz.objects.all()
    context = {'clazzs': all_clazz}

    if request.method == 'GET':
        student_id = request.GET.get('student_id')
    elif request.method == 'POST':
        student_id = request.POST.dict().get('student_id')
    else:
        return redirect('manager_index')

    print('student_id', student_id)
    current_clazz = ClazzStudents.objects.get(student_id=student_id)
    context['current_clazz_id'] = current_clazz.clazz_id
    context['sid'] = student_id
    context['student'] = StudentInfo.objects.get(id=student_id)

    if request.method == 'GET':
        return render(request, 'change_student_info.html', context=context)
    else:
        data = request.POST.dict()
        student_info = StudentInfo.objects.get(id=student_id)
        student_info.name = data['name']
        student_info.sex = data['sex']
        student_info.birth_day = data['birth_day']
        student_info.native_place = data['native_place']
        new_clazz = Clazz.objects.get(id=data['clazz'])
        student_info.major = new_clazz.major_id.name
        student_info.clazz = new_clazz.name
        student_info.update_time = datetime.now()
        student_info.save()
        cs = ClazzStudents.objects.get(student_id=student_id)
        cs.clazz_id = new_clazz
        cs.update_time = datetime.now()
        cs.save()
        context['current_clazz_id'] = new_clazz.id
        context['messages'] = ['修改成功']
        context['student'] = StudentInfo.objects.get(id=student_id)
        return render(request, 'change_student_info.html', context=context)


@check_login
@transaction.atomic
def change_teacher_info(request):
    if request.method == 'GET':
        teacher_id = request.GET.get('teacher_id')
    elif request.method == 'POST':
        teacher_id = request.POST.dict().get('teacher_id')
    else:
        return redirect('manager_index')

    teacher = TeacherInfo.objects.get(id=teacher_id)
    context = {'teacher': teacher}

    if request.method == "GET":
        return render(request, 'change_teacher_info.html', context)
    else:
        data = request.POST.dict()
        teacher.name = data['name']
        teacher.sex = data['sex']
        teacher.birth_day = data['birth_day']
        teacher.update_time = datetime.now()
        teacher.save()
        context = {'teacher': teacher, 'messages': ['修改成功']}
        return render(request, 'change_teacher_info.html', context)


@check_login
@transaction.atomic
def delete_student(request):
    sid = request.GET.get('id')
    if not sid:
        return '请求参数错误'
    if not StudentInfo.objects.filter(id=sid).exists():
        return '参数错误'
    student = StudentInfo.objects.get(id=sid)
    student.delete()
    if Account.objects.filter(id=student.user_id.id).exists():
        Account.objects.filter(id=student.user_id.id).delete()
    return JsonResponse({'success': True, 'message': '删除成功'})


@check_login
@transaction.atomic
def delete_teacher(request):
    tid = request.GET.get('id')
    if not tid:
        return '请求参数错误'
    if not TeacherInfo.objects.filter(id=tid).exists():
        return '参数错误'
    teacher = TeacherInfo.objects.get(id=tid)
    teacher.delete()
    if Account.objects.filter(id=teacher.user_id.id).exists():
        Account.objects.filter(id=teacher.user_id.id).delete()
    return JsonResponse({'success': True, 'message': '删除成功'})
