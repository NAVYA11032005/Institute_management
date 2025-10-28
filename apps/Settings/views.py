from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Setting
from .forms import SettingForm

@login_required
def setting_edit(request):
    # Assume only one Setting instance; create if not exists.
    setting, created = Setting.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = SettingForm(request.POST, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated.")
            return redirect('setting_edit')
    else:
        form = SettingForm(instance=setting)
    return render(request, 'settingsapp/setting_form.html', {'form': form})
