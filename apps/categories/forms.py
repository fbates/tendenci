from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from categories.models import CategoryItem

class CategoryField(forms.ChoiceField):
    """
    A ``ChoiceField`` which validates that its input is a valid category string
    """
    def clean(self, value):
        value = super(CategoryField, self).clean(value)
        return value

category_defaults = {
    'label':_('Category'), 
    'choices': [],
    'help_text': mark_safe('<a href="#" class="add-category">Add Category</a>'),
}

sub_category_defaults = {
    'label':_('Sub Category'), 
    'choices': [],
    'help_text': mark_safe('<a href="#" class="add-sub-category">Add Sub Category</a>'),                    
}

class CategoryForm(forms.Form):
    category = CategoryField(**category_defaults)
    sub_category = CategoryField(**sub_category_defaults)
    
    # instance fields needed to generate content types
    app_label = forms.CharField(widget=forms.HiddenInput())
    model = forms.CharField(widget=forms.HiddenInput())
    pk = forms.CharField(widget=forms.HiddenInput())
    
    def __init__(self, content_type, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        
        if args:
            post_data = args[0]
        else:
            post_data = None
        
        # set up the category choices
        categories = CategoryItem.objects.filter(content_type=content_type,
                                                 parent__exact=None)
        categories = list(set([cat.category.name for cat in categories]))
        categories = [[cat, cat] for cat in categories]
        categories.insert(0,[0,'------------'])
        if post_data:
            new_category = post_data.get('category','0')
            if new_category != '0':
                categories.append([new_category,new_category])
        self.fields['category'].choices = tuple(categories)

        # set up the sub category choices
        sub_categories = CategoryItem.objects.filter(content_type=content_type,
                                                     category__exact=None)
        sub_categories = list(set([cat.parent.name for cat in sub_categories]))
        sub_categories = [[cat, cat] for cat in sub_categories]
        sub_categories.insert(0,[0,'------------'])
        if post_data:
            new_sub_category = post_data.get('sub_category','0')
            if new_sub_category != '0':
                sub_categories.append([new_sub_category,new_sub_category])
        self.fields['sub_category'].choices = tuple(sub_categories)  
              
        
        
    