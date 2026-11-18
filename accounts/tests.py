from django.contrib.auth import get_user_model
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from .admin import FretFlowUserAdmin

User = get_user_model()


class AccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'BrightStrings!7264'
        cls.member = User.objects.create_user('guitarist', 'member@example.com', cls.password)
        cls.other = User.objects.create_user('instructor', 'teacher@example.com', cls.password)
        cls.admin = User.objects.create_user(
            'siteowner', 'admin@example.com', cls.password, is_staff=True,
        )

    def registration_data(self, **changes):
        return {
            'username': 'newplayer', 'email': 'new@example.com', 'first_name': 'Alex',
            'password1': self.password, 'password2': self.password, **changes,
        }

    def test_registration_hashes_password_and_never_grants_admin(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data(
            is_staff='true', is_superuser='true',
        ))
        self.assertRedirects(response, reverse('accounts:dashboard'), fetch_redirect_response=False)
        user = User.objects.get(username='newplayer')
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_registration_rejects_missing_fields(self):
        response = self.client.post(reverse('accounts:register'), {})
        self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(User.objects.count(), 3)

    def test_registration_rejects_invalid_email_and_password_mismatch(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data(
            email='invalid', password2='different',
        ))
        self.assertIn('email', response.context['form'].errors)
        self.assertIn('password2', response.context['form'].errors)

    def test_registration_rejects_weak_password(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data(
            password1='password', password2='password',
        ))
        self.assertIn('password2', response.context['form'].errors)

    def test_registration_rejects_case_variant_username_and_email(self):
        response = self.client.post(reverse('accounts:register'), self.registration_data(
            username='GUITARIST', email='MEMBER@example.com',
        ))
        self.assertIn('username', response.context['form'].errors)
        self.assertIn('email', response.context['form'].errors)

    def test_database_enforces_case_insensitive_email(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user('another', 'MEMBER@example.com', self.password)

    def test_database_enforces_case_insensitive_username(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user('GUITARIST', 'another@example.com', self.password)

    def test_login_routes_member_and_admin(self):
        for user, dashboard in (
            (self.member, 'accounts:member_dashboard'),
            (self.admin, 'accounts:admin_dashboard'),
        ):
            with self.subTest(user=user.username):
                self.client.logout()
                response = self.client.post(reverse('accounts:login'), {
                    'username': user.username, 'password': self.password,
                }, follow=True)
                self.assertEqual(response.request['PATH_INFO'], reverse(dashboard))

    def test_login_rejects_invalid_or_inactive_credentials(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': self.member.username, 'password': 'wrong',
        })
        self.assertTrue(response.context['form'].non_field_errors())
        self.member.is_active = False
        self.member.save()
        self.assertFalse(self.client.login(username=self.member.username, password=self.password))

    def test_login_does_not_redirect_to_external_next_url(self):
        response = self.client.post(reverse('accounts:login') + '?next=https://example.com', {
            'username': self.member.username, 'password': self.password,
        })
        self.assertRedirects(response, reverse('accounts:dashboard'), fetch_redirect_response=False)

    def test_anonymous_users_are_redirected_to_login(self):
        for route in ('dashboard', 'member_dashboard', 'admin_dashboard', 'profile'):
            with self.subTest(route=route):
                response = self.client.get(reverse(f'accounts:{route}'))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('accounts:login')))

    def test_roles_cannot_open_each_others_dashboards(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('accounts:admin_dashboard')).status_code, 403)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('accounts:member_dashboard')).status_code, 403)

    def test_profile_only_updates_the_signed_in_member(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('accounts:profile'), {
            'first_name': 'Jamie', 'last_name': 'Player', 'email': 'jamie@example.com',
            'contact_number': '+63 900 123 4567', 'preferred_accidentals': 'flats',
            'default_bpm': 100, 'id': self.other.pk, 'is_staff': 'true',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        self.member.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Jamie')
        self.assertEqual(self.member.default_bpm, 100)
        self.assertFalse(self.member.is_staff)
        self.assertEqual(self.other.email, 'teacher@example.com')
        self.assertEqual(self.client.get(f'/accounts/profile/{self.other.pk}/').status_code, 404)

    def test_profile_rejects_duplicate_email_and_invalid_preferences(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('accounts:profile'), {
            'email': 'TEACHER@example.com', 'preferred_accidentals': 'invalid', 'default_bpm': 241,
        })
        for field in ('email', 'preferred_accidentals', 'default_bpm'):
            self.assertIn(field, response.context['form'].errors)

    def test_logout_is_post_only_and_ends_session(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_post_endpoints_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for route in ('register', 'login', 'logout'):
            with self.subTest(route=route):
                self.assertEqual(client.post(reverse(f'accounts:{route}'), {}).status_code, 403)

    def test_profile_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        self.assertEqual(client.post(reverse('accounts:profile'), {}).status_code, 403)

    def test_admin_user_creation_requires_email(self):
        request = RequestFactory().get('/admin/accounts/user/add/')
        request.user = self.admin
        form_class = FretFlowUserAdmin(User, admin.site).get_form(request)
        self.assertIn('email', form_class.base_fields)
        self.assertTrue(form_class.base_fields['email'].required)
