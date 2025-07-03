from django import forms
from .models import Product, Party, Invoice, InvoiceItem

CATEGORY_CHOICES = [
    ('Electronics', 'Electronics'),
    ('Furniture', 'Furniture'),
    ('Clothing', 'Clothing'),
    ('Food and Beverages', 'Food and Beverages'),
    ('Automation', 'Automation'),
    ('Books & Stationery', 'Books & Stationery'),
    ('Health & Beauty', 'Health & Beauty'),
    ('Sports & Outdoors', 'Sports & Outdoors'),
    ('Others', 'Others'),
]

class ProductForm(forms.ModelForm):
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)

    class Meta:
        model = Product
        exclude = ('user', 'product_code', 'hsn_code', 'created_at', 'updated_at')


class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        exclude = ['user', 'created_at', 'updated_at']
        
class InvoiceForm(forms.ModelForm):
    party = forms.ModelChoiceField(
        queryset=Party.objects.none(),
        empty_label="Select Party",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'party-select'
        })
    )
    
    class Meta:
        model = Invoice
        fields = ['invoice_no', 'invoice_date', 'due_date', 'status']
        widgets = {
            'invoice_no': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['party'].queryset = Party.objects.filter(user=user, status=True)
            
class ReturnInvoiceForm(forms.Form):
    invoice_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Invoice Number',
            'required': True
        }),
        label='Invoice Number'
    )