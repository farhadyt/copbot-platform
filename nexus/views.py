from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def portal_view(request):
    """Neural Access Portal - Login"""
    if request.user.is_authenticated:
        return redirect('horizon:command_center')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Neural sync established. Welcome, {username}.")
                return redirect('horizon:command_center')
    else:
        form = AuthenticationForm()
    
    return render(request, 'nexus/portal.html', {'form': form})