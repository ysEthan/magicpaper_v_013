from django.shortcuts import render

def home(request):
    """主页视图"""
    context = {
        'title': '首页',
    }
    return render(request, 'page/home.html', context)
