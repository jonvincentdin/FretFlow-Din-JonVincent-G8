from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Song

User = get_user_model()


class SongTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create_user('player', 'player@example.com', 'Practice!75319')
        cls.other = User.objects.create_user('teacher', 'teacher@example.com', 'Practice!75319')
        cls.admin = User.objects.create_user('owner', 'admin@example.com', 'Practice!75319', is_staff=True)
        cls.song = Song.objects.create(owner=cls.member, title='Morning practice', artist='Original exercise', content='[C] Play a little [G] longer.\n')
        cls.private = Song.objects.create(owner=cls.other, title='Private lesson', artist='Another teacher', content='Private notes')

    def setUp(self):
        self.client.force_login(self.member)

    def data(self, **changes):
        return {'title': 'Evening exercise', 'artist': 'Practice room', 'content': '[Am] Take your time.\n', **changes}

    def test_anonymous_users_must_sign_in(self):
        self.client.logout()
        urls = [reverse('songs:list'), reverse('songs:create')]
        urls += [reverse(f'songs:{action}', args=[self.song.pk]) for action in ('detail', 'edit', 'delete')]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('accounts:login')))

    def test_admin_cannot_open_members_music_workspace(self):
        self.client.force_login(self.admin)
        urls = [reverse('songs:list'), reverse('songs:create')]
        urls += [reverse(f'songs:{action}', args=[self.song.pk]) for action in ('detail', 'edit', 'delete')]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(reverse('songs:create'), self.data()).status_code, 403)

    def test_creation_uses_signed_in_owner_even_when_another_owner_is_posted(self):
        response = self.client.post(reverse('songs:create'), self.data(owner=self.other.pk))
        song = Song.objects.get(title='Evening exercise')
        self.assertEqual(song.owner, self.member)
        self.assertRedirects(response, song.get_absolute_url())

    def test_creation_requires_title_and_nonblank_sheet(self):
        for data in ({}, self.data(title='   '), self.data(content=' \t\n  ')):
            with self.subTest(data=data):
                response = self.client.post(reverse('songs:create'), data)
                self.assertTrue(response.context['form'].errors)
        self.assertEqual(Song.objects.count(), 2)

    def test_original_sheet_spacing_is_preserved(self):
        sheet = '  [C]   [G]\n\te|---0---3---|\n\n'
        self.client.post(reverse('songs:create'), self.data(content=sheet))
        self.assertEqual(Song.objects.get(title='Evening exercise').content, sheet)

    def test_sheet_and_metadata_length_limits(self):
        response = self.client.post(reverse('songs:create'), self.data(title='t' * 201, artist='a' * 151, content='x' * 50001))
        for field in ('title', 'artist', 'content'):
            self.assertIn(field, response.context['form'].errors)

    def test_sheet_validation_error_is_linked_to_textarea(self):
        response = self.client.post(reverse('songs:create'), self.data(content='   '))
        textarea = response.content.decode().split('<textarea', 1)[1].split('>', 1)[0]
        self.assertIn('id_content_error', textarea)
        self.assertIn('id_content_helptext', textarea)
        self.assertContains(response, 'Add some chords, lyrics or tablature before saving.')

    def test_artist_is_optional_and_duplicate_titles_are_allowed(self):
        self.client.post(reverse('songs:create'), self.data(title=self.song.title, artist=''))
        self.assertEqual(Song.objects.filter(owner=self.member, title=self.song.title).count(), 2)

    def test_library_only_lists_own_songs(self):
        response = self.client.get(reverse('songs:list'))
        self.assertContains(response, self.song.title)
        self.assertNotContains(response, self.private.title)
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_search_matches_title_or_artist_within_own_library(self):
        for query in ('MORNING', 'original'):
            with self.subTest(query=query):
                response = self.client.get(reverse('songs:list'), {'q': query})
                self.assertContains(response, self.song.title)
        response = self.client.get(reverse('songs:list'), {'q': 'Private lesson'})
        self.assertContains(response, 'No matching songs.')
        self.assertNotContains(response, 'href="' + self.private.get_absolute_url() + '"')
        self.assertEqual(response.context['page_obj'].paginator.count, 0)

    def test_library_pagination_is_scoped_and_search_survives_page_links(self):
        Song.objects.bulk_create([
            Song(owner=self.member, title=f'Paged exercise {i:02}', content='[C] Practice')
            for i in range(24)
        ])
        response = self.client.get(reverse('songs:list'), {'q': 'Paged'})
        self.assertEqual(len(response.context['page_obj']), 20)
        self.assertContains(response, '?q=Paged&amp;page=2')
        second = self.client.get(reverse('songs:list'), {'q': 'Paged', 'page': 2})
        self.assertEqual(len(second.context['page_obj']), 4)
        self.assertEqual(second.context['page_obj'].paginator.count, 24)

    def test_other_members_song_returns_404_for_reads_and_writes(self):
        for action in ('detail', 'edit', 'delete'):
            url = reverse(f'songs:{action}', args=[self.private.pk])
            with self.subTest(action=action):
                self.assertEqual(self.client.get(url).status_code, 404)
                if action != 'detail':
                    self.assertEqual(self.client.post(url, self.data()).status_code, 404)
        self.private.refresh_from_db()
        self.assertEqual(self.private.title, 'Private lesson')

    def test_edit_updates_song_but_keeps_owner_and_creation_time(self):
        created = self.song.created_at
        response = self.client.post(reverse('songs:edit', args=[self.song.pk]), self.data(owner=self.other.pk))
        self.assertRedirects(response, self.song.get_absolute_url())
        self.song.refresh_from_db()
        self.assertEqual(self.song.title, 'Evening exercise')
        self.assertEqual(self.song.owner, self.member)
        self.assertEqual(self.song.created_at, created)

    def test_invalid_edit_preserves_saved_content(self):
        before = self.song.content
        response = self.client.post(reverse('songs:edit', args=[self.song.pk]), self.data(content=''))
        self.assertIn('content', response.context['form'].errors)
        self.song.refresh_from_db()
        self.assertEqual(self.song.content, before)

    def test_delete_requires_explicit_post_confirmation(self):
        url = reverse('songs:delete', args=[self.song.pk])
        self.assertContains(self.client.get(url), 'Keep song')
        self.assertTrue(Song.objects.filter(pk=self.song.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse('songs:list'))
        self.assertFalse(Song.objects.filter(pk=self.song.pk).exists())
        self.assertTrue(Song.objects.filter(pk=self.private.pk).exists())

    def test_csrf_is_required_for_song_writes(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        urls = [reverse('songs:create')]
        urls += [reverse(f'songs:{action}', args=[self.song.pk]) for action in ('edit', 'delete')]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, self.data()).status_code, 403)

    def test_song_sheet_and_metadata_are_escaped(self):
        self.song.title = '<script>alert(1)</script>'
        self.song.content = '<img src=x onerror=alert(1)>\n[C] Keep the text.'
        self.song.save()
        response = self.client.get(self.song.get_absolute_url())
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')

    def test_dashboard_counts_only_own_songs_and_caps_recent_list(self):
        Song.objects.bulk_create([
            Song(owner=self.member, title=f'Saved {i}', content='[G] Go slowly')
            for i in range(6)
        ])
        response = self.client.get(reverse('accounts:member_dashboard'))
        self.assertEqual(response.context['song_count'], 7)
        self.assertEqual(len(response.context['recent_songs']), 5)
        self.assertNotContains(response, self.private.title)

    def test_edit_moves_song_to_top_of_recent_library(self):
        newer = Song.objects.create(owner=self.member, title='Another exercise', content='[D] Rest')
        Song.objects.filter(pk=self.song.pk).update(updated_at=timezone.now() - timedelta(days=1))
        self.assertEqual(self.client.get(reverse('songs:list')).context['page_obj'][0].pk, newer.pk)
        self.client.post(reverse('songs:edit', args=[self.song.pk]), self.data())
        self.assertEqual(self.client.get(reverse('songs:list')).context['page_obj'][0].pk, self.song.pk)
