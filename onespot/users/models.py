import uuid 
from django.contrib.auth.models import (
    BaseUserManager, AbstractUser
)
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.query import QuerySet 
from users.groups import (
    educational_specialist,
    teacher,
    individual_teacher,
    system_admin,
    gotlearning_admin,
    school_admin,
    student,
    educational_specialist
)

class UserManager(BaseUserManager):
    def create(self, email, request, first_name, last_name, display_name=None, password=None):
        """
        Creates and saves a User by default adds the user to the Student group unless specified.

        Args:
            email: email address of user
            first_name: first name of user
            last_name: last name of user
            request: request context
            display_name: name to be displayed if not first_name
            password: user password
        """
        if request.user.has_module_perms(self.model):
            if display_name is None:
                display_name = ""
            email = self.normalize_email(email)
            new_user = super().create(
                email=email,
                username=email,
                first_name = first_name,
                last_name = last_name,
                display_name = display_name
            )
            new_user.set_password(password)
            new_user.save(using=self._db)
            return new_user 
        else:
            raise PermissionError("User is not allowed to create users.")

    def create_superuser(self, email, request, first_name, last_name, display_name=None, password=None):
        """
        Creates a user in the gotLearning admin group.

        Args:
            email: email address of user
            first_name: first name of the user
            last_name: last name of the user
            request: request object for permissions check
            display_name: name to be displayed if not first_name
            password: user password
        """
        if request.user.has_perm("user.can_superuser"):
            new_user = self.create_user(
                email,
                request,
                first_name,
                last_name,
                display_name=display_name,
                password=password,
                is_admin=True,
                is_staff=True,
                is_superuser=True
            )
            
            # Add User to the appropriate group
            new_user.groups.add(gotlearning_admin)
            return new_user 
        else:
            raise PermissionError("You cannot create an administrator.")

    def assign_group(self, request, type, obj):
        """
        Assigns User to a Group.
        
        Args:
            user: user to add to group
            request: request object for permissions check
            type: group type
        """
        if ( type == "gotLearning Administrator" 
            and request.user.has_perm("user.can_create_any_account") 
            ):
            obj.groups.add(gotlearning_admin)
        elif (type == "Teacher" 
            and request.user.has_perm("user.can_create_teacher_account")
            ):
            obj.groups.add(teacher)
        elif (type == "Individual Teacher" 
            and request.user.has_perm("user.can_create_teacher_account")
            ):
            obj.groups.add(individual_teacher)
        elif (type == "Educational Specialist" and
            request.user.has_perm("user.can_create_educational_specialist")
            ):
            obj.groups.add(educational_specialist)
        elif (type == "School Administrator" and
            request.user.has_perm("user.can_create_school_admin_account")
            ):
            obj.groups.add(school_admin)
        elif (type == "System Administrator" and 
            request.user.has_perm("user.can_create_system_admin_account")
            ):
            obj.groups.add(system_admin)
        elif (type == "Student" and 
            request.user.has_perm("user.can_create_student_account")
            ):
            obj.groups.add(student)
        else:
            raise PermissionError("You cannot add user to that group.")

    def toggle_activation(self, request, obj):
        """
        Toggle User activation. 

        Args:
            user: user to toggle.
            request: request for permission checks
        """
        if request.user.has_perm("user.toggle_active"):
            obj.is_active = not obj.is_active
        else:
            raise PermissionError("You cannot toggle user activation.")

    def list(self, request) -> QuerySet:
        """
        Retrieve a list of users filtered only by permissions.

        Args: 
            request: request for permission check
        """
        if request.user.has_perm("user.can_retrieve_all_users"):
            return self.get_queryset().all()
        elif request.user.has_perm("user.can_retrieve_users_in_school"):
            #TODO: implment this
            pass 
        else:
            raise PermissionError("You cannot retrieve users that way.")

    def retrieve(self, request, id) -> QuerySet:
        """
        Retrieve a single user, if permitted.

        Args:
            request: request for permission check
            id: uuid of the user to retrieve
        """

        if request.user.has_perm("user.can_retrieve_all_users"):
            return self.filter(pk=id)
        if request.user.has_perm("user.can_retrieve_users_in_school"):
            #TODO: implement this
            pass
        else:
            raise PermissionError("You do not have permission to access this user.")

    def update(self, request, id, **kwargs):
        """
        Update user values. Overrides default update method

        Args:
            request: request for permission checks
            id: id of object instance to retrieve
            kwargs: keyword arguments for model fields.
        """ 
        obj = self.filter(id=id)
        if obj is None:
            raise ObjectDoesNotExist
        
        if (
            (obj.id == request.user.id and 
            request.user.has_perm("user.can_update_self")) or
            request.user.has_perm("user.can_update_other")):
            # use queryset update to avoid race condition
            obj.update(**kwargs)
        else:
            raise PermissionError("You do not have permissiont to change that user.")

    def delete(self, request, obj):
        """
        Delete a user object. 

        Args:
            request: request for permission checks
            obj: the instance to be deleted
        """
        if (request.user.has_perm("user.can_delete_user") and 
            obj.id != request.user.id):
            obj.is_deleted=True
        else:
            raise PermissionError("You do not have permission to delete this user.")


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(verbose_name="Email Address", unique=True)
    is_deleted = models.BooleanField(default=False)
    display_name = models.CharField(max_length=255, blank=True)

    class Meta:
        permissions = [
            ("can_create_student_account", "Create a Student Account"),
            ("can_create_teacher_account", "Create a Teacher Account"),
            ("can_create_educational_specialist", "Create an Educational Specialist"),
            ("can_create_school_admin_account", "Create School Admin Account"),
            ("can_create_sys_admin_account", "Create System Admin Account"),
            ("can_create_any_account", "Create any user"),
            ("can_create_superuser", "Create superuser."),
            ("can_update_self", "Update own information"),
            ("can_update_other", "Update any user info"),
            ("can_delete_user", "Can delete user"),
            ("can_toggle_activation", "Can Toggle Activation"),
            ("can_retrieve_users_in_class", "Can retrieve classmates"),
            ("can_retrieve_users_in_school", "Can retireve all users in school"),
            ("can_retrieve_all_users", "Can retrieve all users"),
        ]