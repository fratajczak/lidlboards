from django import forms


class PlayerSearchForm(forms.Form):
    player_name = forms.CharField(label="", min_length=5, max_length=16)
    player_name.widget.attrs = {
        "class": "form-control mr-sm-2",
        "placeholder": "Player search",
        "aria-label": "Player search",
    }
