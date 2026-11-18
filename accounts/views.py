from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, RegistrationForm


class SignInView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    form = RegistrationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error(None, 'That username or email was just taken. Please choose another.')
        else:
            login(request, user)
            messages.success(request, 'Your account is ready. Welcome to FretFlow!')
            return redirect('accounts:dashboard')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    destination = 'accounts:admin_dashboard' if request.user.is_staff else 'accounts:member_dashboard'
    return redirect(destination)


@login_required
def member_dashboard(request):
    if request.user.is_staff:
        raise PermissionDenied
    songs = request.user.songs.defer('content')
    return render(request, 'accounts/member_dashboard.html', {
        'song_count': songs.count(), 'recent_songs': songs[:5],
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied
    return render(request, 'accounts/admin_dashboard.html')


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    form = ProfileForm(request.POST if request.method == 'POST' else None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error('email', 'That email was just taken. Please choose another.')
        else:
            messages.success(request, 'Your profile and practice preferences have been saved.')
            return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})
