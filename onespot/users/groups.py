from django.contrib.auth.models import Group 

def teacher():
    return Group.objects.get(name="Teacher")

def gotlearning_admin():
    return Group.objects.get(name="gotLearning Admin")

def system_admin():
    return Group.objects.get(name="System Admin")

def school_admin():
    return Group.objects.get(name="School Admin")

def student():
    return Group.objects.get(name="Student")

def individual_teacher():
    return Group.objects.get(name="Individual Teacher")

def educational_specialist():
    return Group.objects.get(name="Educational Specialist")
