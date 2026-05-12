from django import forms


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantite",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1}),
    )


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        label="Nom complet",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control checkout-input",
                "placeholder": "Nom complet",
                "autocomplete": "name",
            }
        ),
    )
    customer_email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control checkout-input",
                "placeholder": "Gmail",
                "autocomplete": "email",
            }
        ),
    )
    customer_phone = forms.CharField(
        label="Telephone",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control checkout-input",
                "placeholder": "Telephone",
                "autocomplete": "tel",
            }
        ),
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control checkout-input",
                "placeholder": "Ville",
                "autocomplete": "address-level2",
            }
        ),
    )
    shipping_address = forms.CharField(
        label="Adresse de livraison",
        widget=forms.TextInput(
            attrs={
                "class": "form-control checkout-input",
                "placeholder": "Adresse",
                "autocomplete": "street-address",
            }
        ),
    )
