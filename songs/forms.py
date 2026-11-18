from django import forms

from .models import Song


class SongForm(forms.ModelForm):
    content = forms.CharField(
        label='Song sheet', max_length=50000, strip=False,
        widget=forms.Textarea(attrs={
            'rows': 18, 'spellcheck': 'false', 'wrap': 'off',
            'class': 'song-editor',
        }),
        help_text='Paste plain-text chords or ASCII tabs. Spacing is preserved. Up to 50,000 characters.',
    )

    class Meta:
        model = Song
        fields = ('title', 'artist', 'content')
        labels = {'artist': 'Artist (optional)'}

    def clean_content(self):
        content = self.cleaned_data['content']
        if not content.strip():
            raise forms.ValidationError('Add some chords, lyrics or tablature before saving.')
        return content
