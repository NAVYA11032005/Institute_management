from django.shortcuts import render, redirect, get_object_or_404
from .models import Team, INDIAN_STATES
from .forms import TeamForm

def team_list(request):
    teams = Team.objects.all()
    return render(request, 'team/team_list.html', {
        'teams': teams,
        'sidebar_active': 'team',
    })

def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm()
    return render(request, 'team/team_form.html', {
        'form': form,
        'INDIAN_STATES': INDIAN_STATES,
        'sidebar_active': 'team',
    })

def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm(instance=team)
    return render(request, 'team/team_form.html', {
        'form': form,
        'team': team,
        'INDIAN_STATES': INDIAN_STATES,
        'sidebar_active': 'team',
    })

def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        team.delete()
        return redirect('team_list')
    return render(request, 'team/team_confirm_delete.html', {
        'team': team,
        'sidebar_active': 'team',
    })

def team_member_detail(request, pk):
    team_member = get_object_or_404(Team, pk=pk)
    payments = team_member.expenses.all().order_by('-date')
    return render(request, 'team/team_member_detail.html', {
        'team_member': team_member,
        'payments': payments,
        'sidebar_active': 'team',
    })
