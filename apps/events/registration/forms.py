from django import forms
from django.utils.translation import ugettext_lazy as _

from discounts.models import Discount

from events.models import RegConfPricing, PaymentMethod
from events.registration.utils import get_available_pricings

class RegistrationForm(forms.Form):
    """
    Registration form.
    Focuses on non-registrant specific details.
    """
    amount_for_admin = forms.DecimalField(decimal_places=2)
    discount = forms.CharField(label=_('Discount Code'), required=False)
    captcha = CaptchaField(label=_('Type the code below'))
    payment_method = forms.ModelChoiceField(empty_label=None, required=True,
        queryset=PaymentMethod.objects.none(), widget=forms.RadioSelect, initial=1)
    
    def __init__(self, event, user, *args, **kwargs):
        """
        event: instance of Event model
        user: request.user
        reg_count: used for discount validation (discounts have usage limits)
        """
        self.event = event
        self.user = user
        self.reg_count = kwargs.pop('reg_count', 0)
        self.free_event = total_price <= 0
        
        super(RegistrationForm, self).__init__(*args, **kwargs)
        
        # no need for captcha if logged in
        if user.is_authenticated():
            self.fields.pop('captcha')
        
        # admin only price override field
        if not is_admin(user):
            self.fields.pop('amount_for_admin')
        
        # payment methods for non free events only
        if not self.free_event:
            reg_conf =  event.registration_configuration
            if reg_conf.can_pay_online:
                payment_methods = reg_conf.payment_method.all()
            else:
                payment_methods = reg_conf.payment_method.exclude(
                    machine_name='credit card').order_by('pk')
            self.fields['payment_method'].queryset = payment_methods
        else:
            self.fields.pop('payment_method')
   
    def clean_discount(self):
        """
        Returns the discount instance if it exists for a given code.
        Returns none if the code is blank.
        """
        code = self.cleaned_data['discount']:
        if code:
            try:
                discount = Discount.objects.get(discount_code=self.cleaned_data['discount'])
                if discount.available_for(self.reg_count):
                    return discount
                else:
                    raise forms.ValidationError(_("Discount Code cannot be used for %s people." % self.reg_count))
            except Discount.objects.DoesNotExist:
                raise forms.ValidationError(_("This is not a valid Discount Code!"))
        return code

class RegistrantForm(forms.Form):
    """
    Each registrant form will have a hidden pricing field.
    Each registrant form will have a hidden reg_set field.
    The reg_set field will be used to group the registrant data and validate
    them as a whole.
    """
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    company_name = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=20, required=False)
    
    def __init__(self, *args, **kwargs):
        self.pricings = kwargs.pop('pricings')
        self.form_index = kwargs.pop('form_index', None)
        
        super(RegistrantForm, self).__init__(*args, **kwargs)
        
        # make the fields in the subsequent forms as not required
        if self.form_index and self.form_index > 0:
            for key in self.fields.keys():
                self.fields[key].required = False
                
        #initialize pricing options and reg_set field
        self.fields['pricing'] = forms.ModelChoiceField(widget=forms.HiddentInput, queryset=pricings)
        self.fields['reg_set'] = forms.IntegerField(widget=forms.HiddenInput)
    
    def clean_first_name(self):
        data = self.cleaned_data['first_name']
        
        # detect markup
        markup_pattern = re.compile('<[^>]*?>', re.I and re.M)
        markup = markup_pattern.search(data)
        if markup:
            raise forms.ValidationError("Markup is not allowed in the name field")

        # detect URL and Email
        pattern_string = '\w\.(com|net|org|co|cc|ru|ca|ly|gov)$'
        pattern = re.compile(pattern_string, re.I and re.M)
        domain_extension = pattern.search(data)
        if domain_extension or "://" in data:
            raise forms.ValidationError("URL's and Emails are not allowed in the name field")
        
        data.strip()
        return data
        
    def clean_last_name(self):
        data = self.cleaned_data['first_name']
        
        # detect markup
        markup_pattern = re.compile('<[^>]*?>', re.I and re.M)
        markup = markup_pattern.search(data)
        if markup:
            raise forms.ValidationError("Markup is not allowed in the name field")

        # detect URL and Email
        pattern_string = '\w\.(com|net|org|co|cc|ru|ca|ly|gov)$'
        pattern = re.compile(pattern_string, re.I and re.M)
        domain_extension = pattern.search(data)
        if domain_extension or "://" in data:
            raise forms.ValidationError("URL's and Emails are not allowed in the name field")
        
        data.strip()
        return data
    
    def clean_email(self):
        data = self.cleaned_data['email']
        data.strip()
        return data

class PricingForm(forms.Form):
    """
    This form is the user's pricing selection.
    This form will be mainly used for ajax requests.
    This is the first form a user must answer before a registrant formset is loaded.
    """
    
    pricing = forms.ModelChoiceField(queryset=RegConfPricing.objects.none())
    
    def __init__(self, event, user, *args, **kwargs):
        super(PricingForm, self).__init__(*args, **kwargs)
        
        #initialize pricing options
        pricings = get_available_pricings(event, user)
        self.field['pricing'].queryset = pricings
