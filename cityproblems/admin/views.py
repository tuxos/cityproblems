#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.contrib import auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.forms.models import modelform_factory
from django.contrib.auth import get_user_model

from annoying.decorators import render_to

from cityproblems.utils import *
from cityproblems.accounts.forms import RegisterUserForm
from .models import SiteParameters
from .utils import *

User = get_user_model()


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
@render_to("admin_form.html")
def add_admin(request):
    if request.method == 'POST':
        form = RegisterUserForm(request.POST, is_staff=True)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(nextPage(request.GET, reverse("admin_adminsList")))
    else:
        form = RegisterUserForm()
    return {"form": form, "buttonTxt": _("Add"), "title": _("Add new admin")}


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
@render_to("admin_form.html")
def add_parameter(request):
    if not request.user.is_superuser:
        messages.error(request, _("Permission denied"))
        return HttpResponseRedirect(nextPage(request.GET, reverse("admin_parametersList")))
    form = modelform_factory(SiteParameters)(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(nextPage(request.GET, reverse("admin_parametersList")))
    return {"form": form, "buttonTxt": _("Add"), "title": _("Add new parameter")}


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
@render_to("admin_form.html")
def edit_parameter(request, id):
    if not request.user.is_superuser:
        messages.error(request, _("Permission denied"))
        return HttpResponseRedirect(nextPage(request.GET, reverse("admin_parametersList")))
    object = get_object_or_404(SiteParameters, id=id)
    form = modelform_factory(SiteParameters)(request.POST or None, instance=object)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(nextPage(request.GET, reverse("admin_parametersList")))
    return {"form": form, "buttonTxt": _("Save"), "title": _("Parameter edit")}


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
@render_to("admin_admins_list.html")
def admins_list(request):
    adminsList = User.objects.filter(is_staff=True, is_superuser=False)
    return {"title": _("Site admins"), "currentPage": "admin_adminsList",
            "adminsList": adminsList}


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
@render_to("admin_parameters_list.html")
def parameters_list(request):
    paramsList = SiteParameters.objects.all()
    return {"title": _("Site parameters"), "currentPage": "admin_parametersList",
            "paramsList": paramsList}


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
def process_lock(request):
    if request.method != 'POST':
        return HttpResponse("Use post")
    try:
        user = User.objects.get(id=request.POST.get('id', 0))
    except ObjectDoesNotExist:
        messages.error(request, _("No such user"))
        return HttpResponseRedirect(reverse("admin_adminsList"))
    if user.id == request.user.id:
        messages.error(request, _("You can`t lock yourself"))
        return HttpResponseRedirect(reverse("admin_adminsList"))
    user.is_active = not user.is_active
    user.save()
    if not user.is_active:
        [s.delete() for s in Session.objects.all() if s.get_decoded()
         .get('_auth_user_id') == user.id]
    return HttpResponseRedirect(reverse("admin_adminsList"))


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
def process_admin_remove(request):
    if request.method != 'POST':
        return HttpResponse("Use post")
    try:
        user = User.objects.get(id=request.POST.get('id', 0))
    except ObjectDoesNotExist:
        messages.error(request, _("No such user"))
        return HttpResponseRedirect(reverse("admin_adminsList"))
    if user.id == request.user.id:
        messages.error(request, _("You can`t remove yourself"))
        return HttpResponseRedirect(reverse("admin_adminsList"))
    user.delete()
    return HttpResponseRedirect(reverse("admin_adminsList"))


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
def process_parameter_remove(request):
    if not request.user.is_superuser:
        messages.error(request, _("Permission denied"))
        return HttpResponseRedirect(nextPage(request.GET, reverse("admin_parametersList")))
    if request.method != 'POST':
        return HttpResponse("Use post")
    try:
        param = SiteParameters.objects.get(id=request.POST.get('id', 0))
    except ObjectDoesNotExist:
        messages.error(request, _("No such parameter"))
        return HttpResponseRedirect(reverse("admin_parametersList"))
    param.delete()
    return HttpResponseRedirect(reverse("admin_parametersList"))


@login_required
@user_passes_test(is_admin, login_url=reverse_lazy("no_permissions"))
@render_to('admin_form.html')
def change_passwd(request, id):
    user = get_object_or_404(User, id=id, is_superuser=False)
    if request.method == 'POST':
        form = AdminPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("admin_adminsList"))
    else:
        form = AdminPasswordChangeForm(user)
    return {'form': form, "buttonTxt": _("Change"),
            "title": _("Change password for")+u" {}".format(user.username)}