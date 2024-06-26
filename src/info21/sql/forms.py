from django import forms


class DynamicForm(forms.Form):
    """Класс для создания динамических форм."""

    def __init__(self, param_string, *args, **kwargs):
        super().__init__(*args, **kwargs)
        params = [p.strip().split(" ") for p in param_string.split(",")]
        for param in params:
            name, data_type = param[0], param[1]
            if param[0] == "IN" or param[0] == "OUT":
                name, data_type = param[1], param[2]
            if data_type == "character" and "date" not in name:
                self.fields[name] = forms.CharField(
                    widget=forms.TextInput(
                        attrs={"class": "form-control", "placeholder": data_type}
                    )
                )
            elif data_type == "integer":
                self.fields[name] = forms.IntegerField(
                    min_value=0,
                    widget=forms.NumberInput(
                        attrs={"class": "form-control", "placeholder": data_type}
                    ),
                )
            elif data_type == "status":
                self.fields[name] = forms.ChoiceField(
                    choices=[
                        ("Start", "Start"),
                        ("Success", "Success"),
                        ("Failure", "Failure"),
                    ],
                    widget=forms.Select(attrs={"class": "form-control"}),
                )
            elif data_type == "time":
                self.fields[name] = forms.CharField(
                    widget=forms.TextInput(
                        attrs={
                            "class": "form-control",
                            "placeholder": "Format: hh:mm:ss",
                        }
                    )
                )
            elif "date" in name:
                self.fields[name] = forms.CharField(
                    widget=forms.TextInput(
                        attrs={
                            "class": "form-control",
                            "placeholder": "Format: DD.MM.YYYY",
                        }
                    )
                )
            elif "refcursor" not in data_type:
                self.fields[name] = forms.CharField(
                    widget=forms.TextInput(
                        attrs={"class": "form-control", "placeholder": data_type}
                    )
                )
