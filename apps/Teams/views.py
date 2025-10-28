from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Team, INDIAN_STATES
from .forms import TeamForm


@login_required
def team_list(request):
    # List only active (non-deleted) team members
    teams = Team.objects.filter(is_deleted=False).order_by('id')
    return render(request, 'team/team_list.html', {
        'teams': teams,
        'sidebar_active': 'team',
    })


@login_required
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member added successfully.")
            return redirect('team_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TeamForm()

    return render(request, 'team/team_form.html', {
        'form': form,
        'INDIAN_STATES': INDIAN_STATES,
        'sidebar_active': 'team',
    })


@login_required
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk, is_deleted=False)
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member updated successfully.")
            return redirect('team_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TeamForm(instance=team)

    return render(request, 'team/team_form.html', {
        'form': form,
        'team': team,
        'INDIAN_STATES': INDIAN_STATES,
        'sidebar_active': 'team',
    })


@login_required
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk, is_deleted=False)
    if request.method == 'POST':
        # Soft delete - mark as deleted instead of actual deletion
        team.is_deleted = True
        team.deleted_at = timezone.now()
        team.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, "Team member moved to trash.")
        return redirect('team_list')

    return render(request, 'team/team_confirm_delete.html', {
        'team': team,
        'sidebar_active': 'team',
    })


@login_required
def team_member_detail(request, pk):
    team_member = get_object_or_404(Team, pk=pk, is_deleted=False)
    payments = team_member.expenses.all().order_by('-date')
    return render(request, 'team/team_member_detail.html', {
        'team_member': team_member,
        'payments': payments,
        'sidebar_active': 'team',
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Team

@login_required
def team_restore(request, pk):
    team = get_object_or_404(Team, pk=pk, is_deleted=True)
    if request.method == "POST":
        team.is_deleted = False
        team.deleted_at = None
        team.save(update_fields=['is_deleted', 'deleted_at'])
        messages.success(request, "Team member restored successfully.")
        return redirect('team_list')  # or wherever you want to redirect after restore
    return render(request, "team/team_restore_confirm.html", {"team": team})
