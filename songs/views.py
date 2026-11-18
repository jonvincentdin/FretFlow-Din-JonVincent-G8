from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import SongForm
from .models import Song


def member_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@member_required
@require_http_methods(['GET'])
def song_list(request):
    query = request.GET.get('q', '').strip()[:200]
    songs = Song.objects.filter(owner=request.user).defer('content')
    if query:
        songs = songs.filter(Q(title__icontains=query) | Q(artist__icontains=query))
    page = Paginator(songs, 20).get_page(request.GET.get('page'))
    return render(request, 'songs/song_list.html', {'page_obj': page, 'query': query})


@member_required
@require_http_methods(['GET', 'POST'])
def song_create(request):
    form = SongForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        song = form.save(commit=False)
        song.owner = request.user
        song.save()
        messages.success(request, 'Your song has been saved.')
        return redirect(song)
    return render(request, 'songs/song_form.html', {'form': form})


@member_required
@require_http_methods(['GET'])
def song_detail(request, pk):
    song = get_object_or_404(Song, owner=request.user, pk=pk)
    return render(request, 'songs/song_detail.html', {'song': song})


@member_required
@require_http_methods(['GET', 'POST'])
def song_edit(request, pk):
    song = get_object_or_404(Song, owner=request.user, pk=pk)
    form = SongForm(request.POST if request.method == 'POST' else None, instance=song)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your changes have been saved.')
        return redirect(song)
    return render(request, 'songs/song_form.html', {'form': form, 'song': song})


@member_required
@require_http_methods(['GET', 'POST'])
def song_delete(request, pk):
    song = get_object_or_404(Song, owner=request.user, pk=pk)
    if request.method == 'POST':
        song.delete()
        messages.success(request, 'Your song has been deleted.')
        return redirect('songs:list')
    return render(request, 'songs/song_confirm_delete.html', {'song': song})
