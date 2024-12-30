from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"您已登录为 {username}")
                return redirect('page:home')
            else:
                messages.error(request, "用户名或密码无效")
        else:
            messages.error(request, "用户名或密码无效")
    form = AuthenticationForm()
    return render(request, 'muggle/sign-in.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "注册成功！")
            return redirect('page:home')
        messages.error(request, "注册失败，请检查输入信息")
    form = UserCreationForm()
    return render(request, 'muggle/register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'muggle/profile.html', {'user': request.user})

def logout_view(request):
    logout(request)
    messages.info(request, "您已成功退出登录")
    return redirect('page:home')
