from django.shortcuts import render
from django.http import HttpResponse
import datetime
# Create your views here.
tasks=[]
def index(request):
    if request.method=="GET":
        return render(request, "hello/index.html",{
            "q":tasks
        })
    if request.method=="POST":
        x=request.form.get("task")
        tasks.append("task")
        return render(request, "hello/index.html",{
            "q":tasks
        }) 
def add(request):
    return render(request, "hello/add.html")
    if request.method=="POST":
        print()
        print()
        print("ERRORR ERRORRRR")
        print()
