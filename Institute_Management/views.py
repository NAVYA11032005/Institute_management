from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('courses')  # Already logged in, go to courses

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome, {user.get_username()}!')
                return redirect('courses')
            else:
                messages.error(request, 'Your account is inactive. Please contact admin.')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'courses/login.html')  # Always render login page if not authenticated or login failed

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')
