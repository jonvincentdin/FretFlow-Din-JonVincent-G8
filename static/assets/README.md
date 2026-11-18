# FretFlow brand assets

`logo.png` is the project owner's supplied guitar-pick logo. Its original bytes
were recovered from `7b2559e:static/assets/logo.png` after the history reset.
The shared Django template uses it in the header and favicon.

`../root.css` is the owner's supplied brand-token stylesheet, recovered from
the same commit and loaded globally before component styles.

Reuse these originals when adding screens. The requested `logo-name.png`
wordmark file still needs to be supplied; its referenced local path was absent.
