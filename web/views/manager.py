from django.shortcuts import render,redirect
from django.contrib.auth import login,logout,authenticate
from django.urls import  reverse
from django.http import QueryDict

def ac_login(request):
    if request.method == 'POST':
        next = None
        full_path = request.get_full_path()
        print(full_path)
        if 'next' in full_path:
            next = QueryDict(full_path.split('?')[1])
            print('===',next)
        username = request.POST.get("username")
        passwd = request.POST.get("passwd")
        user = authenticate(username=username,password=passwd)
        if user:
            login(request,user)
            if next:
                return redirect(next['next'])
            url = reverse('project_list')
            return redirect(url)

    return render(request,'login.html')

def ac_logout(request):
    logout(request)
    url = reverse('login')
    return redirect(url)